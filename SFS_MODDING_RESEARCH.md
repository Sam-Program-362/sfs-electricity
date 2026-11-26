# SFS Electricity — custom-part modding research and working context

> Research date: **2026-11-26** (UTC). Repository baseline: `c085d8605a1b7f0903ff9de8ab4b0f16aba3b530`.
> Purpose: retain the architecture, mobile constraints, asset map, export method, and verification checklist before making requested modifications.
> **Current branch status:** ion engine retuned to thrust **7.25** / ISP **1800**, with original nominal Power draw preserved; separate **Power + Liquid Fuel Electric RCS Thruster** added (section 16). A manual GitHub Actions artifact pipeline and noninteractive Unity entrypoint are now implemented (section 17). No new `.pack` has been built with Unity or runtime-tested. Sections 1–13 describe the original research/baseline, and section 15 records the superseded first modification pass.

## 1. Quick orientation

- This is the **Electricity pack by VerdiX**, a recreation of the SFS 1.3–1.4 electricity system with additional parts.
- This checkout is an **asset-only Unity source repository**, not a complete Unity project. It has no `ProjectSettings/`, `Packages/`, editor exporter, C# modules, CI build pipeline, or compiled `.pack`.
- The source must be imported into the compatible **official SFS Modding Toolkit** Unity project, preserving `.meta` files.
- The official toolkit inspected here specifies **Unity 6000.1.17f1**. Pin the toolkit and editor versions; do not assume any newer Unity release is compatible.
- Existing assets use AssetBundle label **`n2o4s_electricity`**, with an empty bundle variant.
- The inspected exporter builds Windows, macOS, Android, and iOS bundles and wraps them in **one JSON `.pack` file**. It is **not a ZIP**, a `.unitypackage`, or a loose prefab renamed to `.pack`.
- For mobile, use behaviors already implemented by the game. The exporter can embed an optional DLL, but that does **not** make arbitrary C# modules mobile-compatible.
- The repository README says mobile users need the **full bundle purchase** to install mods. Its installation paths are recorded in section 10.

### Evidence labels

- **Repository verified:** directly inspected source in this checkout.
- **Toolkit verified:** directly inspected official toolkit source at the pinned revision below. This establishes authoring/export behavior, not the private game loader implementation.
- **Upstream documented:** original author's README/release notes.
- **Community guidance:** useful secondary documentation, sometimes outdated or incomplete.
- **Needs runtime verification:** cannot be established from source assets/editor stubs alone.

## 2. README and metadata findings

### `README.md`

The README identifies the pack, lists batteries, RTGs, solar panels, wheels, and an ion engine, and links to the original author's releases:

