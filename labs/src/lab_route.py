#!/usr/bin/env python3
"""route: oaRoute object smoke test."""

import os
import sys
import traceback

from oapy._oa import _base, _design
from pcell_smoke_utils import setup_library, scalar, create_design_with_block, block_visibility


def main():
    print("=" * 60)
    print("Lab route")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("LibRoute", "../data/LibRoute", "maskLayout")
    des, block = create_design_with_block(sn_lib, ns, "top", "layout", vt)
    net = _design.oaScalarNet.create(
        block, scalar(ns, "routeNet"),
        _design.oaSigType(_design.oaSigTypeEnum.oacSignalSigType), 1,
        block_visibility(),
    )
    route = _design.oaRoute.create(block, net)
    _design.oaRect.create(block, 101, 0, _base.oaBox(0, 0, 20, 2))
    route.setGlobal(True)
    route.setRouteStatus(_design.oaRouteStatus(_design.oaRouteStatusEnum.oacFixedRouteStatus))
    assert route.isGlobal()
    assert route.getNumObjects() == 0
    des.save()
    print("  Created oaRoute and updated route status/global flag")
    print("✅ route 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
