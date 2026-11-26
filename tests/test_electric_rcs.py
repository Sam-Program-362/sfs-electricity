"""Static checks of the independent stock-module-based electric RCS part."""

import re
import unittest

from prefab_helpers import (
    ROOT, RCS_GUID, ENGINE_GUID, PART_GUID, FLOW_GUID, POWER_GUID,
    LIQUID_FUEL_GUID, CATEGORY_GUID, component, component_id, composed_input,
    number, resource_flows, metered_rates, resource_masses,
)


class ElectricRcsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "Electricity/Parts/Electric RCS Thruster.prefab"
        cls.text = cls.path.read_text()
        cls.part = component(cls.text, PART_GUID)
        cls.rcs = component(cls.text, RCS_GUID)
        cls.flow = component(cls.text, FLOW_GUID)
        cls.flows = resource_flows(cls.flow)

    def test_unique_identity_and_bundle_membership(self):
        meta = self.path.with_suffix(".prefab.meta").read_text()
        guid = re.search(r"^guid: ([0-9a-f]{32})$", meta, re.M)[1]
        self.assertNotEqual(guid, "fc132a1f34e977b42846895ff3faeb46")  # Stock RCS
        self.assertIn("assetBundleName: n2o4s_electricity\n", meta)
        self.assertIn("  m_Name: Electric RCS Thruster\n", self.text)
        self.assertIn("    TranslatableName: Electric RCS Thruster\n    plainText: 1", self.part)
        self.assertIn(f"guid: {CATEGORY_GUID}, type: 2", self.part)
        # A separate RCS module, not an engine wired to the main throttle.
        self.assertNotIn(f"guid: {ENGINE_GUID}", self.text)

    def test_stock_rcs_stats_and_nozzles_are_retained(self):
        self.assertEqual(composed_input(self.part, "mass"), 0.05)
        self.assertEqual(number(self.rcs, "thrust"), 1.5)
        self.assertEqual(number(self.rcs, "ISP"), 120)
        self.assertEqual(number(self.rcs, "directionAngleThreshold"), 45)
        self.assertEqual(number(self.rcs, "torqueAngleThreshold"), 40)
        normals = re.findall(r"^  - thrustNormal: (.+)$", self.rcs, re.M)
        self.assertEqual(normals, ["{x: 0, y: 1}", "{x: -1, y: 0}", "{x: 0, y: -1}"])
        effects = re.findall(r"^    effect: \{fileID: (\d+)\}$", self.rcs, re.M)
        self.assertEqual(len(set(effects)), 3)
        for file_id in effects:
            self.assertIn(f"--- !u!114 &{file_id} stripped\n", self.text)
        self.assertEqual(self.text.count("  m_SourcePrefab:"), 3)

    def test_rcs_controls_and_flow_are_wired(self):
        self.assertIn(f"  source: {{fileID: {component_id(self.flow)}}}\n", self.rcs)
        self.assertIn(f"      - m_Target: {{fileID: {component_id(self.rcs)}}}\n", self.part)
        self.assertIn("        m_MethodName: ToggleRCS\n        m_Mode: 0\n", self.part)

    def test_power_and_fuel_use_the_ion_mixture_and_start_idle(self):
        self.assertEqual(set(self.flows), {POWER_GUID, LIQUID_FUEL_GUID})
        ion = (ROOT / "Electricity/Parts/Ion Drive.prefab").read_text()
        ion_flows = resource_flows(component(ion, FLOW_GUID))
        for guid, source in self.flows.items():
            with self.subTest(resource=guid):
                self.assertEqual(number(source, "flowPercent", 4), number(ion_flows[guid], "flowPercent", 4))
                self.assertIn("    sourceSearchMode: 0\n", source)
                self.assertIn("    flowType: 0\n", source)
                self.assertIn("      variableName: \n", source)
                self.assertEqual(number(source, "localValue", 6), 0)

    def test_mass_flow_metering_has_no_massless_fallback_or_idle_drain(self):
        # Arithmetic-level verification only, not a runtime depletion/control test.
        for firing_nozzles in range(4):
            mass_flow = number(self.rcs, "thrust") * firing_nozzles / number(self.rcs, "ISP")
            rates = metered_rates(self.flows, mass_flow, resource_masses())
            with self.subTest(firing_nozzles=firing_nozzles):
                self.assertAlmostEqual(rates[LIQUID_FUEL_GUID], mass_flow)
                self.assertAlmostEqual(rates[POWER_GUID], mass_flow * 240 / 29, delta=1e-7)
                if firing_nozzles == 0:
                    self.assertEqual(rates, {POWER_GUID: 0, LIQUID_FUEL_GUID: 0})


class PrefabIntegrityTests(unittest.TestCase):
    def test_asset_guids_are_unique(self):
        seen = {}
        for path in sorted((ROOT / "Electricity").rglob("*.meta")):
            guid = re.search(r"^guid: ([0-9a-f]{32})$", path.read_text(), re.M)[1]
            self.assertNotIn(guid, seen, f"Duplicate GUID in {path} and {seen.get(guid)}")
            seen[guid] = path

    def test_new_rcs_local_references_exist(self):
        text = (ROOT / "Electricity/Parts/Electric RCS Thruster.prefab").read_text()
        object_ids = re.findall(r"^--- !u!\d+ &(\d+)(?: stripped)?$", text, re.M)
        self.assertEqual(len(object_ids), len(set(object_ids)), "Duplicate local object IDs")
        for match in re.finditer(r"\{fileID: (-?\d+)([^}]*)\}", text, re.S):
            file_id, suffix = match.groups()
            if file_id != "0" and "guid:" not in suffix:
                self.assertIn(file_id, object_ids, f"Unresolved local fileID: {file_id}")


if __name__ == "__main__":
    unittest.main()