- [Original upstream repository](https://github.com/VerdiX094/sfs-electricity)
- [Latest upstream release](https://github.com/VerdiX094/sfs-electricity/releases/latest)

It provides Android, iOS, and Steam installation instructions, says mobile needs the full bundle, and warns that duplicate old packs or files remaining in a device's trash can interfere with loading. It also suggests Steam integrity verification or reinstalling as troubleshooting. Prefer checking the path, purchase, version, duplicate files, and logs first; back up saves before considering reinstalling.

### `README.md.meta` — spelling clarification

The requested `README.me.meta` does not exist. The actual file is **`README.md.meta`**:

```yaml
fileFormatVersion: 2
guid: ad9d9c364c520704fbb7d623c26fc94b
TextScriptImporter:
  externalObjects: {}
  userData:
  assetBundleName:
  assetBundleVariant:
```

This is Unity's import metadata for the Markdown file, **not another README and not pack build instructions**. Its AssetBundle fields are empty, so it is not explicitly assigned to this pack's bundle. Preserve it when moving the README inside Unity.

### Why `.meta` files matter throughout this repository

- An asset's `.meta` supplies its persistent Unity GUID and import settings; folder `.meta` files identify folders.
- Prefabs and ScriptableObjects reference other assets by `{fileID, guid, type}`. `guid` identifies the external asset, while `fileID` identifies an object within it. References with only a `fileID` normally point within the serialized file; zero usually means no reference.
- `m_Script` GUIDs link serialized components to scripts supplied by the toolkit; those scripts are not in this checkout.
- Preserve GUIDs when editing/moving existing assets. Deleting metadata can create new identities and break references.
- For a **new** asset, duplicate/create it through Unity so it receives its own metadata. Do not copy an existing GUID into a new independent asset.
- The `.meta` file is not installed on the phone. In particular, `Something.pack.meta` is **not** `Something.pack`.

## 3. Repository inventory and asset map

Repository-verified counts under `Electricity/`: **13 prefabs, 16 `.asset` files, 14 PNG textures, and 51 `.meta` files** (the metadata count includes subfolders). There is also root-level `Electricity.meta` and `README.md.meta`.

```text
Electricity/
├── Parts/
│   ├── Batteries/
│   │   ├── Battery_1x2.prefab
│   │   ├── Battery_1x4.prefab
│   │   ├── Battery_1x6.prefab
│   │   └── Battery_New.prefab
│   ├── RTGs/
│   │   ├── Smol RTG.prefab
│   │   ├── RTG.prefab
│   │   └── RTG 2.prefab
│   ├── Solar Panels/
│   │   ├── Solar Panel Working.prefab
│   │   ├── Solar Panel Working Big.prefab
│   │   └── Solar Panel Working Dual.prefab
│   ├── Wheels/
│   │   ├── Electric Wheel Medium.prefab
│   │   └── Electric Wheel Big.prefab
│   └── Ion Drive.prefab
├── Scriptables/
│   ├── PackData.asset
│   ├── Electricity_Resource.asset
│   ├── Elec_Pick.asset
│   └── [texture/color/shape/shadow definitions]
└── Textures/
    ├── [battery, RTG, icon and other PNGs]
    └── Legacy/ [three old battery textures]
```

All 13 prefab metadata files and all 16 ScriptableObject metadata files explicitly use `n2o4s_electricity`. Eleven PNG metadata files also explicitly use it. Other textures can still be included as dependencies: **an empty label does not prove exclusion**. For example, `new-pack-icon.png` has an empty label but is referenced by `PackData.asset`.

### Pack metadata

`Electricity/Scriptables/PackData.asset` contains:

| Field | Current value |
|---|---|
| Display name | `Electricity Part Pack` |
| Version | `v1.0.1` |
| Description | `A simple part pack reimplementing electricity.` |
| Author | `VerdiX` |
| Show icon | true |
| Icon | `Textures/new-pack-icon.png` via GUID `078fb72745bfeaa419db9a8cabe730c4` |

Keep the distinction between **display name**, **output filename**, **AssetBundle label**, and **prefab/asset identity**. They are different things; renaming one does not automatically rename the others. Preserve original attribution when producing a derivative.

### Core shared assets

| File | Purpose / inspected values |
|---|---|
| `Electricity_Resource.asset` | Resource type: display `Power`, unit text **`KWh`** as written, `resourceMass: 0`, `transferRate: 1`. GUID `04b436aa485ffa14cab70bc05a1ef5bf`. |
| `Elec_Pick.asset` | Custom part picker category: `Electricity`. GUID `3c5e45a9d5d95524bb991a0d1dd6384b`. |
| `Battery_1x2/1x4/1x6.asset` | Texture-related ScriptableObjects, not the battery gameplay prefabs. |
| `BatIcon Shape.asset`, `BattIcon Shadow.asset` | Battery icon shape/shadow definitions. |
| `Color_RTG.asset`, `RTG.asset`, `RTG 2.asset`, `Smol RTG.asset`, `RTG_Shape.asset` | RTG visual definitions. |
| `Solar Panel.asset`, `Old Array.asset`, `Panel Boom.asset` | Solar-panel/boom visual definitions. |

Do not confuse `.asset` and `.prefab` files with similar names. Inspect `m_Script` before deciding which file controls gameplay.

## 4. Custom-part architecture

### 4.1 Authoring layer versus runtime layer

```text
Unity toolkit project + Odin Inspector
    └── prefabs + ScriptableObjects + textures + stable metadata
          └── Unity BuildPipeline: platform-specific AssetBundles
                └── toolkit Builder.cs: JSON .pack container
                      └── SFS Mod Loader on target device
                            └── game-provided module implementations
```

The toolkit contains serializable class definitions and editor tools. Some runtime methods are deliberately empty/commented in its public source. For example, `ResourceModule.ToggleTransfer()` and `WheelModule.ToggleEnabled()` are empty in the inspected toolkit, and the runtime body in `DisableOnNoFlow.Update()` is commented out. That does **not** establish that these features are absent in the actual game: their runtime behavior belongs to the game implementation.

Consequently, editor import success, mesh preview success, and valid `.pack` JSON are separate checks from **in-game functionality**.

### 4.2 Typical prefab composition

A part is a Unity GameObject hierarchy with a root `Part` component and multiple cooperating modules:

| Component / concept | Role |
|---|---|
| `Part` | Display text, mass expression, center of mass, orientation/variables references, variants, and `onPartUsed` UnityEvent. |
| `VariablesModule` | Named double/bool/string state, including whether a value is saved. |
| `OrientationModule` | Orientation state used by the part system. |
| `CustomPipe`, `SimplePipe`, `CustomPolygon`, `BoxPolygon` | Shape definitions, attachment/drag/collider/click-area settings, and depth information. |
| `PipeMesh`, `PolygonMesh` | Rendering geometry from shape data and texture definitions. |
| `PolygonCollider`, `ColliderModule` | Collision-related data. Rendering a shape does not by itself guarantee proper physical collision. |
| `MagnetModule`, `CustomSurfaces`, `AdaptTriggerModule` | Snap/attachment/surface behavior. |
| `ResourceModule` | Storage definition and resource state references. |
| `FlowModule` | Resource generation/consumption connections. |
| `EngineModule`, `WheelModule` | Propulsion and wheel configuration. |
| `MoveModule`, `ToggleModule` | Animation and toggled state. |
| `ExternalVariableModule` | Exposes game state, such as rails timewarp or wheel input, into part variables. |
| `MathModule`, `VariableConverterModule` | Connect expressions and type conversions to variables. |
| `DisableOnNoFlow` | Links resource availability to enabled state. |

The existing root part objects use **layer 8 (`Parts`)**. Preserve the toolkit's layer setup and existing prefab organization. Geometry, mesh, click area, drag surface, attachment surface, and collider are related but distinct settings.

### 4.3 Variables, expressions, and events

- A composed value stores an expression in `input` plus its `variables` reference, e.g. `0.5*width`.
- A `Double_Reference`/`Bool_Reference` can address a named variable (`variableName`, `referenceToVariables`) or use `localValue`. Do not assume the local fallback is the active value when a variable name is set.
- `VariablesModule` values appear as hex-encoded serialized data in YAML, not ordinary numeric fields. Avoid broad search-and-replace or arbitrary deserialization. Prefer editing them through the proper Unity inspector.
- Preserve `save` flags: persistent deployment/charge state and derived flow state have different requirements.
- The inspected `MathModule` explicitly warns against **numbers and special characters other than `_` in expression variable names**. Use simple names such as `power_rate`; recheck parser behavior if changing toolkit revisions.
- Events are serialized persistent calls: target `fileID`, method name, argument mode, and arguments all matter. A visible toggle without the correct event target may do nothing in game.
- `plainText: 1` means literal display text; `plainText: 0` uses a translation key such as `Battery_Name`. Do not turn a key into a literal accidentally.

### 4.4 Flow enum values, verified from toolkit source

```text
SourceMode: Global = 0, Surfaces = 1, Local = 2
FlowType:   Negative = 0, Positive = 1
```

Existing generators use positive/global flows. Wheels and the ion drive use negative/global flows. A surface-mode flow requires its surface reference. Keep flow direction separate from numerical rate; do not invert both casually.

**Units caution:** the custom resource's `KWh` label does not by itself establish the runtime conversion from `flowRate`, resource capacity, engine thrust, or elapsed time to real-world units. The public toolkit has data definitions/stubs, not the entire game simulation. Record expressions as serialized settings, not measured watts or kWh/s.

## 5. Electricity implementation and modification hotspots

### 5.1 Batteries

- Three older standalone prefabs (`Battery_1x2`, `Battery_1x4`, `Battery_1x6`) remain present and bundle-labeled. Their root `Part.variants` lists are empty. Do not delete them just because the new prefab exists; they may matter to old craft compatibility. Actual old-blueprint loading remains untested.
- `Battery_New.prefab` uses width variants **1, 2, 3**, implementing the README's 2-/4-/6-wide choices through its geometry system.
- Mass expression: **`0.5*width`**.
- Its resource storage references `Electricity_Resource`, with `wetMass -> width`, `resourcePercent -> powerPercent`, `dryMassPercent.localValue: -9`, and `setMass: 0`.
- The stored initial `width` and `powerPercent` doubles are both `1`. These were read as known-format primitive values, not executed as serialized objects.
- The unusual negative dry-mass setting is existing behavior, not automatically an error. **Do not normalize it to a 0–1 range without understanding the game's capacity calculation.** Capacity must be checked in the game before quoting exact figures.
- The older battery prefabs wire `onPartUsed` to `ToggleTransfer`; the new prefab's event call list is empty. Do not assume identical interaction behavior.

**Likely changes:** width options, appearance, mass, initial charge, storage balance. Change geometry, variants, storage, mass, snapping/collision, and saved-variable behavior coherently.

### 5.2 RTGs

All three RTGs use positive global Power flow, `ExternalVariableModule` mapping rails timewarp to `rails`, and `MathModule` writing `state`:

| Prefab | `Part.mass.input` | Active generation expression |
|---|---:|---|
| `Smol RTG.prefab` | `0.4` | `state = rails*0.01` |
| `RTG.prefab` | `0.8` | `state = rails*0.02` |
| `RTG 2.prefab` | `2` | `state = rails*0.05` |

`FlowModule.flowRate.variableName` is `state`. Its fallback local values (`0.75`, `1.5`, `3`) are not reliable active-rate balance knobs while the variable reference is set.

**Likely changes:** the MathModule coefficient, mass, and visuals. Verify generation both at ordinary speed and rails timewarp; do not multiply by timewarp again without checking existing behavior.

### 5.3 Solar panels

All three panel prefabs use positive global Power flow with **`flow = rails*state`**. Deployment is built from toggles, saved state, and `MoveModule` animation; it is not just a static output number.

- Small panel mass input: `0.5`; animation time: `6`.
- Big panel mass input: `1.25`; animation time: `8`.
- Dual panel mass input: `4`; animation time: `8`.
- Stored variables include `state`, `state_target`, `current_state`, `flow`, and `rails`.
- `state_target` and `current_state` are saved; derived generation/timewarp values are not.

**Likely changes:** deployment animation/state amplitude, output expression, geometry, and mass. Trace how the animation writes `state` before changing generation. No sunlight, eclipse, or distance-dependent production claim is established by this inspection; verify such behavior rather than assuming physically accurate solar simulation.

### 5.4 Electric wheels

The README's small wheel corresponds to file **`Electric Wheel Medium.prefab`**; the larger one is **`Electric Wheel Big.prefab`**.

| Setting | Medium file | Big file |
|---|---:|---:|
| `Part.mass.input` | `0.3` | `0.5` |
| `WheelModule.power` | `2000` | `3000` |
| `traction` | `40` | `40` |
| `maxAngularVelocity` | `800` | `1600` |
| `wheelSize` | `0.45` | `0.65` |
| Power consumption expression | `on*absSteering*0.01333` | `on*absSteering*0.02` |

`ExternalVariableModule.wheelsInput` feeds `steering`; conversion/animation wiring supplies derived variables. Negative global flow consumes Power using `flow`. `DisableOnNoFlow` references `wheel_on`. `onPartUsed` calls `ToggleEnabled` on the wheel module.

**Likely changes:** torque/power, angular-speed limit, traction, radius, consumption coefficient, mass. Test reverse motion and zero-input idle; `WheelModule.power` is not itself the electrical-consumption expression.

### 5.5 Ion drive

`Ion Drive.prefab` combines the game engine module, custom geometry/plume, audio, heat data, and a multi-resource flow source:

- Display name: `Electric Ion Engine`.
- Mass input: `0.5`; thrust input: `1.25`; ISP input: `1500`; no gimbal.
- Negative global **Power** flow: `flowPercent: 40`, fallback `flowRate.localValue: 500`.
- Negative global **Liquid Fuel** flow: `flowPercent: 1`, fallback `flowRate.localValue: 5`.
- Engine references that FlowModule and uses `engine_on` / `throttle`; part-use event calls `ToggleEngine`.

The original author's v1.0.1 release explicitly says **liquid-fuel use is intentional**. Do not remove it as a presumed bug. Engine runtime may set flow rates from thrust, ISP, mixture and throttle; the fallback rates alone are not measured resource consumption.

**Likely changes:** thrust, ISP, mass, fuel mix, resource requirements, plume and audio. Test all four resource cases: both available, no Power, no Liquid Fuel, neither.

## 6. Mobile rules and compatibility boundaries

1. **Use a mobile-capable SFS version and full bundle.** The pack's README gives the purchase requirement; the original v1.0 release introduced mobile support. Desktop-era instructions saying mobile cannot load any packs predate this support.
2. **Export for the actual target platform.** A Windows bundle is not an Android or iOS bundle, even when they originated from the same prefab.
3. **Do not depend on arbitrary DLL execution on mobile.** Treat game-provided modules as the supported building blocks. The official mobile announcement specifically told authors to re-export and said popular custom modules were being incorporated into the game. [8](https://www.reddit.com/r/SpaceflightSimulator/comments/1povljp/finally_mobile_modding_official/)
4. **Exporting does not add new runtime module implementations to the phone.** If a desired behavior cannot be expressed with game-supported modules, establish support before designing around a desktop-only custom module.
5. **The optional DLL picker is not proof of mobile DLL support.** Cancel it for this asset-only pack; there is no DLL source in this checkout.
6. **Pin game + toolkit + Unity versions together.** Upstream v1.0.1 documents compatibility with `1.6.00.02+` at the cost of breaking `1.6.00.0` and `1.6.00.1`. Do not promise forward compatibility with every future release.
7. **Avoid duplicate versions/identities.** Install only one version of this pack during baseline testing, including checking device trash where applicable.
8. **Keep a mobile budget.** Reuse shared assets, avoid unnecessarily huge textures, and test loading time, memory, and wheel/animation behavior on a real device. No specific polygon/texture hard limit was verified.

No standalone native Linux AssetBundle field or target exists in the inspected exporter. It explicitly builds Windows/macOS/Android/iOS; do not advertise native Linux support based on it.

## 7. Reconstructing the authoring project

### Prerequisites

- A computer with Unity Hub and the editor version specified by the chosen toolkit's `ProjectSettings/ProjectVersion.txt`.
- The compatible official [SFS Modding Toolkit](https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit).
- **Odin Inspector**, obtained under an appropriate license/trial. The toolkit README requires it, and its code imports `Sirenix` editor/runtime namespaces. It is not supplied by this asset repository.
- Unity target-platform build-support modules matching all targets invoked by the exporter. Community setup instructions recommend Android Build Support, iOS Build Support, and Mac Build Support (Mono), in addition to the host's Windows support. Availability depends on the Unity installation/host. [1](https://spaceflight-simulator.fandom.com/wiki/Custom_Part_Creation)
- SFS on the target device with mod access, plus a backed-up test world/craft.

This process builds **AssetBundles**, not an APK or an iOS application. App signing/Xcode deployment is a different workflow; do not confuse it with installing a `.pack` into the existing game.

### Project setup procedure

1. Get the official toolkit at a known compatible revision. The revision inspected here is `855f3eeb094f79c9aa9d27a3d689f51f350b4e06` (commit dated 2026-04-26).
2. In Unity Hub, add/open the **inner `Modding Toolkit/` directory**, which contains `Assets/`, `Packages/`, and `ProjectSettings/`. Do not open this electricity repository alone as if it were the complete project.
3. Use Unity **6000.1.17f1** for the inspected revision; install the required platform modules.
4. Import/configure Odin Inspector and let Unity finish resolving/compiling the toolkit. Resolve compiler errors before modifying assets.
5. Copy **`Electricity/` and sibling `Electricity.meta` together** into the toolkit's `Assets/Resources/` directory. This is a practical placement convention; bundle membership comes from labels/dependencies, not the folder name alone.
6. Preserve all internal `.meta` files. Avoid importing the same assets twice under different paths or copying this repository's `.git` directory into Unity.
7. Let Unity import. Open representative prefabs and verify no missing scripts, textures, materials, resource types, or categories.
8. Check that the existing `n2o4s_electricity` label appears in the AssetBundle list. Keep the variant empty for a faithful baseline.
9. Inspect `Scriptables/PackData.asset`, its icon, category, and Power resource.
10. **Build and test an unmodified baseline before changing gameplay.** Record the actual game version and exporter revision used.

The reference scan in section 12 found every externally referenced GUID in the inspected toolkit. That is encouraging for reconstruction, but **does not replace a Unity import/compile check**.

### Creating a new part safely

1. Duplicate the closest working prefab **inside Unity**, generating a fresh asset GUID. Use a new unique prefab name when the intent is a new part, not a replacement.
2. Preserve/add `Part`, variables/orientation, appropriate geometry/mesh, attachment and collision modules; keep the correct Parts layer.
3. Set display text/translation flags, mass, center of mass, variants, and picker-category tags.
4. Add functionality using game-supported modules, wiring all object and variable references explicitly.
5. Configure part-use events and saved state as required. Test click activation/staging separately.
6. Assign the new prefab and appropriate new assets to the intended bundle. Do not accidentally retain another pack's label.
7. Export and test on the target platform. For edits to an existing part, preserve its identity unless deliberately accepting old-craft incompatibility.

## 8. Exact `.pack` creation method

### 8.1 Unity UI workflow for this repository

With the project from section 7 compiling:

1. Save assets and inspect the Unity Console for errors.
2. Open **`SFS > Build Pack`**.
3. Set **Output File Name** to a filename stem, e.g. `Electricity_baseline` (**without** `.pack`; the exporter appends it).
4. Drag existing `Electricity/Scriptables/PackData.asset` into the pack data field. Confirm metadata and icon.
5. Select AssetBundle label **`n2o4s_electricity`**.
6. Invoke the all-platform build button. In this source its method is `BuildPartPackModForAllPlatforms`; displayed wording may vary with Odin formatting/toolkit revision.
7. When the **Custom module (Optional)** DLL picker opens, **Cancel** it for this pack.
8. Wait for all platform bundles and serialization. Inspect the **entire Console**, not only the final success message.
9. The result is at:

   ```text
   <toolkit project>/Assets/ModBuilder/Electricity_baseline.pack
   ```

10. Distribute/install that `.pack` only, not `.pack.meta`, cache folders, manifests, or source YAML. Keep it outside the source checkout unless release-artifact policy deliberately calls for tracking binaries.

**Important:** older community instructions describe selecting Windows/Mac checkboxes. The inspected current `Builder.cs` has **four hard-coded target builds**, not those selectors. Follow the actual source/revision in use. [1](https://spaceflight-simulator.fandom.com/wiki/Custom_Part_Creation)

### 8.2 Exporter internals — toolkit verified

Source: `Modding Toolkit/Assets/Editor/Builder.cs`, class `SFS_PartPackModBuilder`.

1. Create `Assets/ModBuilder/` and temporary `Assets/ModBuilder/Cache/`.
2. Require `PackData`. Assign its importer to the selected bundle name/variant. If data was newly created in the builder, save it temporarily as an asset first; using the existing persistent PackData is clearer here.
3. Optionally read a selected DLL into `CodeAssembly`; cancellation leaves it unset.
4. Invoke:

   ```csharp
   BuildPipeline.BuildAssetBundles(outputDirectory, BuildAssetBundleOptions.None, target);
   ```

   for the following platform targets:

   | Cache subfolder | Unity target | JSON field |
   |---|---|---|
   | `Windows` | `StandaloneWindows64` | `WindowsBuild` |
   | `Mac` | `StandaloneOSX` | `MacBuild` |
   | `Android` | `Android` | `AndroidBuild` |
   | `IOS` | `iOS` | `IOS_Build` |

5. For each target, read the output bundle named exactly `assetBundleLabel` into a byte array. Note that `BuildAssetBundles` builds the project's labeled bundles; the wrapper reads the selected one.
6. Serialize an `AssetBundlePack` with Newtonsoft `JsonConvert.SerializeObject` and write `<outputFileName>.pack` as text.
7. Delete the temporary cache directory and its `.meta`, log completion, and refresh the asset database.

The container class is:

```csharp
[Serializable]
public class AssetBundlePack
{
    public byte[] MacBuild, WindowsBuild, AndroidBuild, IOS_Build;
    public byte[] CodeAssembly;
}
```

Newtonsoft serializes these `byte[]` values as Base64 strings. A schematic container is therefore:

```json
{
  "MacBuild": "<base64 AssetBundle>",
  "WindowsBuild": "<base64 AssetBundle>",
  "AndroidBuild": "<base64 AssetBundle>",
  "IOS_Build": "<base64 AssetBundle>",
  "CodeAssembly": null
}
```

**This schematic is not an installable pack.** The strings must contain real Unity-built bundles. Pack metadata is a ScriptableObject **inside the bundle**, not top-level JSON metadata.

### 8.3 Exporter pitfalls

- It does not robustly abort on every failed target build. Missing output is logged and can result in a null platform field while later steps still print completion. Validate output fields and Console errors explicitly.
- A stale cache from an interrupted run can mislead inspection. For a clean rebuild, clear only the generated `Assets/ModBuilder/Cache/` after stopping any build, then rebuild and verify timestamps/logs.
- Labels with dots are split into name/variant by the builder. The current undotted label avoids this issue; do not casually rename it or add multiple dots.
- Multiple labeled bundles can introduce cross-bundle dependencies. The wrapper contains only the selected label's output, not every sibling bundle automatically. Inspect Unity's generated manifests/dependencies if changing labeling.
- The official exporter is an Odin editor-window workflow with a file picker and a non-public build method. The original repository supplied no `-executeMethod`/CI entrypoint. **This branch now adds a separate noninteractive entrypoint and artifact workflow** (section 17; [setup guide](docs/PACK_BUILD.md)). It still needs a correctly licensed/configured Unity runner, and real Unity execution has not been tested here.
- Renaming a ZIP to `.pack`, concatenating YAML, or rewrapping only a desktop bundle cannot generate valid mobile bundle contents.

### 8.4 Lightweight container check after a real build

Run this against an actual exported pack (Python standard library only). It checks container presence/Base64, **not runtime compatibility**:

```python
import base64
import json
from pathlib import Path

path = Path("Electricity_baseline.pack")
pack = json.loads(path.read_text(encoding="utf-8-sig"))
assert isinstance(pack, dict), "Expected a JSON object"
for key in ("WindowsBuild", "MacBuild", "AndroidBuild", "IOS_Build"):
    value = pack.get(key)
    assert isinstance(value, str) and value, f"Missing platform payload: {key}"
    payload = base64.b64decode(value, validate=True)
    assert payload, f"Empty payload: {key}"
    print(key, len(payload), "bytes; header:", repr(payload[:16]))
assert pack.get("CodeAssembly") is None, "Unexpected custom code in asset-only pack"
```

For modern Unity bundles a `UnityFS` header is a useful sanity clue, but even a plausible bundle header does not establish that it contains the correct assets or works with the installed SFS build. Preserve a SHA-256 checksum of the final file in release notes for reproducibility.

## 9. Historical compatibility context

Original upstream release notes inspected through GitHub:

| Release | Date | Relevant context |
|---|---|---|
| `v0.5` | 2023-07-20 | Pre-mobile-era release; v1.0 notes direct SFS 1.5.10 users to this version. |
| `v1.0` | 2025-12-22 | Introduced mobile support, dual solar panel, working wheels, variant/mesh battery, and timewarp generation fix. Now marked archived/do not download upstream. |
| `v1.0.1` | 2025-12-26 | Changes compatibility to SFS `1.6.00.02+`, explicitly breaking early `1.6.00.0`/`.1`; wheel and ion-drive rebalance. Current PackData matches this version. |

Sources: [v0.5](https://github.com/VerdiX094/sfs-electricity/releases/tag/v0.5), [v1.0](https://github.com/VerdiX094/sfs-electricity/releases/tag/v1.0), [v1.0.1](https://github.com/VerdiX094/sfs-electricity/releases/tag/v1.0.1).

The v1.0.1 release lists `Electricity_v1.0.1.pack` (2,514,398 bytes). The release metadata was accessible, but downloading the binary failed at GitHub's release-assets host in this environment. Its actual payloads were **not** independently inspected. The format findings above come from official exporter source, not a claim to have decoded this release artifact.

## 10. Installing a built pack

From the repository README (keep the exact underscore in `Custom_Assets`):

### Android

```text
Android/media/com.StefMorojna.SpaceflightSimulator/files/Mods/Custom_Assets/Parts
```

### iOS / Files app

```text
Browse/On my iPhone/Spaceflight Simulator/files/Mods/Custom_Assets/Parts
```

`Browse/On my iPhone` describes Files-app navigation, not a literal Unix directory prefix.

### Steam

Open the game → **Mod Loader** → **Open Mods Folder** → `Custom_Assets/Parts`.

### Safe installation sequence

1. Back up valuable worlds and blueprints.
2. Remove the old version from the Parts directory; check trash for duplicates if applicable.
3. Copy the actual `.pack` into the existing Parts directory, not its parent `Mods` directory and not a guessed `Android/data` path.
4. Restart SFS; inspect Mod Loader errors and enable the pack if necessary.
5. Verify the Electricity category and test in a disposable world.

Folder conventions can change across game versions; if the installed game's own mod-folder UI disagrees with older instructions, investigate the version-specific path rather than creating several speculative copies.

## 11. Troubleshooting and test plan

| Symptom | First checks |
|---|---|
| Pack absent from loader | Actual `.pack` extension, exact folder, mobile full bundle, game version, restart. |
| Cannot deserialize pack | Wrong file (e.g. `.meta`/README/source archive), corrupt/truncated download, invalid JSON. |
| Unsupported runtime platform | Target payload missing, null, or built for another platform; rebuild with correct support modules. |
| Null-reference error | Duplicate versions/trash, incompatible game/toolkit, missing scripts/assets/event targets; not one guaranteed cause. |
| Category/parts missing | Variant tags/category references, intended bundle membership, dependencies, picker priorities. |
| Ground clipping / unclickable part | Parts layer, collision/click flags, collider polygon reference, transforms. |
| No generation at timewarp | `rails` mapping, MathModule expression/output reference, generation state, full battery/no space. |
| Wheel consumes power while idle / free powered motion | Converters, steering/on variables, flow expression, DisableOnNoFlow wiring; test both steering directions. |
| Ion engine stops | Both fuel types, throttle, engine state, available storage, flow source reference. |
| Mesh/triangulation errors | Shape vertices/order/degenerate geometry and mesh generation; preserve a known-good prefab for comparison. |

Negative picker priorities are **not universally forbidden**: this repository itself uses them, including the ion engine's Engines category priority `-20` and the big wheel's Electricity priority `-1`. However, an early upstream release recorded a category-priority interaction causing missing parts. Treat priority changes as a compatibility test area, not an automatic fix.

### Minimum regression matrix for later edits

- [ ] Unmodified baseline exports without Unity errors and loads on the chosen device/game version.
- [ ] Pack metadata/icon and category render correctly; expected variants are visible.
- [ ] Each battery size has correct mass, dimensions, initial charge, storage, attachment, collision, and resource display.
- [ ] RTGs charge connected batteries; full batteries do not create resource overflow/errors.
- [ ] Solar panels deploy/retract; saved deployment survives reload; stowed/deployed production matches intent.
- [ ] RTG/solar generation checked at 1× and several physics/rails timewarp settings, and after returning to 1×.
- [ ] Wheels tested idle, forward, reverse, on/off, empty/full batteries, slope/contact, and save/load.
- [ ] Ion engine tested through throttle range, toggling, and depletion of each required resource independently.
- [ ] Shared-resource transfer tested across connected parts, disconnected craft, and docking if relevant.
- [ ] Existing craft/blueprints still load; legacy battery references are not silently removed.
- [ ] Modified pack tested alone first, then with the user's intended other packs; no duplicate pack versions.
- [ ] Each advertised platform tested or explicitly marked untested.

## 12. Research verification performed and limits

### Performed

- Read `README.md`, `README.md.meta`, directory metadata, all prefab component layouts, ScriptableObjects, and relevant texture import metadata.
- Counted repository assets and inspected bundle labels, PackData, category/resource references, formulas, events, and variant definitions.
- Checked existing asset/folder companion metadata: no missing companion `.meta` under `Electricity/`; no duplicate GUIDs among its metadata plus the two root metadata files.
- Mapped **every prefab `m_Script` GUID** to a script in the pinned official toolkit: none unresolved.
- Scanned external GUID references across this pack's `.prefab`/`.asset` files against this repository plus the toolkit: all resolved, including materials, stock textures, audio, fuel, and categories. This was a GUID-level check, not a validation of every sub-object `fileID` or runtime event signature.
- Read official `Builder.cs`, `PackData.cs`, `Part.cs`, resource/flow/wheel definitions, MathModule and relevant mod-support code.
- Checked upstream release metadata and cross-checked community mobile/export guidance. Where community UI instructions diverge, exporter source takes precedence.

### Not performed / not established

- Unity import, compilation, editor preview, or a real AssetBundle build. No Unity executable was found on PATH in this sandbox.
- Any Android/iOS/Steam runtime tests or validation of current DLC entitlement behavior beyond documentation.
- Download/decoding of the published v1.0.1 binary (download blocked as described above).
- Full private game-loader/runtime-source audit, exact physical unit conversion, or guarantees of old-save/forward-version compatibility.
- A license grant for redistribution: no LICENSE file was found in this checkout, and upstream GitHub metadata reports no detected license. Public source availability is not itself blanket permission to redistribute derivatives. Preserve attribution and establish permission/license terms before public distribution; Unity/Odin/game assets have their own terms.

## 13. Source index and reproducibility

### Primary sources

- **Local baseline:** `README.md`, `README.md.meta`, `Electricity/**/*.prefab`, `Electricity/**/*.asset`, and their metadata at repository baseline above.
- **Original upstream:** [repository](https://github.com/VerdiX094/sfs-electricity), [releases](https://github.com/VerdiX094/sfs-electricity/releases).
- **Official toolkit revision inspected:** [`855f3eeb094f79c9aa9d27a3d689f51f350b4e06`](https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit/tree/855f3eeb094f79c9aa9d27a3d689f51f350b4e06).
- **Exporter/container definition:** [`Assets/Editor/Builder.cs`](https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit/blob/855f3eeb094f79c9aa9d27a3d689f51f350b4e06/Modding%20Toolkit/Assets/Editor/Builder.cs).
- **Editor version:** [`ProjectVersion.txt`](https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit/blob/855f3eeb094f79c9aa9d27a3d689f51f350b4e06/Modding%20Toolkit/ProjectSettings/ProjectVersion.txt).
- **Module definitions:** [`Assets/Scripts/Parts`](https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit/tree/855f3eeb094f79c9aa9d27a3d689f51f350b4e06/Modding%20Toolkit/Assets/Scripts/Parts); particularly `Fuel/`, `Interaction/WheelModule.cs`, `ModSupport/`, and `Parts/Part.cs`.
- **Pack metadata definition:** [`PackData.cs`](https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit/blob/855f3eeb094f79c9aa9d27a3d689f51f350b4e06/Modding%20Toolkit/Assets/Scripts/Needed/PackData.cs).

### Secondary/context sources

- Community custom-part tutorial, including its own work-in-progress warnings; inspected setup, export, mobile, and troubleshooting sections. Some portions still describe older UI. [1](https://spaceflight-simulator.fandom.com/wiki/Custom_Part_Creation)
- Official mobile-modding announcement posted by Stef_Moroyna; re-export requirement and incorporation of modules into the game. [8](https://www.reddit.com/r/SpaceflightSimulator/comments/1povljp/finally_mobile_modding_official/)

For repeat research, inspect the source at the pinned toolkit revision rather than silently using moving `main`. The upstream v1.0.1 pack predates the inspected toolkit commit; its exact historical authoring-toolkit revision is **not known** from this repository.

## 14. Working context for the next modification request

**Current status:** second modification pass implemented in source. Ion thrust is `7.25`, ISP is `1800`, and its Power mixture coefficient is `8.275862` to preserve the original nominal Power draw. A separate stock-module-based Electric RCS Thruster now uses Power + Liquid Fuel; massless-only propulsion remains deferred. See section 16 for current settings, limitations, provenance, and checks. Section 15 is historical, not the current configuration. A GitHub Actions build/artifact system has also been added; see section 17 and `docs/PACK_BUILD.md`. Its Python tooling is tested, but its Unity entrypoint is not yet compiled/executed here.

Before implementing:

1. Record requested behavior and exact target game version/platform (Android and/or iOS).
2. Identify whether the change is visual, numeric balance, variant/state wiring, or a new behavior requiring module support.
3. Use the file/module map in section 5; preserve existing identities and legacy compatibility unless intentionally changing them.
4. Separate source changes from Unity build validation and real-device verification. Do not report an unbuilt edit as a working mobile pack.
5. Update this context document with new findings, build versions, test results, and remaining uncertainties.

### Future build/change ledger

| Date | Change / build | Game / platform | Unity / toolkit revision | Checks performed | Open issues |
|---|---|---|---|---|---|
| 2026-11-26 | Initial research; no gameplay changes or build | Not runtime-tested | Source inspected: 6000.1.17f1 / `855f3ee…` | Repository inventory, GUID/label scan, official exporter/module-source review | Baseline Unity import/build and device tests pending |
| 2026-11-26 | Ion engine: thrust 2.5, ISP 3000; no build (superseded by next row) | Mobile intended; exact game/device version not supplied | Toolkit `855f3ee…`; shared runtime source `5f3077c…` | Standard-library source regression tests; exact asset-diff review | At that pass: fuel removal and Power-only electric RCS deferred |
| 2026-11-26 | Ion engine: thrust 7.25, ISP 1800, old Power draw preserved; mixed-resource Electric RCS added; no build | Mobile intended; exact game/device version not supplied | Same pinned toolkit/shared source | 11 source regression tests; GUID/local-reference validation; stock-template and baseline diff review | Unity export and device tests pending; shared craft-wide RCS switch applies |
| 2026-11-26 | GitHub `.pack` artifact pipeline and noninteractive Unity build tools added; not remotely executed | Targets Windows/macOS/Android/iOS | Unity 6000.1.17f1 / toolkit `855f3ee…` | 22 offline tests; workflow YAML parse/gating review; current Unity asset YAML parse | Licensed runner/Odin setup, first real Unity compilation/export, and device testing pending |

## 15. First modification pass — ion engine and electric RCS feasibility

> **Historical:** the current settings and mixed-resource RCS implementation are in section 16. This section records why the originally requested **Power-only** RCS was deferred; it does not prohibit an RCS using Power **and** Liquid Fuel.

### Request and decision

The user requested double ion-engine thrust and efficiency, removal of the stock
Liquid Fuel tank requirement if safely possible, and a separate Power-only RCS
part if supported. They explicitly allowed leaving the latter two unchanged when
limited by the game. No changes to the shared Power resource, batteries, or game
runtime were requested.

| Requested change | Finding | Action |
|---|---|---|
| Double ion thrust | A serialized `EngineModule.thrust` value | Changed `1.25` to **`2.5`**. |
| Double ion efficiency | A serialized `EngineModule.ISP` value | Changed `1500` to **`3000`**. |
| Remove Liquid Fuel requirement | The mixed-resource configuration is intentional, but simply deleting fuel breaks correct metering of massless Power in the inspected runtime | **Deferred; retained both existing flow sources.** |
| Separate electric RCS | A separate prefab with `RcsModule` is supported; correct Power-only metering has the same massless-resource limitation | **Deferred; no RCS prefab created and stock RCS untouched.** |

### Additional primary-source investigation

The official toolkit's `EngineModule` and `RcsModule` are authoring stubs, but
Starshot Games also publishes shared part-module runtime source. Inspected:

- Repository: [Starshot-Games/SFS-Shared-Parts](https://github.com/Starshot-Games/SFS-Shared-Parts).
- Pinned revision: [`5f3077c5387b5813cbe0d26da981f68c55d6125f`](https://github.com/Starshot-Games/SFS-Shared-Parts/tree/5f3077c5387b5813cbe0d26da981f68c55d6125f), dated 2026-11-25.
- [`Fuel/FlowModule.cs`](https://github.com/Starshot-Games/SFS-Shared-Parts/blob/5f3077c5387b5813cbe0d26da981f68c55d6125f/Fuel/FlowModule.cs): `SetMassFlow`, `GetMassFlowPerUnit`, source validation and flow update behavior.
- [`Physics/EngineModule.cs`](https://github.com/Starshot-Games/SFS-Shared-Parts/blob/5f3077c5387b5813cbe0d26da981f68c55d6125f/Physics/EngineModule.cs): `RecalculateMassFlow` calls `source.SetMassFlow(thrust * multiplier * throttle / Isp)`.
- [`Physics/RcsModule.cs`](https://github.com/Starshot-Games/SFS-Shared-Parts/blob/5f3077c5387b5813cbe0d26da981f68c55d6125f/Physics/RcsModule.cs): references a configurable FlowModule; calls `SetMassFlow(0)` when idle and `SetMassFlow(thrust * throttle / ScaledISP)` when firing.
- [`Fuel/ResourceModule.cs`](https://github.com/Starshot-Games/SFS-Shared-Parts/blob/5f3077c5387b5813cbe0d26da981f68c55d6125f/Fuel/ResourceModule.cs): storage, mass recalculation, and notifications to flow modules.
- Official toolkit `Assets/Resources/Parts/RCS.prefab`: stock mass `0.05`, thrust `1.5`, ISP `120`, three nozzle effects, a Liquid Fuel FlowModule, and `ToggleRCS` event. It can be a template for a distinct part, but its existence alone does not solve massless flow.

The runtime module script GUIDs match the toolkit's corresponding definitions.
However, this shared-source revision is newer than the original pack's release;
it is **not proof of the exact implementation in every installed SFS 1.6 build**.
Without an exact target game version and device tests, the conservative choice
is to preserve the working fuel mixture rather than introduce a speculative
mobile workaround.

### Why changing the resource list alone is not a correct fix

The inspected `FlowModule.SetMassFlow` performs:

```text
massFlowPerUnit = sum(resource.resourceMass * flowPercent)
totalResourceFlow = massFlowPerUnit > 0 ? requestedMassFlow / massFlowPerUnit : 1
flowRate = totalResourceFlow * flowPercent   (for each configured source)
```

This pack's Power has `resourceMass = 0`; the stock Liquid Fuel asset has
`resourceMass = 1`. The existing mixture therefore supplies a nonzero denominator
through its Liquid Fuel source.

If only Power remains, the denominator becomes zero. With the ion engine's
existing Power `flowPercent = 40`, the fallback writes a rate of **40**, regardless
of requested thrust, throttle, or ISP, including when `SetMassFlow(0)` is called.
A Power-only stock RCS conversion similarly gets a constant rate instead of
per-firing consumption. Thus merely swapping a resource can appear to work but
can drain batteries while idle and lose the requested efficiency behavior.

This is a **limitation of the inspected mass-flow calculation for massless-only
propulsion**, not a universal claim that custom resources or electric RCS are
impossible in all SFS versions.

Possible future solutions require separately scoped work and runtime validation:

- A game-supported corrected flow implementation for massless-only propulsion.
- A thoroughly designed data-module metering/gating workaround that handles
  idle/off state, throttle, RCS nozzle activation, depletion, restart, and reload.
  A second drain module alone is not enough: the propulsion source must also
  receive correct no-resource state notifications and stop thrust reliably.
- A custom runtime module, only on platforms/game loaders that support it; do
  not assume a DLL can be added to mobile.
- Giving Power a nonzero mass changes the meaning of the shared resource and
  can affect existing battery mass calculations and mixed-resource balance.
  It was **not** used as a workaround.

### Exact implementation scope

Only two serialized gameplay values were changed, both in
`Electricity/Parts/Ion Drive.prefab`:

```text
EngineModule.thrust.input: 1.25 -> 2.5
EngineModule.ISP.input:    1500 -> 3000
```

The prefab's identity, event wiring, engine mass, geometry, resource references,
flow percentages and rates, and metadata are unchanged. The original fuel-tank
requirement remains. No RCS part, custom C# assembly, or altered Power resource
was added. PackData is still `v1.0.1`: do not confuse the unbuilt branch with a
new published version. Assign a release version when an actual export is ready.

Doubling thrust and ISP together keeps the nominal `thrust / ISP` ratio equal:
`1.25 / 1500 = 2.5 / 3000`. Under the inspected runtime this means the nominal
full-throttle resource rate is unchanged at the same difficulty/orientation,
while thrust and the displayed ISP each double. Doubling efficiency does not
mean doubling the electrical-consumption coefficient.

### Validation and remaining checks

Run source regression checks from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

These check the exact doubled engine values, preserved two-resource mixture,
and engine/flow/event wiring. An exact diff against the repository baseline was
also checked to ensure only those two gameplay lines changed. They do **not**
execute Unity or the SFS simulation.

Before calling this an installable/tested modification:

- Export a new `.pack` through the compatible toolkit using section 8.
- Verify the engine's displayed thrust and efficiency on the target device.
- Test ignition, partial/full throttle, off/idle state, and depletion of both
  resources; compare nominal full-throttle drain with the original pack.
- Confirm old craft still load, and ensure only one Electricity pack is installed.
- Record the exact game/platform and export/test results here.

**Build/runtime status:** no Unity editor available on PATH; no `.pack` built;
no real-device tests performed. The upstream release download is unchanged and
will not contain this branch's stat increases.

## 16. Second modification pass — retuned ion engine and mixed-resource electric RCS

### Current request and feasibility

The user now accepts the stock Liquid Fuel requirement for both propulsion types.
This removes the zero-mass denominator issue described in section 15. The inspected
stock `RcsModule` already supports a configurable multi-resource `FlowModule`, so
an **additional** RCS part consuming Power **and** Liquid Fuel is feasible without
new runtime code. No Power-only metering workaround or global resource change is
needed. This is source-supported feasibility, **not a claim of completed mobile
runtime validation**.

The toolkit and shared-source revisions remain those pinned in sections 13/15:

- [Stock RCS template](https://github.com/Stef-Moroyna/Spaceflight-Simulator--ModdingToolkit/blob/855f3eeb094f79c9aa9d27a3d689f51f350b4e06/Modding%20Toolkit/Assets/Resources/Parts/RCS.prefab).
- [RCS runtime controls/metering](https://github.com/Starshot-Games/SFS-Shared-Parts/blob/5f3077c5387b5813cbe0d26da981f68c55d6125f/Physics/RcsModule.cs).
- [Flow calculation and all-resources validation](https://github.com/Starshot-Games/SFS-Shared-Parts/blob/5f3077c5387b5813cbe0d26da981f68c55d6125f/Fuel/FlowModule.cs).

### Ion engine: requested values and preserved Power consumption

Current serialized settings in `Electricity/Parts/Ion Drive.prefab`:

| Setting | Original upstream | First pass (superseded) | Current |
|---|---:|---:|---:|
| Thrust input | 1.25 | 2.5 | **7.25** |
| ISP input | 1500 | 3000 | **1800** |
| Power `flowPercent` | 40 | 40 | **8.275862** |
| Liquid Fuel `flowPercent` | 1 | 1 | **1** |

“Old Power consumption” is interpreted as the nominal per-time draw of the
original upstream engine. The first-pass engine has the same nominal draw because
both thrust and ISP were doubled, so either old baseline gives the same answer.
This does not mean preserving Power per unit of thrust or copying the fallback
`flowRate.localValue`: the runtime calculates the actual rates.

With Power mass `0`, Liquid Fuel mass `1`, and fuel ratio `1`, the inspected
mass-flow denominator is `1`. At a given throttle/difficulty/orientation:

```text
Power rate = (thrust / ISP) * Power.flowPercent * operating_factor

Old: (1.25 / 1500) * 40 = 1/30
New required coefficient:
    40 * (1.25 / 1500) / (7.25 / 1800) = 240/29 = 8.275862068965...
New: (7.25 / 1800) * (240/29) = 1/30
```

The serialized `8.275862` approximates `240/29` within the precision of the C#
`float` mixture field (relative error about `4e-8` after float32 conversion).
Nominal full-throttle Power draw therefore remains approximately **0.0333333
Power units per simulation second**, and scales with the same throttle,
difficulty ISP multiplier, and orientation/scale factor as before. Do not equate
these resource units to measured physical kW without separate verification.

Liquid Fuel consumption is **not** held constant: it scales from `1.25/1500` to
`7.25/1800`, a factor of **29/6 ≈ 4.83333** at matching operating conditions.
This follows the requested thrust/ISP change; only Power was requested unchanged.

No other ion-engine gameplay data was changed: geometry, mass, identity, event
wiring, fuel source, and fallback local rates are preserved. The Power resource
and all existing battery/generator definitions are unchanged.

### New Electric RCS Thruster

New source files:

```text
Electricity/Parts/Electric RCS Thruster.prefab
Electricity/Parts/Electric RCS Thruster.prefab.meta
```

This is a **standalone copy of the stock toolkit RCS prefab**, not a variant or
replacement referencing the stock RCS root prefab. It has a newly assigned asset
GUID `b07feae2bb4f48f28f01c25585df2975`, distinct from stock RCS GUID
`fc132a1f34e977b42846895ff3faeb46`, and bundle label `n2o4s_electricity`.
Local object IDs may match those in the template; those IDs are scoped to each
asset and do not make it the same prefab. Metadata was authored with a fresh GUID
because Unity is unavailable here; verify its import in the real toolkit project.

The copied stock part's changes are limited to:

- Root name and literal display name: **Electric RCS Thruster**.
- Description explicitly requires **Power and Liquid Fuel**.
- Picker category changed to this pack's **Electricity** category.
- Added a negative/global Power source before the existing negative/global
  Liquid Fuel source. Mixture is **`8.275862 : 1`**, matching the current ion
  engine. The user did not specify RCS consumption balance; this reuses the
  engine mixture rather than inventing a new resource or fuel type.
- Fresh asset metadata with this pack's bundle label.

Retained stock settings and behavior:

| Setting | Value |
|---|---:|
| Mass input | 0.05 |
| Thrust | 1.5 |
| ISP | 120 |
| Direction-angle threshold | 45 |
| Torque-angle threshold | 40 |
| Thrust position | `(0.3, 0)` |
| Nozzle force normals | `(0, 1)`, `(-1, 0)`, `(0, -1)` |
| Activation | Dynamic `ToggleRCS(UsePartData)` event, `m_Mode: 0` |

Stock mesh/shape, attachment, materials, and three nested exhaust-effect instances
are preserved. The new part deliberately shares the stock appearance and normal
RCS controls; its name/category distinguish it. The shared nested exhaust asset
is `Resources/Effects/RCS Exhaust.prefab` in the toolkit, GUID
`6cf6053aa4d930c41bdae89818543319`. Keep that toolkit asset and its metadata;
it should be bundled as a dependency. No additional textures, custom scripts,
or DLL were added, and the stock RCS asset was not edited.

Both sources initialize their fallback rates to `0`. The stock RCS runtime calls
`SetMassFlow(0)` while idle/off and `SetMassFlow(thrust * firing_nozzles /
ScaledISP)` while firing. Because the fuel source keeps the denominator nonzero,
zero requested flow now produces zero rates for **both** resources without the
massless-only constant-rate fallback. At default difficulty/scale the nominal
per-firing-nozzle rates are:

```text
Liquid Fuel: 1.5 / 120              = 0.0125 resource units/s
Power:       (1.5 / 120) * (240/29) ≈ 0.1034483 resource units/s
```

Rates sum with the stock module's count of firing nozzles. These are static
source-model calculations; actual device behavior still requires testing.

### Normal RCS limitations retained

- This is a separate **part**, not a new independent RCS control channel. The
  stock runtime uses the craft-wide `Rocket.arrowkeys.rcs` switch for all RCS.
- A source becoming unavailable makes the electric RCS use the stock shutdown
  path, which can disable **craft-wide RCS**, including ordinary thrusters on the
  same craft. Restore resources and re-enable RCS normally. Mixed-craft depletion
  behavior is a required test case, not a claimed independent shutdown feature.
- Requires accessible charged Power storage **and** stock Liquid Fuel storage.
  The shared FlowModule validates every listed resource; Infinite Fuel cheats
  can change depletion behavior as usual.
- Stock RCS force selection, rotation/translation inputs, timewarp constraints,
  plume/audio behavior, and game-version compatibility still apply.
- A separate electric-only control group, Power-only operation, new visuals, and
  revised RCS thrust/efficiency were not requested or implemented.

These ordinary stock-control constraints are compatible with the user's request
to use the game's RCS system; no new blocker was found for the accepted mixed
fuel design.

### Checks performed and required next steps

Run:

```sh
python3 -m unittest discover -s tests -v
```

**11 source tests pass**, including:

- Exact ion thrust/ISP and two-resource configuration.
- Computed ion Power draw compared with the original at several throttles,
  difficulty ISP multipliers, and orientation multipliers, using float32 mixture
  precision; zero-throttle and expected Liquid Fuel metering.
- RCS identity, bundle/category, stock stats, three nozzles, event/flow wiring,
  same ion mixture, and zero idle/arithmetic flow at zero firing nozzles.
- Unique pack metadata GUIDs and valid local references in the new prefab.

Additionally, all external GUIDs in the new RCS prefab were resolved against the
pack plus the pinned official toolkit, and its diff against the stock template
was reviewed to exclude unintended geometry/control changes. Existing-asset
changes against the original repository baseline are restricted to the ion
engine's three settings above. The inventory is now **14 prefabs** under
`Electricity/` (one more than the original inventory in section 3).

**These are static/arithmetic checks, not Unity or game tests.** Before release:

1. Import into the pinned-compatible toolkit and check the new prefab and nested
   dependencies for missing scripts/references or import errors.
2. Export a new all-platform `.pack`; inspect Console and platform payloads.
3. On the chosen device/game version, verify displayed ion stats and compare
   original/new Power draw at 0%, partial and full throttle. Verify higher fuel
   draw is expected and both depleted-resource paths stop the engine.
4. Find Electric RCS in Electricity; test stock and electric parts together,
   translation, rotation, mirrored/flipped mounting, no-input idle, and RCS off.
5. Test Power depletion, fuel depletion, missing tanks, restoring resources,
   re-enabling RCS, and save/load. Check the shared craft-wide shutdown behavior.
6. Confirm ordinary RCS still uses only Liquid Fuel and old craft still load.
7. Verify only one Electricity pack is installed. Record target versions/results
   and assign a new release version before distributing the modified `.pack`.

**Current delivery status:** source assets/tests/docs updated; PackData remains
`v1.0.1` until an actual release is prepared. No Unity export, `.pack` artifact,
or real-device validation has been performed. The upstream release link is not
an installer for these unbuilt branch changes.

## 17. GitHub Actions `.pack` artifact system

The repository now contains a build system, rather than only instructions for
the toolkit's interactive exporter. Full setup/usage:
**[docs/PACK_BUILD.md](docs/PACK_BUILD.md)**.

### Added components

- `.github/workflows/build-pack.yml`: hosted source checks on relevant pushes/PRs;
  manual-only protected Unity job on a self-hosted Windows `sfs-unity` runner;
  pack/checksum/provenance upload and separate diagnostic log upload.
- `build-tools/Editor/SfsPackBuild.cs`: public
  `SfsElectricity.CI.PackBuilder.BuildPlatform` batch-mode entrypoint using actual
  Unity `BuildPipeline.BuildAssetBundles`. Checks editor/target, required assets,
  missing scripts, strict build errors, outputs and sibling-bundle dependencies.
- `scripts/ci/build_pack.py`: pinned-template/license-dependency preflight,
  disposable project copy with stable asset metadata, four separate target-specific
  Unity processes, official-schema packaging, checksum and provenance generation.
- `scripts/ci/validate_pack.py`: rejects incomplete schema/platforms, custom DLLs,
  duplicate JSON fields, bad Base64, malformed/truncated UnityFS headers and file
  sizes. It is structural validation, not an asset/game-compatibility proof.
- `tests/test_pack_build.py`: offline unit/mock checks, including successful
  orchestration and a failed rerun not reusing an earlier pack.
- `.gitignore`: excludes generated workspace, caches, Python bytecode and artifacts.

### Necessary configuration

Unity/Odin cannot be assumed present on GitHub-hosted runners. Before the first
manual build, provision the dedicated self-hosted Windows runner with a valid
Unity license, Unity 6000.1.17f1 and all four build-support modules, and the clean
pinned toolkit plus privately licensed Odin. Configure runner machine paths:

```text
SFS_UNITY_EDITOR=<absolute path to Unity.exe>
SFS_TOOLKIT_PROJECT=<absolute path to inner Modding Toolkit project>
```

Create/protect GitHub environment `sfs-pack-build`, restrict execution to reviewed
trusted source, and set repository variable `SFS_UNITY_BUILDS_ENABLED=true` only
after setup. Pull requests never run this workflow's Unity/self-hosted job.
Manual dispatch still runs repository code, so do not approve untrusted branches.
No license keys, GitHub PATs, or proprietary packages are added to this repository.

### Artifact contract

On success, Actions uploads `Electricity-pack-<full commit SHA>` with:

```text
Electricity_<12-character commit prefix>.pack
Electricity_<12-character commit prefix>.pack.sha256
build-info.json
```

All four platform payloads must exist and validate. `CodeAssembly` is null. The
pack uses the same bundle label and source PackData version as the current assets;
filename/provenance identify the source revision without silently changing the
in-game version. GitHub's download is an artifact ZIP: extract it and install the
**`.pack` inside**, not the ZIP. Pack artifacts expire after 14 days; diagnostic
logs after 7 days. This does not create a GitHub Release or automatically publish
pack source/licenses.

### Validation status and remaining work

**22 offline tests pass** (11 gameplay-source tests plus 11 build-tool tests).
The workflow YAML parses and its manual-only self-hosted gate, protected-environment
name, read-only repository permission and SHA-pinned actions were checked. The two
modified/new Unity prefab YAML files also parse. Synthetic UnityFS headers in
unit tests are temporary fixtures only and are not installable or delivered as
real packs.

No compatible Unity executable/Odin/license exists in the development sandbox;
the C# entrypoint has **not** been compiled or exercised by Unity. No workflow
was pushed/dispatched, no runner/environment was configured remotely, and no
real GitHub `.pack` artifact has been produced by this work. The first configured
runner build must verify editor compilation, imports, cross-platform modules and
actual bundle generation; then perform the section 16 real-device tests. This
build-system task does not change the gameplay assets further.
