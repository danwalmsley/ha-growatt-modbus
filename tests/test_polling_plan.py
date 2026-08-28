"""Regression tests for the profile polling groups."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def _load_registers_module():
    path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "growatt_modbus_lufi"
        / "registers.py"
    )
    spec = importlib.util.spec_from_file_location("growatt_registers", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


registers = _load_registers_module()


def _covered_addresses(blocks: list[tuple[int, int]]) -> set[int]:
    return {
        address
        for start, count in blocks
        for address in range(start, start + count)
    }


class PollingPlanTest(unittest.TestCase):
    """Verify the default and high-frequency read plans."""

    def test_fast_power_is_disabled_by_default(self) -> None:
        for profile in registers.PROFILES.values():
            plan = profile.polling_plan()
            self.assertEqual(plan[registers.GROUP_POWER][registers.REG_INPUT], [])

            live = _covered_addresses(
                plan[registers.GROUP_LIVE][registers.REG_INPUT]
            )
            self.assertTrue({1, 2, 1009, 1010, 1011, 1012} <= live)
            self.assertTrue({1021, 1022, 1029, 1030, 1037, 1038} <= live)

    def test_fast_power_uses_two_narrow_blocks(self) -> None:
        for profile in registers.PROFILES.values():
            plan = profile.polling_plan(fast_power_enabled=True)
            blocks = plan[registers.GROUP_POWER][registers.REG_INPUT]
            self.assertEqual(blocks, [(1, 2), (1009, 30)])

            covered = _covered_addresses(blocks)
            self.assertTrue({1, 2, 1009, 1010, 1011, 1012} <= covered)
            self.assertTrue({1021, 1022, 1029, 1030, 1037, 1038} <= covered)
            self.assertTrue({0, 3, 93, 1040, 1067, 1086}.isdisjoint(covered))


if __name__ == "__main__":
    unittest.main()
