"""Small readers for the Unity YAML fields used by these source-only tests."""

from pathlib import Path
import re
import struct


ROOT = Path(__file__).resolve().parents[1]
ENGINE_GUID = "c8f9cfaf9b4647048b56580331f1c4ef"
RCS_GUID = "ce7e6b04cd6d32b40958291f2c5bd3b1"
PART_GUID = "a01d8382f787b844d84fe3e7463aba27"
FLOW_GUID = "f80098a90a69dcd45a1b26ae1e010609"
POWER_GUID = "04b436aa485ffa14cab70bc05a1ef5bf"
LIQUID_FUEL_GUID = "228bca42e456ecb4cb87cdd837fa81fe"
CATEGORY_GUID = "3c5e45a9d5d95524bb991a0d1dd6384b"


def component(text, script_guid):
    matches = [
        block
        for block in text.split("--- !u!")
        if re.search(r"m_Script:.*guid: " + script_guid + r"\b", block)
    ]
    if len(matches) != 1:
        raise AssertionError(f"Expected one component for {script_guid}")
    return matches[0]


def component_id(block):
    return re.match(r"114 &(\d+)\n", block)[1]


def composed_input(block, field):
    match = re.search(
        rf"^  {field}:\n    variables: .*\n    input: ([^\n]+)$", block, re.M
    )
    if match is None:
        raise AssertionError(f"Missing composed input: {field}")
    return float(match[1])


def number(block, field, indent=2):
    return float(re.search(rf"^{' ' * indent}{field}: ([^\n]+)$", block, re.M)[1])


def resource_flows(block):
    result = {}
    for source in block.split("  - resourceType:")[1:]:
        guid = re.search(r"guid: ([0-9a-f]{32})", source)[1]
        if guid in result:
            raise AssertionError(f"Duplicate resource: {guid}")
        result[guid] = source
    return result


def float32(value):
    # Flow.flowPercent is a C# float, not a double.
    return struct.unpack("<f", struct.pack("<f", value))[0]


def metered_rates(flows, mass_flow, resource_masses):
    """Mirror inspected FlowModule.SetMassFlow arithmetic, not the simulation.

    Source: SFS-Shared-Parts @ 5f3077c5387b5813cbe0d26da981f68c55d6125f.
    No claim is made here about Unity execution, depletion, or notifications.
    """
    fractions = {guid: float32(number(src, "flowPercent", 4)) for guid, src in flows.items()}
    mass_per_unit = sum(resource_masses[guid] * part for guid, part in fractions.items())
    total = mass_flow / mass_per_unit if mass_per_unit > 0 else 1
    return {guid: total * part for guid, part in fractions.items()}


def resource_masses():
    power = (ROOT / "Electricity/Scriptables/Electricity_Resource.asset").read_text()
    # Stock Liquid_Fuel.asset resourceMass = 1, verified in the pinned toolkit.
    return {POWER_GUID: number(power, "resourceMass"), LIQUID_FUEL_GUID: 1.0}
