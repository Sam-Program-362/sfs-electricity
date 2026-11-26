"""Dependency-free guard tests plus opt-in tests against the original binary.

Set SFS_PATCH_SOURCE to an unmodified v1.0.1 .pack and install the optional
requirements to run the real four-platform integration test.
"""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("patch_ion_pack", ROOT / "scripts/patch_ion_pack.py")
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)


class PatchGuardTests(unittest.TestCase):
    def test_original_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.pack"
            source.write_bytes(b"original")
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                patcher.patch_pack(source, source)
            self.assertEqual(source.read_bytes(), b"original")

    def test_reject_unknown_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.pack"
            output = Path(directory) / "patched.pack"
            source.write_bytes(b"unknown content")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                patcher.patch_pack(source, output)
            self.assertFalse(output.exists())

    def test_reject_existing_output_or_sidecars(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.pack"
            source.write_bytes(b"original")
            output = Path(directory) / "patched.pack"
            for existing in (output, output.with_suffix(".report.json"),
                             output.with_suffix(".pack.sha256")):
                existing.write_bytes(b"keep")
                with self.assertRaisesRegex(ValueError, "already exists"):
                    patcher.patch_pack(source, output)
                self.assertEqual(existing.read_bytes(), b"keep")
                existing.unlink()

    def test_reject_non_pack_extension(self):
        with self.assertRaisesRegex(ValueError, "end in .pack"):
            patcher.patch_pack("original.pack", "output.zip")

    def test_pinned_source_and_tool_version(self):
        self.assertEqual(len(patcher.SOURCE_SHA256), 64)
        requirements = (ROOT / "scripts/requirements-pack-patch.txt").read_text()
        self.assertIn(f"UnityPy=={patcher.UNITYPY_VERSION}", requirements)


@unittest.skipUnless(os.environ.get("SFS_PATCH_SOURCE"), "SFS_PATCH_SOURCE not provided")
class RealPackIntegrationTests(unittest.TestCase):
    def test_all_platforms_patch_and_verify_without_changing_source(self):
        source = Path(os.environ["SFS_PATCH_SOURCE"])
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "ion_test.pack"
            report = patcher.patch_pack(source, output)
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse(report["runtime_tested"])
            self.assertFalse(report["electric_rcs_included"])
            self.assertEqual(report["output_sha256"], patcher.sha256(output.read_bytes()))
            self.assertEqual(set(report["platforms"]), set(patcher.PLATFORMS))
            for info in report["platforms"].values():
                self.assertEqual(info["objects"], 590)
                self.assertEqual(info["changed_objects"], 2)
                self.assertLess(abs(info["power_rate_relative_error"]), 1e-6)
            self.assertEqual(json.loads(output.with_suffix(".report.json").read_text()), report)
            self.assertTrue(output.with_suffix(".pack.sha256").read_text().startswith(report["output_sha256"]))
            self.assertIsNone(json.loads(output.read_text())["CodeAssembly"])
            with self.assertRaisesRegex(ValueError, "already exists"):
                patcher.patch_pack(source, output)


if __name__ == "__main__":
    unittest.main()
