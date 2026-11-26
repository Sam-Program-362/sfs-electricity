# Electricity pack by VerdiX

A feature-complete reimplementation of the 1.3-1.4 electricity system, with a few extras!

## Parts

* 2-, 4-, and 6-wide batteries
* Small, medium and big RTGs
* Small, big and double solar panels
* Small and large wheels
* Ion Engine
* Electric RCS Thruster (unreleased; separate from stock RCS)

## Unreleased changes in this branch

* Electric Ion Engine: **thrust 7.25**, **efficiency (ISP) 1800**.
* Ion-engine Power consumption is kept at the original engine's nominal rate
  at the same throttle, difficulty, and orientation/scale. Its Power mixture
  coefficient is adjusted to `8.275862` to compensate for the new thrust/ISP.
  It still needs Liquid Fuel; its nominal fuel consumption is about **4.83×**
  the original rate.
* Added a separate **Electric RCS Thruster** in the **Electricity** category.
  It uses **Power + stock Liquid Fuel**, with the same mixture as the revised
  ion engine, while retaining stock RCS mass (`0.05`), thrust (`1.5`), ISP (`120`),
  nozzle layout, appearance, and controls. Stock RCS is not replaced or modified.
* Both RCS types use the normal craft-wide RCS switch. An electric RCS losing
  either required resource can switch RCS off for the craft; after replenishing,
  re-enable RCS normally. Power-only propulsion remains deferred.

See the [current implementation notes](SFS_MODDING_RESEARCH.md#16-second-modification-pass--retuned-ion-engine-and-mixed-resource-electric-rcs)
for the consumption calculation, source references, and validation limits.

These are source changes only: **no updated `.pack` has been built or tested in
SFS yet**. The upstream release link below does not contain these branch changes.
Build this source using the [Unity UI workflow](SFS_MODDING_RESEARCH.md#8-exact-pack-creation-method)
or the GitHub artifact workflow below. Source checks:
`python3 -m unittest discover -s tests -v`.

## Build a `.pack` GitHub artifact

The **Build SFS pack** Actions workflow provides:

* Automatic source/tooling checks on relevant pushes and pull requests.
* A **manual, protected Unity build** for Windows, macOS, Android, and iOS.
* Downloadable `.pack`, SHA-256 checksum, and build provenance, with diagnostic
  logs available separately. No custom DLL is embedded.

**One-time setup is required:** a self-hosted Windows runner labeled `sfs-unity`,
Unity **6000.1.17f1** with the four platform modules and a valid license, and the
pinned official toolkit with licensed Odin Inspector. See **[PACK_BUILD.md](docs/PACK_BUILD.md)**
for runner setup, the protected `sfs-pack-build` environment, and the repository
variable `SFS_UNITY_BUILDS_ENABLED=true`.

Once configured and the workflow is available on GitHub, use **Actions → Build
SFS pack → Run workflow** on the reviewed branch. Download
**Electricity-pack-<commit SHA>** from the successful run's Artifacts section,
extract it, and install **the `.pack` inside**, not GitHub's artifact ZIP.

The workflow has been added in source; it has **not** yet run a real Unity build.

## Installation

**Note:** On mobile platforms you need to buy the full bundle to install mods!

First, get the [latest version](https://github.com/VerdiX094/sfs-electricity/releases/latest) of the pack.
After that's done, move the `.pack` file you've downloaded into:

* Android: `Android/media/com.StefMorojna.SpaceflightSimulator/files/Mods/Custom_Assets/Parts`
* iOS: `Browse/On my iPhone/Spaceflight Simulator/files/Mods/Custom_Assets/Parts`
* Steam:
  1. Open the game, then from the main menu click on "Mod Loader"
  2. In the modloader menu, click on Open Mods Folder
  3. From there, navigate to `Custom_Assets/Parts` and paste the `.pack` file there.

## Troubleshooting

### The pack won't show up in the mod loader menu/build screen!
  Read the instructions again. This type of an issue is very often caused by pasting the pack in the wrong folder or trying to install it without the full bundle purchase (if on mobile).
  
  Sometimes the issue can be resolved by [verifying the game files integrity](https://help.steampowered.com/en/faqs/view/0C48-FCBD-DA71-93EB) (if on Steam) or reinstalling the game.

### I updated the pack and now it won't load/it still loads the old version!
  If you haven't deleted the old version, that might be the reason.
  If you have, try clearing the trash too - depending on your device, it might also be causing issues.
