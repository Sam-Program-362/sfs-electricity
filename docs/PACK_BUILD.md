# Building the `.pack` GitHub artifact

The **Build SFS pack** workflow runs source checks on pushes/PRs and can build a
real installable-format pack on **manual dispatch**. It does not publish a GitHub
Release, push commits, or run Unity on pull requests.

> One-time setup is required. This is an asset-only repository: GitHub-hosted
> runners do not come with the compatible Unity editor, an activated Unity
> license, or licensed Odin Inspector. The Unity build therefore uses a trusted
> self-hosted Windows runner. No Unity build has been executed in the development
> sandbox; the Python tests use temporary synthetic fixtures, not shipped packs.

## What is produced

A successful manual run uploads **`Electricity-pack-<full source commit SHA>`**:

```text
Electricity_<first 12 commit characters>.pack
Electricity_<first 12 commit characters>.pack.sha256
build-info.json
```

The pack contains `WindowsBuild`, `MacBuild`, `AndroidBuild`, and `IOS_Build`
Base64-encoded Unity AssetBundles, plus `CodeAssembly: null`, matching the official
exporter's format. This is not a ZIP renamed to `.pack`.

GitHub wraps downloaded artifacts in a ZIP. **Extract it, then install the
`.pack` inside** into SFS's `Mods/Custom_Assets/Parts` folder. Do not install the
artifact ZIP, checksum, provenance JSON, `.meta`, or Unity build logs.

Pack artifacts are retained for **14 days**. Diagnostic logs are a separate
`Electricity-build-logs-<SHA>` artifact retained for **7 days**. Download needed
builds before expiration. No licensed toolkit/Odin source, Unity project cache,
activation files, or custom DLL is included in either artifact.

## 1. Provision the licensed runner

Use a dedicated, trusted Windows machine/account with sufficient disk space for
four platform imports/builds. Do not use a public shared or untrusted machine.

1. Install Git, a GitHub Actions self-hosted runner, and **Unity 6000.1.17f1**.
   Register the runner to this repository with the custom label **`sfs-unity`**
   (the standard `self-hosted` and `Windows` labels are also required).
2. Activate Unity using your legitimate license under the **same account that
   runs the runner service**. Verify that account can launch the editor in batch
   mode. License eligibility/activation depends on your Unity plan and current
   terms; this workflow does not acquire, bypass, or store a license for you.
3. Install Unity build support for Windows x64, macOS, Android, and iOS. The
   pipeline builds AssetBundles, **not an APK, IPA, or signed game executable**;
   nevertheless every target needs its matching editor build-support module.
4. Outside the Actions work directory, clone the official toolkit and pin it:

   ```powershell
   git clone https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit.git C:\SFS\Toolkit
   git -C C:\SFS\Toolkit checkout --detach 855f3eeb094f79c9aa9d27a3d689f51f350b4e06
   ```

5. Open its **inner** `C:\SFS\Toolkit\Modding Toolkit` project with the pinned
   editor. Install Odin Inspector under your own valid license into this
   template's `Assets` directory. Typical assemblies include
   `Sirenix.OdinInspector.Attributes.dll` and `Sirenix.OdinInspector.Editor.dll`.
   Licensed packages must remain private/untracked; do not commit or upload them.
6. Verify the template compiles without errors, then close the editor. Keep it a
   **clean stock template**, without importing this Electricity pack or other
   custom packs/build scripts. Tracked files must match the pinned revision;
   review/restore any Unity-generated tracked changes in this dedicated template.
   Untracked/ignored Odin installation files are allowed and copied privately.
7. Configure these machine environment variables for the runner service account:

   | Variable | Example |
   |---|---|
   | `SFS_UNITY_EDITOR` | `C:\Program Files\Unity\Hub\Editor\6000.1.17f1\Editor\Unity.exe` |
   | `SFS_TOOLKIT_PROJECT` | `C:\SFS\Toolkit\Modding Toolkit` |

   Set their values to raw absolute paths, **without surrounding quote characters**.
   These are file paths, not secrets or license keys. Restart the runner service
   after setting them. The template must not be inside the repository's generated
   `.build` directory; builds use a disposable copy and never modify the template.

