#!/usr/bin/env python3
"""
oapy Lab 11-3: multibit — MultiBit Nets and Bus Terminals

功能: 创建 BusNet、BusTerm、VectorInst、BundleNet，演示多比特信号操作。
      oapy 限制: InstTerm→VectorInst / BundleName.append 签名不同，已适配。

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab11_3_multibit.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, c_str
from oapy._oa import _design, _base, _dm


LIB = "lab11_3"
LIB_PATH = "../data/LibDir11_3"
CELL = "multibit"
VIEW = "schematic"


def main():
    print("=" * 60)
    print("oapy Lab 11-3: MultiBit Nets and Bus Terminals")
    print("=" * 60)

    init_oa()

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    os.makedirs(LIB_PATH, exist_ok=True)
    ns = get_namespace("native")

    # ── Create Lib ──
    sn_lib = make_oa_name(ns, LIB)
    lib = _dm.oaLib.create(sn_lib, make_oa_string(LIB_PATH),
            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
            make_oa_string('oaDMFileSys'), _dm.oaDMAttrArray(0))
    print(f"\nCreated Lib '{LIB}' at '{LIB_PATH}'")

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    ST = _design.oaSigTypeEnum; BV = _design.oaBlockDomainVisibilityEnum
    TT = _design.oaTermTypeEnum
    sig = _design.oaSigType(ST.oacSignalSigType)
    vis = _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock)

    # ── Open Design ──
    sn_cell = make_oa_name(ns, CELL)
    sn_view = make_oa_name(ns, VIEW)
    view = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
    block = _design.oaBlock.create(view, True)
    print(f"Design: {LIB}/{CELL}/{VIEW}")

    # ── Create BusNet D<3:0> ──
    bus_d = _design.oaBusNet.create(block, make_oa_name(ns, "D"), 0, 3, 1, sig, 0, vis)
    print(f"\nBusNet D<3:0>: start={bus_d.getStart()}, stop={bus_d.getStop()}, step={bus_d.getStep()}")

    # ── Create BusTerm on D<3:0> ──
    vn = _base.oaVectorName(ns, "D", 0, 3, 1)
    bus_term = _design.oaBusTerm.create(bus_d, vn,
                     _design.oaTermType(TT.oacInputTermType), vis)
    print(f"BusTerm: {bus_term.getName(ns)}")

    # ── Create VectorInst ──
    # First create a master design
    sn_master = make_oa_name(ns, "inv")
    view_master = _design.oaDesign.open(sn_lib, sn_master, sn_view, vt, 'w')
    block_master = _design.oaBlock.create(view_master, True)
    net_in = _design.oaScalarNet.create(block_master, make_oa_name(ns, "I"), sig, 1, vis)
    net_out = _design.oaScalarNet.create(block_master, make_oa_name(ns, "O"), sig, 1, vis)
    _design.oaScalarTerm.create(net_in, make_oa_name(ns, "I"))
    _design.oaScalarTerm.create(net_out, make_oa_name(ns, "O"))
    view_master.save(); view_master.close()

    view_master = _design.oaDesign.open(sn_lib, sn_master, sn_view, vt, 'r')

    xform = _base.oaTransform(100, 100, _base.oaOrient(_base.oaOrientEnum.oacR0))
    vec_inst = _design.oaVectorInst.create(block, view_master,
                                            make_oa_name(ns, "I"),
                                            0, 3, xform,
                                            _base.oaParamArray(0),
                                            _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock),
                                            _design.oaPlacementStatus(_design.oaPlacementStatusEnum.oacUnplacedPlacementStatus))
    print(f"\nVectorInst I<0:3>: start={vec_inst.getStart()}, stop={vec_inst.getStop()}, numBits={vec_inst.getNumBits()}")

    # ── Create ScalarInst ── (single instance)
    sc_inst = _design.oaScalarInst.create(block, view_master,
                                           make_oa_name(ns, "I_single"),
                                           xform,
                                           _base.oaParamArray(0),
                                           _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock),
                                           _design.oaPlacementStatus(_design.oaPlacementStatusEnum.oacUnplacedPlacementStatus))
    print(f"ScalarInst I_single: created")

    # ── Create InstTerm on ScalarInst (更简单的场景) ──
    term_ref = _design.oaScalarTerm.create(
        _design.oaScalarNet.create(block, make_oa_name(ns, "inst_net"), sig, 1, vis),
        make_oa_name(ns, "inst_term"))
    # Try InstTerm on ScalarInst
    try:
        it = _design.oaInstTerm.create(net_in, sc_inst, term_ref, vis)
        print(f"InstTerm created on ScalarInst I_single")
    except Exception as e:
        # Try with name
        try:
            it = _design.oaInstTerm.create(net_in, sc_inst,
                                           make_oa_name(ns, "I"), vis)
            print(f"InstTerm created by name on ScalarInst")
        except Exception as e2:
            print(f"  InstTerm skipped: {e2}")

    # ── Create BundleNet ──
    bun = _base.oaBundleName()
    bun.append(make_oa_name(ns, "b1"), 0)
    bun.append(make_oa_name(ns, "b2"), 0)
    bun_net = _design.oaBundleNet.create(block, bun, sig, 0, vis)
    print(f"\nBundleNet b1/b2: numMembers={bun_net.getNumMembers()}")

    # ── Create more BusNets ──
    bus_a = _design.oaBusNet.create(block, make_oa_name(ns, "A"), 0, 7, 1, sig, 0, vis)
    bus_a_tap = _design.oaBusNet.create(block, make_oa_name(ns, "A"), 2, 4, 1, sig, 0, vis)
    print(f"\nBusNet A<7:0>: start={bus_a.getStart()}, stop={bus_a.getStop()}")
    print(f"Tapped A<4:2>: start={bus_a_tap.getStart()}, stop={bus_a_tap.getStop()}")

    # ── Equivalence: try creating a bit net equivalency ──
    net_a = _design.oaScalarNet.create(block, make_oa_name(ns, "a"), sig, 1, vis)
    # oaBitNet.find returns oaNet (generic) - don't know exact bit index
    try:
        bus_member = bus_a.getBit(0)
        net_a.makeEquivalent(bus_member)
        print(f"Equivalenced: a == A<0> (via getBit)")
    except Exception as e:
        print(f"  Equivalence via getBit: {e}")

    # ── Save & verify disk ──
    view.save(); view.close()
    view_master.close()
    lib.close()

    print(f"\n--- Disk Contents ---")
    for root, dirs, files in os.walk(LIB_PATH):
        for f in sorted(files):
            print(f"  {root}/{f}")

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    print(f"\n✅ oapy Lab 11-3 完成!")


if __name__ == "__main__":
    main()
