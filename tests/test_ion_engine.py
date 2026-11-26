"""Source-only regression checks; no Unity or third-party packages required."""

import unittest

from prefab_helpers import (
    ROOT, ENGINE_GUID, FLOW_GUID, POWER_GUID, LIQUID_FUEL_GUID,
    component, component_id, composed_input, number, resource_flows,
    metered_rates, resource_masses,
)


class IonEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "Electricity/Parts/Ion Drive.prefab").read_text()
        cls.engine = component(cls.text, ENGINE_GUID)
        cls.flow = component(cls.text, FLOW_GUID)
        cls.flows = resource_flows(cls.flow)

    def test_requested_thrust_and_efficiency(self):
        self.assertEqual(composed_input(self.engine, "thrust"), 7.25)
        self.assertEqual(composed_input(self.engine, "ISP"), 1800)

    def test_two_resource_mixture_is_preserved(self):
        self.assertEqual(set(self.flows), {POWER_GUID, LIQUID_FUEL_GUID})
        self.assertAlmostEqual(number(self.flows[POWER_GUID], "flowPercent", 4), 240 / 29, places=6)
        self.assertEqual(number(self.flows[LIQUID_FUEL_GUID], "flowPercent", 4), 1)
        for guid, rate in ((POWER_GUID, 500), (LIQUID_FUEL_GUID, 5)):
            with self.subTest(resource=guid):
                source = self.flows[guid]
                self.assertIn("    sourceSearchMode: 0\n", source)
                self.assertIn("    flowType: 0\n", source)
                self.assertEqual(number(source, "localValue", 6), rate)

    def test_original_power_draw_is_preserved_at_matching_operating_points(self):
        masses = resource_masses()
        self.assertEqual(masses[POWER_GUID], 0)
        for throttle in (0, 0.1, 0.5, 1):
            for isp_multiplier in (0.5, 1, 2):
                for orientation_multiplier in (1, 2):
                    with self.subTest(throttle=throttle, difficulty=isp_multiplier, scale=orientation_multiplier):
                        factor = throttle * orientation_multiplier / isp_multiplier
                        mass_flow = 7.25 / 1800 * factor
                        rates = metered_rates(self.flows, mass_flow, masses)
                        original_power = 1.25 / 1500 * 40 * factor
                        # Tolerance accounts for serialized C# float mixture precision.
                        self.assertAlmostEqual(rates[POWER_GUID], original_power, delta=1e-7)
                        self.assertAlmostEqual(rates[LIQUID_FUEL_GUID], mass_flow)

    def test_engine_source_and_activation_remain_wired(self):
        self.assertIn(f"  source: {{fileID: {component_id(self.flow)}}}\n", self.engine)
        self.assertIn(f"      - m_Target: {{fileID: {component_id(self.engine)}}}\n", self.text)
        self.assertIn("        m_MethodName: ToggleEngine\n", self.text)


if __name__ == "__main__":
    unittest.main()
