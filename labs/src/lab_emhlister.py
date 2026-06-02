#!/usr/bin/env python3
"""emhlister: open-design hierarchy lister smoke test."""

import os
import sys
import traceback

from oapy._oa import _design
from pcell_smoke_utils import setup_library, scalar, create_design_with_block, instantiate_pcell, param_array


def main():
    print("=" * 60)
    print("Lab emhlister")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("LibEMHLister", "../data/LibEMHLister")
    top, block_top = create_design_with_block(sn_lib, ns, "top", "schematic", vt)
    child, block_child = create_design_with_block(sn_lib, ns, "child", "schematic", vt)
    inst = _design.oaScalarInst.create(
        block_top, child, scalar(ns, "u_child"),
        __import__("pcell_smoke_utils").r0_transform(),
        param_array([]),
        __import__("pcell_smoke_utils").block_visibility(),
        __import__("pcell_smoke_utils").placement_status(),
    )
    assert inst.isValid()
    designs = _design.oaDesign.getOpenDesigns()
    print(f"  Open design count={designs.getCount()}")
    assert designs.getCount() >= 2
    print("✅ emhlister 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