Odin may have its own activation requirements. Ensure it is usable by this
account in batch mode. Do not paste license keys/tokens into chat, YAML, commits,
or build command lines. The workflow requires no GitHub PAT and only requests
`contents: read` for its normal Actions token.

## 2. Protect and enable builds

Before enabling the Unity job:

1. In repository **Settings → Environments**, create **`sfs-pack-build`**.
2. Configure required reviewers (where supported by your GitHub plan) and/or
   trusted branch restrictions for that environment. Approve **only reviewed,
   trusted source revisions**, including any workflow, editor script, or Python
   build-tool changes. An environment name alone is not an approval policy.
3. Restrict runner access to this repository/trusted users. A self-hosted runner
   executes repository code with machine access: do not run untrusted forks/PRs
   on it. Source checks use GitHub-hosted Ubuntu; the Unity job is gated to
   `workflow_dispatch` only. Manual dispatch on an untrusted branch is still
   dangerous and must not be approved.
4. In **Settings → Secrets and variables → Actions → Variables**, add repository
   variable **`SFS_UNITY_BUILDS_ENABLED` = `true`**.

Keep this variable unset or false until setup is complete. A manual run without
it fails with a setup explanation on a hosted runner, instead of silently
queuing a Unity job forever. If it is enabled but no matching runner is online,
the Unity job will queue until a runner becomes available; job execution timeout
does not limit the time spent waiting for an offline runner.

## 3. Run and download

1. Push/merge the workflow and the intended part modifications to GitHub through
   the normal review process. GitHub normally needs a `workflow_dispatch`
   workflow present on the repository's **default branch** before displaying its
   Run workflow button. The file exists locally until your changes are pushed;
   creating it here does not register or run it remotely.
2. Open **Actions → Build SFS pack → Run workflow**. Select the reviewed branch
   containing the desired changes. The checked-out commit determines pack content
   and artifact name; the workflow does not silently download the upstream pack.
3. Wait for source tests, any environment approval, and the Unity job. Four
   platform builds run sequentially, in separate Unity processes.
4. Open the successful run's **Artifacts** section and download
   **Electricity-pack-<SHA>**. Extract and install its `.pack` only.
5. Optionally verify the `.pack.sha256` checksum and inspect `build-info.json`.
   It records the source commit, source-asset digest, toolkit revision, editor
   version, PackData version, and each payload's size/checksum.

The pack's `PackData.Version` remains whatever is in source (currently `v1.0.1`).
A commit-specific filename/build-info distinguishes development artifacts; it
does not automatically change the in-game version. Set an appropriate new
PackData version as part of an actual release. Remove old Electricity packs
before testing to avoid duplicate identities.

## 4. How the automation works

Files:

| File | Responsibility |
|---|---|
| `.github/workflows/build-pack.yml` | Hosted checks, protected manual Unity build, artifact/log uploads. |
| `scripts/ci/build_pack.py` | Preflight, project preparation, Unity invocations, packaging, provenance. |
| `build-tools/Editor/SfsPackBuild.cs` | Public noninteractive Unity `-executeMethod` entrypoint. |
| `scripts/ci/validate_pack.py` | Four-platform JSON/Base64/UnityFS structural validation. |
| `tests/test_pack_build.py` | Offline tests of build tooling using temporary fixtures/mocks. |

Detailed sequence:

1. Check runner paths, toolkit Git revision/clean tracked state, editor version in
   the template, and installed Odin assemblies. The C# entrypoint also checks
   the actual running editor version and build-target support.
2. Make a fresh project in `.build/pack-ci`, copying only template `Assets`,
   `Packages`, and `ProjectSettings`, not `.git`, Library, UserSettings, or local
   activation files. This does copy licensed Odin **privately into the workspace**,
   never into the artifact. Only disposable directories bearing the build tool's
   marker can be replaced on reruns.
3. Import this checkout's `Electricity/` and `Electricity.meta` under
   `Assets/Resources/`, preserving all asset GUIDs, and copy the C# entrypoint
   under `Assets/Editor/`.
