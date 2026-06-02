#!/usr/bin/env python3
"""Lab 14-3: multiple PCell plugin/link smoke test."""

import os
import sys
import traceback

from oapy._oa import _design
from pcell_smoke_utils import (
    setup_library, scalar, param_array, create_design_with_block,
    define_supermaster, instantiate_pcell,
)


def main():
    print("=" * 60)
    print("Lab 14-3: MultiPlug")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("Lib14_3_MultiPlug", "../data/Lib14_3_MultiPlug")
    top, block_top = create_design_with_block(sn_lib, ns, "top", "schematic", vt)

    ip_a, link_a, def_a, pc_a, _, params_a = define_supermaster(
        sn_lib, ns, vt, "pcA", "si2multiA", param_array([("kind", "A"), ("size", 1)]))
    ip_b, link_b, def_b, pc_b, _, params_b = define_supermaster(
        sn_lib, ns, vt, "pcB", "si2multiB", param_array([("kind", "B"), ("size", 2)]))

    inst_a = instantiate_pcell(block_top, ns, pc_a, "iA", params_a, 0, 0)
    inst_b = instantiate_pcell(block_top, ns, pc_b, "iB", params_b, 20, 0)
    assert inst_a.isValid() and inst_b.isValid()
    inst_a.getMaster()
    inst_b.getMaster()

    top.save()
    print(f"  Registered links: {link_a}, {link_b}")
    print("✅ Lab 14-3 完成")
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
