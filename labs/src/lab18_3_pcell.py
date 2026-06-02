#!/usr/bin/env python3
"""Lab 18-3: PCell lifecycle smoke test."""

import os
import sys
import traceback

from pcell_smoke_utils import (
    setup_library, param_array, create_design_with_block,
    define_supermaster, instantiate_pcell,
)


def main():
    print("=" * 60)
    print("Lab 18-3: PCell")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("Lib18_3_Pcell", "../data/Lib18_3_Pcell")
    top, block_top = create_design_with_block(sn_lib, ns, "top", "schematic", vt)
    ip, link, pcell_def, pc, block_pc, params = define_supermaster(
        sn_lib, ns, vt, "pc", "si2pyPcell",
        param_array([("p0param", "NetParamName"), ("p1param", 595)]),
    )

    i1 = instantiate_pcell(block_top, ns, pc, "i1", params, 0, 0)
    i2_params = param_array([("p0param", "OtherNet"), ("p1param", 78)])
    i2 = instantiate_pcell(block_top, ns, pc, "i2", i2_params, 50, 0)
    assert i1.getMaster().isSubMaster()
    assert i2.getMaster().isSubMaster()
    assert ip.eval_count >= 2

    top.save()
    pc.save()
    print(f"  eval_count={ip.eval_count} bind_count={ip.bind_count}")
    print("✅ Lab 18-3 完成")
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