4. Launch Unity separately for Windows, macOS, Android, and iOS with explicit
   `-buildTarget`, `-batchmode`, `-nographics`, and `-executeMethod` arguments.
   Separate launches avoid switching target and recompiling halfway through an
   executing editor script. Each launch has a 35-minute process timeout; the
   Actions build job has a 150-minute timeout after starting on a runner.
5. The C# method checks required labeled assets, PackData, and missing scripts,
   then uses **real `BuildPipeline.BuildAssetBundles`** with an explicit map for
   `n2o4s_electricity`, strict error handling, and forced rebuild. Dependencies
   are included by Unity. Unexpected sibling-bundle dependencies fail the build.
   There is no optional DLL picker or other interactive UI.
6. Require successful process exit, a per-platform completion marker, and a valid
   bundle file for **every** platform. Null/missing/stale platform payloads are
   not accepted. Old generated output is discarded before rebuilding.
7. Base64-wrap the four bundles in the official JSON schema, with
   `CodeAssembly: null`. Validate the schema, Base64, UnityFS signatures, header
   sizes and file lengths. Write an SHA-256 file and build provenance JSON.
8. Upload the output only after all build/validation steps succeed. Unity logs
   upload on failure too, when available. The generated Unity project, raw cache
   bundles, `.meta` files, and licensed dependencies are not uploaded.

The Actions artifact upload uses a commit-pinned official action, as do checkout
and Python setup. No third-party Unity activation action or cloud credential is
required. Generated files are excluded by `.gitignore`.

## 5. Run locally on the configured machine

With the same editor/template/environment setup:

```powershell
python -m unittest discover -s tests -v
python scripts/ci/build_pack.py
python scripts/ci/validate_pack.py artifacts/pack/Electricity_<commit-prefix>.pack
```

Use the actual generated filename for the last command. Outputs are in
`artifacts/pack/`; Unity logs are in `artifacts/logs/`. The build script uses the
same pipeline locally and in Actions. A dirty local source checkout is allowed
but is explicitly marked in `build-info.json`; commit/source-digest provenance
must be interpreted accordingly. Close Unity before starting and do not run two
local builds from the same checkout at once.

## 6. Troubleshooting and limits

- **Disabled-build setup error:** configure the runner/environment and set the
  repository variable exactly to `true`.
- **Queued Unity job:** check runner labels, Windows platform, availability,
  repository access, and pending environment approval.
- **License/compile error:** check all Unity logs under the runner service
  account. Installing a license/Odin for a different desktop user is insufficient.
- **Missing platform support:** add the matching module for this exact Unity
  editor installation, not another editor version.
- **Template Git preflight failure:** use the pinned clean clone, not a ZIP
  download or your modified personal authoring project. Do not delete Odin while
  restoring tracked toolkit files.
- **Unmanaged-directory refusal:** the script deliberately refuses to delete an
  existing `.build/pack-ci` or output directory it did not create. Inspect and
  move aside that specific generated path if needed; never delete the repository
  or template root. Do not add the marker to arbitrary valuable directories.
- **Timeout/crashed editor:** inspect logs and stop any leftover Unity process
  before retrying. Do not open the disposable project interactively during CI.
- **Artifact download has only a ZIP:** extract it; the installable-format `.pack`
  is inside. Workflow logs are a different artifact.
- **Real-device behavior:** successful export/structural validation does not test
  game compatibility, Power metering, RCS inputs, depletion, or old-craft loading.
  Perform the regression checks in `SFS_MODDING_RESEARCH.md` on the target device.
- **Licensing/redistribution:** this pipeline does not grant rights to upstream,
  game, or Odin assets. Resolve the licensing concerns already recorded in the
  research before publishing/distributing derivative packs. Never publish the
  private template or proprietary source/dependency files.

The system creates a downloadable GitHub Actions artifact when a configured
runner successfully executes it. It does **not** claim a pack already exists,
that this C# entrypoint has been compiled here, or that a device test has passed.
