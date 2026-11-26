"""Offline build-tool checks. Synthetic UnityFS headers are fixtures, NOT packs
for installation. Actual Unity execution/compilation is not tested here.
"""

import base64
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts/ci"))
import build_pack  # noqa: E402
import validate_pack  # noqa: E402


def synthetic_bundle():
    prefix = b"UnityFS\0" + struct.pack(">I", 8) + b"6000.1.17f1\0test-fixture\0"
    size = len(prefix) + 20 + 16
    return prefix + struct.pack(">QIII", size, 16, 16, 0) + bytes(16)


def container():
    encoded = base64.b64encode(synthetic_bundle()).decode("ascii")
    return {**dict.fromkeys(validate_pack.PLATFORMS, encoded), "CodeAssembly": None}


class PackValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.pack = self.root / "fixture.pack"

    def write(self, data):
        self.pack.write_text(json.dumps(data), encoding="utf-8")
        return self.pack

    def test_complete_container_has_four_payload_hashes(self):
        info = validate_pack.validate_pack(self.write(container()))
        self.assertEqual(set(info), set(validate_pack.PLATFORMS))
        for value in info.values():
            self.assertEqual(value["bytes"], len(synthetic_bundle()))
            self.assertEqual(len(value["sha256"]), 64)

    def test_missing_null_empty_bad_base64_or_nonbundle_payload_is_rejected(self):
        for platform in validate_pack.PLATFORMS:
            for value in (None, "", "!badbase64!", base64.b64encode(b"not a bundle").decode()):
                with self.subTest(platform=platform, value=value):
                    data = container()
                    data[platform] = value
                    with self.assertRaises(ValueError):
                        validate_pack.validate_pack(self.write(data))
        data = container()
        del data["IOS_Build"]
        with self.assertRaises(ValueError):
            validate_pack.validate_pack(self.write(data))

    def test_duplicate_fields_custom_code_and_wrong_extension_are_rejected(self):
        self.pack.write_text('{"WindowsBuild":"x","WindowsBuild":"y"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            validate_pack.validate_pack(self.pack)
        data = container()
        data["CodeAssembly"] = "dll-content"
        with self.assertRaises(ValueError):
            validate_pack.validate_pack(self.write(data))
        with self.assertRaises(ValueError):
            validate_pack.validate_pack(self.root / "fixture.pack.meta")

    def test_truncation_header_sizes_and_format_version_are_checked(self):
        bundle = synthetic_bundle()
        bad_version = bundle[:8] + struct.pack(">I", 123) + bundle[12:]
        for data in (bundle[:-1], bundle[:25], bad_version, b"UnityFS\0" + bytes(30)):
            with self.subTest(header=data[:16]):
                with self.assertRaises(ValueError):
                    validate_pack.validate_bundle(data)

    def test_wrapper_requires_all_real_payload_files_and_no_custom_code(self):
        bundles = {}
        for platform in validate_pack.PLATFORMS:
            path = self.root / platform
            path.write_bytes(synthetic_bundle())
            bundles[platform] = path
        build_pack.write_pack(bundles, self.pack)
        self.assertIsNone(json.loads(self.pack.read_text())["CodeAssembly"])
        self.assertFalse(self.pack.with_suffix(".pack.tmp").exists())
        with self.assertRaises(ValueError):
            build_pack.write_pack({"WindowsBuild": bundles["WindowsBuild"]}, self.pack)
        bundles["IOS_Build"].write_bytes(b"invalid")
        with self.assertRaises(ValueError):
            build_pack.write_pack(bundles, self.root / "invalid.pack")
        self.assertFalse((self.root / "invalid.pack").exists())


class BuildPreparationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.template = self.root / "template"
        for folder in ("Assets/Editor", "Packages", "ProjectSettings"):
            (self.template / folder).mkdir(parents=True)
        (self.template / "Assets/Editor/Builder.cs").write_text("// fixture", encoding="utf-8")
        (self.template / "ProjectSettings/ProjectVersion.txt").write_text(
            f"m_EditorVersion: {build_pack.UNITY_VERSION}\n", encoding="utf-8")
        for dll in ("Sirenix.OdinInspector.Attributes.dll", "Sirenix.OdinInspector.Editor.dll"):
            (self.template / "Assets" / dll).write_bytes(b"private-dependency-fixture")

    def test_unmanaged_directory_is_never_deleted(self):
        path = self.root / "valuable"
        path.mkdir()
        (path / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_pack.reset_generated_directory(path)
        self.assertTrue((path / "keep.txt").is_file())

    def test_managed_workspace_can_be_reset_without_stale_files(self):
        path = self.root / "generated"
        build_pack.reset_generated_directory(path)
        (path / "old.pack").write_text("stale", encoding="utf-8")
        build_pack.reset_generated_directory(path)
        self.assertFalse((path / "old.pack").exists())
        self.assertTrue((path / build_pack.MARKER).is_file())

    def test_prepare_copies_pack_metadata_and_editor_without_template_mutation(self):
        workspace = self.root / "work"
        build_pack.prepare_project(self.template, workspace)
        self.assertEqual(
            (workspace / "Assets/Resources/Electricity.meta").read_bytes(),
            (REPO / "Electricity.meta").read_bytes())
        self.assertTrue((workspace / "Assets/Editor/SfsElectricityCI/SfsPackBuild.cs").is_file())
        self.assertFalse((self.template / "Assets/Resources/Electricity").exists())
        self.assertFalse((workspace / ".git").exists())
        with self.assertRaises(ValueError):
            build_pack.prepare_project(self.template, self.template / "inside-template")

    def test_preflight_requires_pinned_clean_toolkit_and_private_odin(self):
        with patch.object(build_pack, "git", return_value=build_pack.TOOLKIT_REVISION), patch.object(
            build_pack.subprocess, "run", return_value=SimpleNamespace(returncode=0)
        ):
            build_pack.validate_template(self.template)
            (self.template / "Assets/Sirenix.OdinInspector.Editor.dll").unlink()
            with self.assertRaisesRegex(ValueError, "Odin"):
                build_pack.validate_template(self.template)
        with patch.object(build_pack, "git", return_value="wrong-revision"):
            with self.assertRaisesRegex(ValueError, "pinned"):
                build_pack.validate_template(self.template)

    def test_missing_runner_configuration_fails_before_unity(self):
        with patch.dict(os.environ, {"SFS_UNITY_EDITOR": "", "SFS_TOOLKIT_PROJECT": ""}):
            with self.assertRaisesRegex(ValueError, "SFS_UNITY_EDITOR"):
                build_pack.main()

    def test_mocked_end_to_end_and_failure_never_reuses_previous_pack(self):
        # Everything created here is under TemporaryDirectory and deleted after
        # the test. The fake editor only tests orchestration, not Unity builds.
        repo = self.root / "checkout"
        repo.mkdir()
        shutil.copytree(REPO / "Electricity", repo / "Electricity")
        shutil.copy2(REPO / "Electricity.meta", repo / "Electricity.meta")
        shutil.copytree(REPO / "build-tools", repo / "build-tools")
        unity = self.root / "Unity.exe"
        unity.write_bytes(b"fake-editor")
        calls = []

        def fake_unity(command, timeout):
            self.assertEqual(timeout, 2100)
            field = command[command.index("-sfsPlatform") + 1]
            calls.append(field)
            output = Path(command[command.index("-sfsBundleOutput") + 1])
            output.mkdir(parents=True)
            (output / build_pack.BUNDLE_NAME).write_bytes(synthetic_bundle())
            log = Path(command[command.index("-logFile") + 1])
            log.write_text(f"SFS_PACK_PLATFORM_OK {field}\n", encoding="utf-8")
            return SimpleNamespace(returncode=0)

        with patch.object(build_pack, "ROOT", repo), patch.object(build_pack, "validate_template"), patch.object(
            build_pack, "git", side_effect=lambda *args: "a" * 40 if args[0] == "rev-parse" else ""
        ), patch.dict(os.environ, {"SFS_UNITY_EDITOR": str(unity), "SFS_TOOLKIT_PROJECT": str(self.template)}), patch.object(
            build_pack.subprocess, "run", side_effect=fake_unity
        ):
            build_pack.main()
            self.assertEqual(calls, list(validate_pack.PLATFORMS))
            output = repo / "artifacts/pack"
            self.assertEqual(len(list(output.glob("*.pack"))), 1)
            self.assertTrue((output / "Electricity_aaaaaaaaaaaa.pack.sha256").is_file())
            info = json.loads((output / "build-info.json").read_text())
            self.assertEqual(info["source_commit"], "a" * 40)
            self.assertFalse(info["runtime_tested"])
            self.assertFalse(list(output.rglob("*.dll")))
            with patch.object(build_pack.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(RuntimeError):
                    build_pack.main()
            self.assertFalse(list(output.glob("*.pack")), "Failed rerun must not leave the last successful pack")


if __name__ == "__main__":
    unittest.main()
