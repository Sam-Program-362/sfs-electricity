"""Patch the known upstream Electricity v1.0.1 binary without Unity/Odin.

Install scripts/requirements-pack-patch.txt, then run:
  python scripts/patch_ion_pack.py ORIGINAL.pack artifacts/pack/Electricity_ion_test.pack
This is an ion-only experimental patch, NOT a build of the repository prefabs.
"""

import argparse
import base64
import copy
import hashlib
import json
import math
import struct
from pathlib import Path
import tempfile

from ci.validate_pack import PLATFORMS, validate_pack

SOURCE_SHA256 = "cf164ff3f2ddab38222ec65bbecddccf490136e81d888136c4d2a53dced1883b"
UNITYPY_VERSION = "1.22.5"
POWER_COEFFICIENT = 8.275862


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_unitypy():
    import UnityPy
    require(UnityPy.__version__ == UNITYPY_VERSION,
            f"Install the pinned UnityPy=={UNITYPY_VERSION}")
    return UnityPy


def index_objects(env):
    # The known source has exactly one serialized asset file per platform.
    objects = list(env.objects)
    indexed = {obj.path_id: obj for obj in objects}
    require(len(indexed) == len(objects), "Ambiguous object IDs across asset files")
    return indexed


def container_refs(env):
    return {name: (obj.assetsfile.name, obj.file_id, obj.path_id)
            for name, obj in env.container.items()}


def patch_bundle(payload):
    unity = load_unitypy()
    env = unity.load(payload)
    objects = index_objects(env)
    before = {key: obj.get_raw_data() for key, obj in objects.items()}
    trees = {key: obj.read_typetree() for key, obj in objects.items()}
    scripts = {key: tree["m_ClassName"] for key, tree in trees.items()
               if objects[key].type.name == "MonoScript"}
    engines = [key for key, tree in trees.items()
               if objects[key].type.name == "MonoBehaviour"
               and scripts.get(tree.get("m_Script", {}).get("m_PathID")) == "EngineModule"]
    require(len(engines) == 1, "Expected exactly one engine")
    engine_id = engines[0]
    engine = copy.deepcopy(trees[engine_id])
    require(engine["thrust"]["input"] == "1.25" and engine["ISP"]["input"] == "1500",
            "Unexpected original engine settings")
    ion_paths = [name for name in env.container if name.endswith("/ion drive.prefab")]
    require(len(ion_paths) == 1 and
            env.container[ion_paths[0]].path_id == engine["m_GameObject"]["m_PathID"],
            "Engine is not attached to the ion prefab root")
    require(engine["source"]["m_FileID"] == 0, "External engine flow reference")
    flow_id = engine["source"]["m_PathID"]
    flow = copy.deepcopy(trees[flow_id])
    require(scripts.get(flow["m_Script"]["m_PathID"]) == "FlowModule",
            "Engine source is not a FlowModule")
    require(len(flow["sources"]) == 2, "Expected Power and Liquid Fuel")
    resources = {}
    for source in flow["sources"]:
        ref = source["resourceType"]
        require(ref["m_FileID"] == 0, "External resource reference")
        name = trees[ref["m_PathID"]]["m_Name"]
        require(name not in resources, "Duplicate engine resource")
        resources[name] = source
    require(set(resources) == {"Electricity_Resource", "Liquid_Fuel"},
            "Unexpected engine resource types")
    require(resources["Electricity_Resource"]["flowPercent"] == 40.0 and
            resources["Liquid_Fuel"]["flowPercent"] == 1.0,
            "Unexpected original mixture")
    engine["thrust"]["input"] = "7.25"
    engine["ISP"]["input"] = "1800"
    resources["Electricity_Resource"]["flowPercent"] = struct.unpack(
        "<f", struct.pack("<f", POWER_COEFFICIENT))[0]
    objects[engine_id].save_typetree(engine)
    objects[flow_id].save_typetree(flow)
    # Compare reloaded trees against the intended edits, with explicit float32 rounding.
    expected = {engine_id: engine, flow_id: flow}
    result = env.file.save(packer="lz4")
    check = unity.load(result)
    after = index_objects(check)
    require(set(after) == set(objects), "Object inventory changed")
    require(container_refs(check) == container_refs(env), "Asset container references changed")
    changed = {key for key in objects if before[key] != after[key].get_raw_data()}
    require(changed == {engine_id, flow_id}, "Unexpected object edits")
    for key in changed:
        require(after[key].read_typetree() == expected[key], "Changed fields did not survive save")
    checked_flow = after[flow_id].read_typetree()
    power = next(source for source in checked_flow["sources"]
                 if source["resourceType"] == resources["Electricity_Resource"]["resourceType"])
    old_draw = (1.25 / 1500) * 40
    new_draw = (7.25 / 1800) * power["flowPercent"]
    require(math.isclose(new_draw, old_draw, rel_tol=1e-6), "Power rate was not preserved")
    return result, {"objects": len(objects), "changed_objects": len(changed),
                    "engine_path_id": engine_id, "flow_path_id": flow_id,
                    "power_coefficient_float32": power["flowPercent"],
                    "power_rate_relative_error": new_draw / old_draw - 1,
                    "sha256": sha256(result), "bytes": len(result)}


def patch_pack(source, destination):
    source, destination = Path(source), Path(destination)
    require(source.resolve() != destination.resolve(), "Never overwrite the original pack")
    require(destination.suffix == ".pack", "Output must end in .pack")
    report_path = destination.with_suffix(".report.json")
    checksum_path = destination.with_suffix(".pack.sha256")
    require(not any(path.exists() for path in (destination, report_path, checksum_path)),
            "Output/report/checksum already exists; choose a new filename")
    raw = source.read_bytes()
    require(sha256(raw) == SOURCE_SHA256, "Source SHA-256 mismatch: use the unmodified v1.0.1 pack")
    validate_pack(source)
    pack = json.loads(raw)
    report = {"method": "UnityPy serialized-field patch (not Unity export)",
              "source_sha256": SOURCE_SHA256, "unitypy_version": UNITYPY_VERSION,
              "runtime_tested": False, "electric_rcs_included": False,
              "scope": "ion only: thrust 7.25, ISP 1800, original nominal Power draw; Liquid Fuel retained",
              "platforms": {}}
    for platform in PLATFORMS:
        result, info = patch_bundle(base64.b64decode(pack[platform], validate=True))
        pack[platform] = base64.b64encode(result).decode("ascii")
        report["platforms"][platform] = info
    output = json.dumps(pack, separators=(",", ":")).encode("utf-8")
    report["output_sha256"] = sha256(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".pack", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(output)
        validate_pack(temporary)
        # Exclusive creation also guards against concurrent output replacement.
        with destination.open("xb") as handle:
            handle.write(temporary.read_bytes())
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    checksum_path.write_text(f"{report['output_sha256']}  {destination.name}\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        report = patch_pack(args.source, args.destination)
    except (ValueError, OSError, ImportError) as exc:
        parser.exit(1, f"Patch failed: {exc}\n")
    print(json.dumps(report, indent=2))
    print("EXPERIMENTAL ION-ONLY PACK: phone test required; separate electric RCS not included.")


if __name__ == "__main__":
    main()
