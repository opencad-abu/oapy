#!/usr/bin/env python3
"""
oapy Lab 12-1: Module — 使用 Module Domain 创建层次化设计

目标: Module domain 层次化设计 (Module/ModNet/ModTerm/ModScalarInst/ModInstTerm)

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab12_1_module.py
"""

import os, shutil
from utils import init_oa, make_oa_string, get_namespace, create_lib
from oapy._oa import _design, _base, _dm


def main():
    print("=" * 60)
    print("oapy Lab 12-1: Module Hierarchy")
    print("=" * 60)

    init_oa()
    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    sn_lib, lib = create_lib("testLib", "../data/LibDir")
    print("✅ Library created")

    ns = _base.oaNativeNS()
    vt = _dm.oaViewType.find(_base.oaString("schematic"))
    st = _design.oaSigTypeEnum
    tt = _design.oaTermTypeEnum
    input_type = _design.oaTermType(tt.oacInputTermType)
    output_type = _design.oaTermType(tt.oacOutputTermType)
    sig_signal = _design.oaSigType(st.oacSignalSigType)

    def make_mod_net(mod, name):
        net = _design.oaModScalarNet.create(mod, sig_signal, False)
        net.setName(_base.oaScalarName(ns, name))
        return net

    def make_mod_term(net, name, ttype):
        return _design.oaModScalarTerm.create(net, _base.oaScalarName(ns, name), ttype)

    # ═══════════════════════════════════════════════════════════════════
    # Step 1: Leaf Cells (Xor, And, Or) — Block-domain designs
    # ═══════════════════════════════════════════════════════════════════
    print("\n--- Step 1: Leaf Cells ---")
    leaf_designs = {}
    for cname, tnames in [("Xor", ["A", "B", "Y"]),
                           ("And", ["A", "B", "Y"]),
                           ("Or",  ["A", "B", "Y"])]:
        view = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, cname),
                                      _base.oaScalarName(ns, "schematic"), vt, 'w')
        block = _design.oaBlock.create(view, True)
        for i, tname in enumerate(tnames):
            net = _design.oaScalarNet.create(block, _base.oaScalarName(ns, tname),
                sig_signal, 1, _design.oaBlockDomainVisibility(
                    _design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock))
            term = _design.oaScalarTerm.create(net, _base.oaScalarName(ns, tname))
            term.setTermType(output_type if i == len(tnames)-1 else input_type)
        view.save()
        view.close()
        leaf_designs[cname] = None
        print(f"  ✅ {cname}")

    # ═══════════════════════════════════════════════════════════════════
    # Step 2: HalfAdder — Module domain design
    # ═══════════════════════════════════════════════════════════════════
    print("\n--- Step 2: HalfAdder ---")
    des_ha = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "HalfAdder"),
                                     _base.oaScalarName(ns, "schematic"), vt, 'w')
    _design.oaBlock.create(des_ha, True)
    mod_ha = _design.oaModule.create(des_ha)

    # Module nets + terms
    netA = make_mod_net(mod_ha, "A")
    netB = make_mod_net(mod_ha, "B")
    netC = make_mod_net(mod_ha, "C")
    netS = make_mod_net(mod_ha, "S")
    make_mod_term(netA, "A", input_type)
    make_mod_term(netB, "B", input_type)
    make_mod_term(netC, "C", output_type)
    make_mod_term(netS, "S", output_type)

    # Open leaf designs in read mode and create ModScalarInsts
    des_xor = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "Xor"),
                                     _base.oaScalarName(ns, "schematic"), vt, 'r')
    des_and = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "And"),
                                     _base.oaScalarName(ns, "schematic"), vt, 'r')

    inst_xor = _design.oaModScalarInst.create(mod_ha, des_xor)
    inst_xor.setName(_base.oaScalarName(ns, "Xor1"))
    inst_and = _design.oaModScalarInst.create(mod_ha, des_and)
    inst_and.setName(_base.oaScalarName(ns, "And1"))

    # Connect: Xor1(A→netA, B→netB, Y→netS), And1(A→netA, B→netB, Y→netC)
    _design.oaModInstTerm.create(netA, inst_xor, 0)  # A
    _design.oaModInstTerm.create(netB, inst_xor, 1)  # B
    _design.oaModInstTerm.create(netS, inst_xor, 2)  # Y
    _design.oaModInstTerm.create(netA, inst_and, 0)  # A
    _design.oaModInstTerm.create(netB, inst_and, 1)  # B
    _design.oaModInstTerm.create(netC, inst_and, 2)  # Y

    des_xor.close(); des_and.close()
    des_ha.save(); des_ha.close()
    print("  ✅ HalfAdder: 4 nets + 4 terms + 2 insts + 6 instTerms")

    # ═══════════════════════════════════════════════════════════════════
    # Step 3: FullAdder — ModScalarInst connecting leaf cells
    # ═══════════════════════════════════════════════════════════════════
    print("\n--- Step 3: FullAdder ---")
    des_fa = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "FullAdder"),
                                     _base.oaScalarName(ns, "schematic"), vt, 'w')
    _design.oaBlock.create(des_fa, True)
    mod_fa = _design.oaModule.create(des_fa)

    # I/O nets with terms
    faA  = make_mod_net(mod_fa, "A");  make_mod_term(faA, "A", input_type)
    faB  = make_mod_net(mod_fa, "B");  make_mod_term(faB, "B", input_type)
    faCi = make_mod_net(mod_fa, "Ci"); make_mod_term(faCi, "Ci", input_type)
    faCo = make_mod_net(mod_fa, "Co"); make_mod_term(faCo, "Co", output_type)
    faS  = make_mod_net(mod_fa, "S");  make_mod_term(faS, "S", output_type)
    # Internal nets
    h1c = make_mod_net(mod_fa, "H1c")
    h1s = make_mod_net(mod_fa, "H1s")
    h2c = make_mod_net(mod_fa, "H2c")

    # Open leaf designs
    des_ha_r = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "HalfAdder"),
                                      _base.oaScalarName(ns, "schematic"), vt, 'r')
    des_or_r = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "Or"),
                                      _base.oaScalarName(ns, "schematic"), vt, 'r')

    inst_ha1 = _design.oaModScalarInst.create(mod_fa, des_ha_r)
    inst_ha1.setName(_base.oaScalarName(ns, "Ha1"))
    inst_ha2 = _design.oaModScalarInst.create(mod_fa, des_ha_r)
    inst_ha2.setName(_base.oaScalarName(ns, "Ha2"))
    inst_or1 = _design.oaModScalarInst.create(mod_fa, des_or_r)
    inst_or1.setName(_base.oaScalarName(ns, "Or1"))

    # Connect Ha1: A→faA, B→faB, C→h1c, S→h1s
    _design.oaModInstTerm.create(faA,  inst_ha1, 0)
    _design.oaModInstTerm.create(faB,  inst_ha1, 1)
    _design.oaModInstTerm.create(h1c,  inst_ha1, 2)
    _design.oaModInstTerm.create(h1s,  inst_ha1, 3)
    # Connect Ha2: A→h1s, B→faCi, C→h2c, S→faS
    _design.oaModInstTerm.create(h1s,  inst_ha2, 0)
    _design.oaModInstTerm.create(faCi, inst_ha2, 1)
    _design.oaModInstTerm.create(h2c,  inst_ha2, 2)
    _design.oaModInstTerm.create(faS,  inst_ha2, 3)
    # Connect Or1: A→h1c, B→h2c, Y→faCo
    _design.oaModInstTerm.create(h1c,  inst_or1, 0)
    _design.oaModInstTerm.create(h2c,  inst_or1, 1)
    _design.oaModInstTerm.create(faCo, inst_or1, 2)

    des_ha_r.close(); des_or_r.close()
    des_fa.save(); des_fa.close()
    print("  ✅ FullAdder: 8 nets + 5 terms + 3 insts + 11 instTerms")

    # ═══════════════════════════════════════════════════════════════════
    # Step 4: 3-bit Adder (top level)
    # ═══════════════════════════════════════════════════════════════════
    print("\n--- Step 4: 3-bit Adder ---")
    des_3b = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "Adder3bit"),
                                     _base.oaScalarName(ns, "schematic"), vt, 'w')
    _design.oaBlock.create(des_3b, True)
    mod_3b = _design.oaModule.create(des_3b)

    nets = {}
    for nname in ["A0", "B0", "S0", "A1", "B1", "S1", "A2", "B2", "S2", "Ci", "Co"]:
        net = make_mod_net(mod_3b, nname)
        ttype = output_type if nname.startswith("S") or nname == "Co" else input_type
        make_mod_term(net, nname, ttype)
        nets[nname] = net
    net_c01 = make_mod_net(mod_3b, "C01")
    net_c12 = make_mod_net(mod_3b, "C12")

    des_fa_r = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, "FullAdder"),
                                      _base.oaScalarName(ns, "schematic"), vt, 'r')
    ci_nets = {"Ci": nets["Ci"], "C01": net_c01, "C12": net_c12}
    co_nets = {"C01": net_c01, "C12": net_c12, "Co": nets["Co"]}
    for fa_name, a_net, b_net, ci_net, co_net, s_net in [
        ("Fa0", "A0", "B0", "Ci", "C01", "S0"),
        ("Fa1", "A1", "B1", "C01","C12","S1"),
        ("Fa2", "A2", "B2", "C12","Co", "S2"),
    ]:
        fa_inst = _design.oaModScalarInst.create(mod_3b, des_fa_r)
        fa_inst.setName(_base.oaScalarName(ns, fa_name))
        _design.oaModInstTerm.create(nets[a_net],  fa_inst, 0)  # A
        _design.oaModInstTerm.create(nets[b_net],  fa_inst, 1)  # B
        _design.oaModInstTerm.create(ci_nets[ci_net], fa_inst, 2)  # Ci
        _design.oaModInstTerm.create(co_nets[co_net], fa_inst, 3)  # Co
        _design.oaModInstTerm.create(nets[s_net],  fa_inst, 4)  # S

    des_fa_r.close()
    des_3b.save(); des_3b.close()
    lib.close()

    # ── Verify ──
    print(f"\n--- Output Files ---")
    for root, dirs, files in os.walk("../data/LibDir"):
        for f in sorted(files):
            print(f"  {root}/{f}")

    print(f"\n✅ oapy Lab 12-1 完成！")


if __name__ == "__main__":
    main()
