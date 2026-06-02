#!/usr/bin/env python3
"""Lab 18-4: PCell file/cache persistence smoke test."""

import os
import sys
import traceback

from pcell_smoke_utils import (
    setup_library, param_array, create_design_with_block,
    define_supermaster, instantiate_pcell,
)


def main():
    print("=" * 60)
    print("Lab 18-4: PCellFile")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("Lib18_4_PcellFile", "../data/Lib18_4_PcellFile")
    top, block_top = create_design_with_block(sn_lib, ns, "top", "schematic", vt)
    ip, link, pcell_def, pc, block_pc, params = define_supermaster(
        sn_lib, ns, vt, "pcell", "si2pyPcellFile",
        param_array([("cacheKey", "A"), ("version", 1)]),
    )

    inst = instantiate_pcell(block_top, ns, pc, "i_cache", params)
    sub = inst.getMaster()
    assert sub.isSubMaster()
    pcell_def.addData(oa_str("cachePolicy"), oa_str("memory"))

    top.save()
    pc.save()
    print("  SuperMaster/SubMaster created and saved")
    print("✅ Lab 18-4 完成")
    os._exit(0)


from pcell_smoke_utils import oa_str

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
