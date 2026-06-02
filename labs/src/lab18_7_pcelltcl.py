#!/usr/bin/env python3
"""Lab 18-7: Tcl PCell compatibility smoke test."""

import os
import sys
import traceback

from pcell_smoke_utils import (
    setup_library, param_array, create_design_with_block,
    define_supermaster, instantiate_pcell, oa_str,
)


def main():
    print("=" * 60)
    print("Lab 18-7: PCell Tcl")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("Lib18_7_PcellTcl", "../data/Lib18_7_PcellTcl")
    top, block_top = create_design_with_block(sn_lib, ns, "top", "schematic", vt)
    ip, link, pcell_def, pc, _, params = define_supermaster(
        sn_lib, ns, vt, "tclCell", "si2tclPcell",
        param_array([("language", "tcl"), ("width", 4)]),
    )
    pcell_def.addData(oa_str("GeneratorLanguage"), oa_str("Tcl"))
    inst = instantiate_pcell(block_top, ns, pc, "i_tcl", params)
    assert inst.getMaster().isSubMaster()
    top.save()
    print("  Tcl generator metadata stored on PcellDef")
    print("✅ Lab 18-7 完成")
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
