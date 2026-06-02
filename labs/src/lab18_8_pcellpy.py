#!/usr/bin/env python3
"""Lab 18-8: Python PCell plugin smoke test."""

import os
import sys
import traceback

from pcell_smoke_utils import (
    setup_library, param_array, create_design_with_block,
    define_supermaster, instantiate_pcell, oa_str,
)


def main():
    print("=" * 60)
    print("Lab 18-8: PCell Python")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("Lib18_8_PcellPy", "../data/Lib18_8_PcellPy")
    top, block_top = create_design_with_block(sn_lib, ns, "top", "schematic", vt)
    ip, link, pcell_def, pc, _, params = define_supermaster(
        sn_lib, ns, vt, "pythonCell", "si2pythonPcell",
        param_array([("language", "python"), ("fingers", 2)]),
    )
    pcell_def.addData(oa_str("GeneratorLanguage"), oa_str("Python"))
    inst = instantiate_pcell(block_top, ns, pc, "i_py", params)
    assert inst.getMaster().isSubMaster()
    top.save()
    print(f"  Python IPcell eval_count={ip.eval_count}")
    print("✅ Lab 18-8 完成")
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
