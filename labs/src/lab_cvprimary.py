#!/usr/bin/env python3
"""cvprimary: primary DM file / cellView smoke test."""

import os
import sys
import traceback

from oapy._oa import _dm
from pcell_smoke_utils import setup_library, scalar, create_design_with_block


def main():
    print("=" * 60)
    print("Lab cvprimary")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("LibCVPrimary", "../data/LibCVPrimary")
    des, block = create_design_with_block(sn_lib, ns, "cell1", "schematic", vt)
    des.save()
    lib.getAccess(_dm.oaLibAccess(_dm.oaLibAccessEnum.oacReadLibAccess), 0)
    cv = _dm.oaCellView.find(lib, scalar(ns, "cell1"), scalar(ns, "schematic"))
    assert cv is not None
    primary = cv.getPrimary()
    assert primary is not None
    print(f"  Primary DM object: {primary}")
    print("✅ cvprimary 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
