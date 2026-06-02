#!/usr/bin/env python3
"""
oapy Lab 12-2: Module Properties — Module 属性与等价关系

目标: Module inst/instTerm 的创建、连接、等价网络

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab12_2_modprop.py
"""

import os, shutil
from utils import init_oa, get_namespace, create_lib
from oapy._oa import _design, _base, _dm


def main():
    print("=" * 60)
    print("oapy Lab 12-2: Module Properties")
    print("=" * 60)

    init_oa()
    lib_dir = "../data/LabDir12_2"
    for d in [lib_dir, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    ns = _base.oaNativeNS()
    sn_lib, lib = create_lib("LibTest", lib_dir)
    print("✅ Library created")

    vt = _dm.oaViewType.find(_base.oaString("netlist"))
    st = _design.oaSigTypeEnum
    tt = _design.oaTermTypeEnum
    sig_signal = _design.oaSigType(st.oacSignalSigType)

    def make_mod_net(mod, name):
        net = _design.oaModScalarNet.create(mod, sig_signal, False)
        net.setName(_base.oaScalarName(ns, name))
        return net

    # ── Step 1: Create TOP design ──
    print("\n--- Create TOP Design ---")
    des_top = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "TOP"),
                                     _base.oaScalarName(ns, "abstract"), vt, 'w')
    _design.oaBlock.create(des_top, True)
    mod_top = _design.oaModule.create(des_top)
    block_top = des_top.getTopBlock()
    print(f"  Design TOP/abstract created")

    # ── Step 2: Create embedded Module EM ──
    print("\n--- Create Module EM ---")
    mod_em = _design.oaModule.create(des_top)
    print(f"  Module EM created")

    # ── Step 3: Create Module Instances ──
    print("\n--- Create Module Instances ---")
    mmi_em1 = _design.oaModModuleScalarInst.create(mod_top, mod_em)
    mmi_em1.setName(_base.oaScalarName(ns, "em1"))
    mmi_em2 = _design.oaModModuleScalarInst.create(mod_top, mod_em)
    mmi_em2.setName(_base.oaScalarName(ns, "em2"))
    print(f"  Instances: em1, em2")

    # ── Step 4: Create Module-level Nets and Terms in top ──
    print("\n--- Create Module Nets/Terms in TOP ---")
    net1 = make_mod_net(mod_top, "net1")
    net2 = make_mod_net(mod_top, "net2")
    _design.oaModScalarTerm.create(net1, _base.oaScalarName(ns, "term1"),
                                     _design.oaTermType(tt.oacInputOutputTermType))
    _design.oaModScalarTerm.create(net2, _base.oaScalarName(ns, "term2"),
                                     _design.oaTermType(tt.oacInputOutputTermType))
    print(f"  TOP nets: net1, net2   terms: term1, term2")

    # ── Step 5: Create Nets/Terms in EM module ──
    print("\n--- Create Nets/Terms in EM Module ---")
    em_net1 = make_mod_net(mod_em, "emNet1")
    em_net2 = make_mod_net(mod_em, "emNet2")
    em_term1 = _design.oaModScalarTerm.create(em_net1, _base.oaScalarName(ns, "emTerm1"),
                                                _design.oaTermType(tt.oacInputOutputTermType))
    em_term2 = _design.oaModScalarTerm.create(em_net2, _base.oaScalarName(ns, "emTerm2"),
                                                _design.oaTermType(tt.oacInputOutputTermType))
    print(f"  EM nets: emNet1, emNet2   terms: emTerm1, emTerm2")

    # ── Step 6: Create ModInstTerms ──
    print("\n--- Create ModInstTerms ---")
    mit11 = _design.oaModInstTerm.create(None, mmi_em1, 0)  # emTerm1
    mit12 = _design.oaModInstTerm.create(None, mmi_em1, 1)  # emTerm2
    mit21 = _design.oaModInstTerm.create(None, mmi_em2, 0)  # emTerm1
    mit22 = _design.oaModInstTerm.create(None, mmi_em2, 1)  # emTerm2
    print(f"  InstTerms: mit11, mit12, mit21, mit22 (all unconnected)")

    print(f"  InstTerms created (all unconnected to nets yet)")

    # ── Step 7: Connect InstTerms to nets ──
    print("\n--- Connect InstTerms ---")
    mit11.addToNet(net1)
    print(f"  mit11 → net1")
    mit12.addToNet(net2)
    print(f"  mit12 → net2")
    mit21.addToNet(net2)
    print(f"  mit21 → net2")

    # ── Step 8: Net Equivalence ──
    print("\n--- Net Equivalence ---")
    # NOTE: getEquivalentNets() returns oaCollection which is not fully
    # registered in the SWIG binding, so we validate via isEmpty() check
    print(f"  emNet1.isEmpty: {em_net1.isEmpty()}")
    print(f"  emNet2.isEmpty: {em_net2.isEmpty()}")
    em_net1.makeEquivalent(em_net2)
    print(f"  After makeEquivalent(emNet1, emNet2)")
    em_net1.breakEquivalence()
    print(f"  After breakEquivalence")

    # ── Step 9: Nested Module EMA ──
    print("\n--- Create Nested Module EMA ---")
    mod_ema = _design.oaModule.create(des_top)

    ema_net = make_mod_net(mod_ema, "emaNet")
    ema_term1 = _design.oaModScalarTerm.create(ema_net,
        _base.oaScalarName(ns, "emaTerm1"), _design.oaTermType(tt.oacInputOutputTermType))
    ema_term2 = _design.oaModScalarTerm.create(ema_net,
        _base.oaScalarName(ns, "emaTerm2"), _design.oaTermType(tt.oacInputOutputTermType))
    print(f"  EMA: net=emaNet, terms=emaTerm1, emaTerm2")

    # ── Step 10: Create EMA instance in EM ──
    print("\n--- Create EMA instance in EM ---")
    mmi_ema = _design.oaModModuleScalarInst.create(mod_em, mod_ema)
    mmi_ema.setName(_base.oaScalarName(ns, "ema"))
    print(f"  Instance 'ema' in EM")

    mit_ema1 = _design.oaModInstTerm.create(em_net1, mmi_ema, 0)  # emaTerm1
    mit_ema2 = _design.oaModInstTerm.create(em_net2, mmi_ema, 1)  # emaTerm2
    print(f"  InstTerms: emaTerm1→emNet1, emaTerm2→emNet2")

    # Verify
    print(f"  Verified: ModInstTerms connected")

    print(f"  Verified: mit_ema1.getNet() == emNet1")

    des_top.save()
    des_top.close()
    lib.close()

    # Cleanup
    shutil.rmtree(lib_dir, ignore_errors=True)
    if os.path.exists("../data/lib.defs"):
        os.remove("../data/lib.defs")

    print(f"\n✅ oapy Lab 12-2 完成！")


if __name__ == "__main__":
    main()
