#!/usr/bin/env python3
"""flat2: hierarchy flattening with connection-aware placeholder smoke test."""

import os
import sys
import traceback

from oapy._oa import _design
from pcell_smoke_utils import (
    setup_library, scalar, create_design_with_block, param_array,
    r0_transform, block_visibility, placement_status,
)


def main():
    print("=" * 60)
    print("Lab flat2")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("LibFlat2", "../data/LibFlat2")
    top, block_top = create_design_with_block(sn_lib, ns, "top", "schematic", vt)
    leaf, block_leaf = create_design_with_block(sn_lib, ns, "leaf", "schematic", vt)
    _design.oaScalarNet.create(
        block_leaf, scalar(ns, "leafNet"),
        _design.oaSigType(_design.oaSigTypeEnum.oacSignalSigType), 1,
        block_visibility(),
    )
    inst = _design.oaScalarInst.create(
        block_top, leaf, scalar(ns, "u_leaf"), r0_transform(),
        param_array([]), block_visibility(), placement_status(),
    )
    assert inst.isValid()

    flat = _design.oaDesign.open(sn_lib, scalar(ns, "top"), scalar(ns, "flat2"), vt, "w")
    flat_block = _design.oaBlock.create(flat, True)
    _design.oaScalarInst.create(
        flat_block, leaf, scalar(ns, "u_leaf_flat"), r0_transform(),
        param_array([]), block_visibility(), placement_status(),
    )
    flat.save()
    print("  Created flat2 view with copied leaf instance")
    print("✅ flat2 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
