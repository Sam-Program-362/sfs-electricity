"""Validate the official JSON/Base64 pack container, without loading game code.

Usage: python scripts/ci/validate_pack.py path/to/Electricity.pack
This is structural validation, not proof of platform/game compatibility.
"""

import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path
import struct


PLATFORMS = ("WindowsBuild", "MacBuild", "AndroidBuild", "IOS_Build")


def validate_bundle(payload):
    """Check UnityFS signature, bounded version strings, and declared file size."""
    if not payload.startswith(b"UnityFS\0") or len(payload) < 32:
        raise ValueError("Not a UnityFS AssetBundle")
    version = struct.unpack_from(">I", payload, 8)[0]
    if version not in (6, 7, 8):
        raise ValueError(f"Unexpected UnityFS format version: {version}")
    offset = 12
    for _ in range(2):  # Unity version and revision (NUL-terminated strings).
        end = payload.find(b"\0", offset, min(offset + 256, len(payload)))
        if end == -1:
            raise ValueError("Invalid UnityFS version string")
        offset = end + 1
    if offset + 20 > len(payload):
        raise ValueError("Truncated UnityFS header")
    declared_size, compressed_info, raw_info, _flags = struct.unpack_from(">QIII", payload, offset)
    if declared_size != len(payload):
        raise ValueError("UnityFS file size does not match payload (truncated/corrupt bundle)")
    if compressed_info == 0 or raw_info == 0 or compressed_info > len(payload):
        raise ValueError("Invalid UnityFS block-info size")
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def validate_pack(path):
    path = Path(path)
    if path.suffix != ".pack":
        raise ValueError("Expected an actual .pack file, not .pack.meta or an artifact ZIP")
    pack = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    if not isinstance(pack, dict) or set(pack) != set(PLATFORMS) | {"CodeAssembly"}:
        raise ValueError("Unexpected pack schema; all four platform fields and CodeAssembly are required")
    if pack["CodeAssembly"] is not None:
        raise ValueError("This mobile asset-only pack must not embed a custom DLL")
    info = {}
    for platform in PLATFORMS:
        value = pack[platform]
        if not isinstance(value, str) or not value:
            raise ValueError(f"Missing/empty platform payload: {platform}")
        try:
            payload = base64.b64decode(value, validate=True)
            info[platform] = validate_bundle(payload)
        except (ValueError, binascii.Error, struct.error) as exc:
            raise ValueError(f"Invalid {platform}: {exc}") from exc
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_pack(args.pack), indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Pack validation failed: {exc}\n")
