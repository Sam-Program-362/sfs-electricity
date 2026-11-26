# Free, phone-testable ion patch (experimental)

## Status and scope

The user reports that the original `Electricity_v1.0.1.pack` uploaded to `main`
loads on their Android phone without a Full Bundle purchase. That observation
is the prerequisite for this test; this tool does not change SFS, its loader,
or purchase checks. The older README's blanket purchase instruction should not
be treated as a diagnosis of this user's installation.

A real binary patch has now been generated using **UnityPy 1.22.5**, without
Unity, Odin, a self-hosted runner, an activation service, or a paid API. This is
**not** an export of the repository's prefab changes.

Included:
- Ion thrust **7.25**, ISP **1800**.
- Power mixture coefficient `8.275862` (stored as float32
  `8.275861740112305`) to preserve the old nominal Power consumption.
- Liquid Fuel requirement and coefficient unchanged. At equal operating
  conditions, nominal Liquid Fuel consumption increases by about **4.83x**.
- All four original platform bundles, with no custom code assembly.

**Not included:** the separate electric RCS. Stock RCS is not modified.
**In-game verification:** pending a phone test. File validation is not runtime proof.

## Why this works without Unity

The existing pack is JSON with Base64-encoded Unity bundles, not source files
or a ZIP. Its compiled bundles contain the type trees needed to edit the ion's
serialized fields directly. All four source bundle headers identify Unity
`6000.2.10f1`; this is different from the toolkit's documented `6000.1.17f1`.
Direct editing avoids importing/rebuilding the source in a different editor.

The input is pinned by SHA-256:

```
cf164ff3f2ddab38222ec65bbecddccf490136e81d888136c4d2a53dced1883b
```

Do not use this script on arbitrary, newer, previously patched, or untrusted packs.
The exact input hash is checked before UnityPy loads it.

## Reproduce on a suitable free Python environment

These commands were tested in the Arena Linux workspace. They do not require
GitHub Actions. Termux dependency installation has **not** been tested; native
Python dependencies may need additional setup on Android. A standard public-repo
GitHub-hosted runner is another possible place to execute the same commands;
no new workflow has been enabled by this change.

```sh
python3 -m pip install -r scripts/requirements-pack-patch.txt
python3 scripts/patch_ion_pack.py Electricity_v1.0.1.pack artifacts/pack/Electricity_ion_7.25_1800_EXPERIMENTAL.pack
python3 scripts/ci/validate_pack.py artifacts/pack/Electricity_ion_7.25_1800_EXPERIMENTAL.pack
```

Use the path to your original downloaded pack if it is not at the repository
root. The upload is on `main`; it need not be committed again to this branch.
The patcher refuses to overwrite the original or existing output/sidecar files.
It also creates `.report.json` and `.pack.sha256` sidecars. Generated files stay
in ignored `artifacts/`, not in Git.

Ordinary tests (UnityPy not required):

```sh
python3 -m unittest discover -s tests -v
```

Real binary integration test (requires optional dependencies and original file):

```sh
SFS_PATCH_SOURCE=/path/to/Electricity_v1.0.1.pack python3 -m unittest discover -s tests -p test_pack_patch.py -v
```

For each of the four real bundles the patcher saves/reopens and verifies:
- The same 590 serialized objects and identical asset container references.
- Exactly two changed objects: the ion EngineModule and its FlowModule.
- Exact intended type-tree contents after float32 rounding.
- Byte-for-byte identical raw data for every other serialized object.
- Preserved nominal Power rate to relative tolerance `1e-6`.
- A structurally valid final JSON/Base64/UnityFS container and null CodeAssembly.

Compression and bundle layout may differ from the original. These checks do
not prove the game will accept the rewritten bundle.

## Safe Android test

1. Back up your saves/blueprints and the original working pack.
2. Fully close SFS.
3. Move the original pack **out of** the game's active parts-pack folder. Do not
   keep two active copies: the patched pack deliberately retains the same identity.
4. Place only `Electricity_ion_7.25_1800_EXPERIMENTAL.pack` in the same folder
   where the original worked. No ZIP extraction or renaming is needed.
5. Restart SFS. Use a new disposable test craft/world rather than important saves.
6. Check the ion's displayed thrust and ISP, then test with Power **and** Liquid
   Fuel available. Keep throttle, difficulty, and engine scale equal when comparing
   Power drain against the original. Very short tests may hide drain due to UI rounding.
7. If loading fails, fully close SFS, remove the experimental file and restore the
   original. Report the exact error or a screenshot. Do not clear app data.

Expected: ion thrust 7.25 / ISP 1800, approximately unchanged Power drain at the
same conditions, faster Liquid Fuel use. There will be **no electric RCS part**
in this test file. Pack display version remains v1.0.1 because metadata was not edited.

## Remaining RCS investigation

The supplied pack contains 41 MonoScript objects, but no `RcsModule` and no RCS
prefab. Its existing metadata cannot simply be reused as if EngineModule were
RcsModule. Copying the repository's YAML prefab into the JSON is not a valid build.

Possible next routes, neither demonstrated yet:
1. A compatible, legitimately available compiled donor bundle containing a stock
   RCS prefab and its type metadata, followed by careful object/dependency import,
   reference remapping, new part registration, and device testing.
2. A free Unity Personal build on a standard GitHub-hosted runner, after testing
   legitimate activation and adapting the toolkit's Odin-based editor dependencies.

The absence of RCS here is not proof the free routes are impossible. It means
this ion patch is a narrow, testable first deliverable, not completion of the
full ion + separate mixed-resource RCS request. No purchase bypass, paid trial,
cloud resource purchase, or subscription activation was used.
