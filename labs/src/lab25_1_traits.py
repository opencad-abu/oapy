#!/usr/bin/env python3
"""
oapy Lab 25-1: traits — Python Type Dispatch for InstTerm Types

功能: 使用 Python 类型分派实现 traits 类型分派模式，统一处理三种 InstTerm:
      oaInstTerm (Block domain), oaModInstTerm (Module domain),
      oaOccInstTerm (Occurrence domain)

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab25_1_traits.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, c_str
from oapy._oa import _design, _base, _dm


def _s(v):
    if isinstance(v, str):
        return v
    if hasattr(v, 'c_str'):
        return c_str(v)
    try:
        op = getattr(v, 'operator[]', None)
        if op:
            return ''.join(op(i) for i in range(v.getLength()))
    except:
        pass
    return str(v)


LIB = "LibTest25"
LIB_PATH = "../data/LibDir25_1"
CELL_INV = "Inverter"
CELL_TOP = "Top"
VIEW = "abstract"


def _sn(sn):
    if isinstance(sn, str): return sn
    s = make_oa_string(); sn.get(s); return c_str(s)


# ═══════════════════════════════════════════════════════════════════════════
# Traits-style dispatch functions
# ═══════════════════════════════════════════════════════════════════════════

def traits_get_num_pins(term):
    """Get number of pins — only Block domain Terms have getPins()."""
    if term is None:
        return 0
    try:
        pins = term.getPins(0)
        return pins.getCount()
    except:
        return 0


def traits_get_mod_inst_term(inst_term):
    """从 Block-domain InstTerm 获取对应的 ModInstTerm."""
    try:
        occ = inst_term.getOccInstTerm()
        if occ:
            return occ.getModInstTerm()
    except:
        pass
    return None


def traits_type_name(obj):
    """获取 InstTerm 的类型名称（OA 风格）"""
    if obj is None:
        return "NULL"
    try:
        return obj.getType().getName()
    except:
        return type(obj).__name__


def traits_get_container_name(inst_term):
    """获取 InstTerm 容器的类型名（Block/Module/Occurrence）"""
    try:
        ot = _s(inst_term.getType().getName())
        if "Occ" in ot:
            return "Occurrence"
        elif "ModInstTerm" in ot:
            return "Module"
        elif "InstTerm" in ot:
            return "Block"
        return "Unknown"
    except:
        return "Unknown"


def get_master_info(it, term_names=None):
    """打印任意 InstTerm 的 Master 信息（traits 分派）"""
    if it is None:
        return

    container_type = traits_get_container_name(it)
    term = None

    try:
        ot = _s(it.getType().getName())
    except:
        ot = ""

    if "OccInstTerm" in ot:
        try:
            occ_term = it.getTerm(False)
            if occ_term:
                try:
                    term = occ_term.getTerm()
                except:
                    term = None
        except:
            term = None
    else:
        try:
            term = it.getTerm()
        except:
            term = None

    # 获取 Term 类型名
    if "OccInstTerm" in ot:
        term_type_name = "OccTerm"
    else:
        term_type_name = traits_type_name(term) if term else "UNBINDABLE"

    # Pin 数量（不同 Domain 行为不同）
    num_pins = traits_get_num_pins(term) if term else 0

    # Term 名称
    if "OccInstTerm" in ot:
        try:
            t_name = it.getTermName(get_namespace("native"))
        except:
            t_name = "UNBINDABLE"
    elif term:
        try:
            ns = get_namespace("native")
            t_name = term.getName(ns)
            if not isinstance(t_name, str):
                t_name = _sn(t_name)
        except:
            t_name = str(term_names.get(int(term.__hash__()), "?")) if term_names else "?"
    else:
        t_name = "UNBINDABLE"

    print(f"  {_s(term_type_name):20s} {_s(container_type):14s} {int(num_pins):5d}   {_s(t_name)}")


def main():
    print("=" * 60)
    print("oapy Lab 25-1: Traits Pattern (Python Type Dispatch)")
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
    print(f"\n  Created Lib '{LIB}'")

    ST = _design.oaSigTypeEnum; BV = _design.oaBlockDomainVisibilityEnum
    sig = _design.oaSigType(ST.oacSignalSigType)
    vis = _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock)

    vt = _dm.oaViewType.find(make_oa_string("netlist"))

    # ── Create Inverter Design ──
    sn_inv = make_oa_name(ns, CELL_INV)
    sn_top = make_oa_name(ns, CELL_TOP)
    sn_view = make_oa_name(ns, VIEW)

    des_inv = _design.oaDesign.open(sn_lib, sn_inv, sn_view, vt, 'w')
    des_top = _design.oaDesign.open(sn_lib, sn_top, sn_view, vt, 'w')
    block_inv = _design.oaBlock.create(des_inv, True)
    block_top = _design.oaBlock.create(des_top, True)
    print(f"  Created Blocks for {CELL_INV} and {CELL_TOP}")

    # ── Create Nets, Terms, Pins in Inverter ──
    net_i = _design.oaScalarNet.create(block_inv, make_oa_name(ns, "netIn"), sig, 1, vis)
    net_o = _design.oaScalarNet.create(block_inv, make_oa_name(ns, "netOut"), sig, 1, vis)

    term_i = _design.oaScalarTerm.create(net_i, make_oa_name(ns, "TermIn"))
    term_o = _design.oaScalarTerm.create(net_o, make_oa_name(ns, "TermOut"))

    # Create Pins (only Block domain terms have pins)
    _design.oaPin.create(term_i, 0)
    _design.oaPin.create(term_i, 1)
    _design.oaPin.create(term_o, 0)
    print(f"  Created 2 Pins on TermIn, 1 Pin on TermOut")

    # ── Instantiate Inverter in Top ──
    xform = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))
    inst_inv = _design.oaScalarInst.create(block_top, des_inv,
                                            make_oa_name(ns, "Inv1"),
                                            xform, _base.oaParamArray(0),
                                            vis,
                                            _design.oaPlacementStatus(_design.oaPlacementStatusEnum.oacUnplacedPlacementStatus))
    print(f"  Created Inst: Inv1")

    # ── Create InstTerms ──
    it_i = _design.oaInstTerm.create(None, inst_inv, term_i, vis)
    it_o = _design.oaInstTerm.create(None, inst_inv, term_o, vis)
    print(f"  Created InstTerms: it_i, it_o")

    # ── Get OccInstTerms ──
    oit_i = it_i.getOccInstTerm()
    oit_o = it_o.getOccInstTerm()
    print(f"  OccInstTerms: oit_i={oit_i is not None}, oit_o={oit_o is not None}")

    # ── Get ModInstTerms ──
    mit_i = traits_get_mod_inst_term(it_i)
    mit_o = traits_get_mod_inst_term(it_o)
    print(f"  ModInstTerms: mit_i={mit_i is not None}, mit_o={mit_o is not None}")

    # ── Print Master Info (traits dispatch) ──
    print(f"\n{'='*60}")
    print(f"OBJECT TYPE         CONTAINER       #PINS   TERM NAME")
    print(f"{'='*60}")

    term_names = {}
    for it in [it_i, mit_i, it_o, mit_o]:
        if it:
            get_master_info(it, term_names)

    # Also try OccInstTerms
    for oit in [oit_i, oit_o]:
        if oit:
            get_master_info(oit, term_names)

    print(f"{'='*60}")

    des_inv.save(); des_top.save()
    des_inv.close(); des_top.close()
    lib.close()

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    print(f"\n✅ oapy Lab 25-1 完成!")


if __name__ == "__main__":
    main()
