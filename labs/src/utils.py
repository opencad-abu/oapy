#!/usr/bin/env python3
"""
oapy Lab 工具函数

提供 oapy API 的便捷包装，弥补 pybind11 绑定的 Python 化不足。

注意: 必须通过 run_lab.sh 启动以设置正确的 LD_PRELOAD 环境。
"""

import os
import sys

# 确保 oapy 在路径中
_oapy_build = os.path.join(os.path.dirname(__file__), '..', 'build')
_oapy_src = os.path.join(os.path.dirname(__file__), '..')
for _p in [_oapy_build, _oapy_src]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from oapy._oa import _base, _dm, _design, _tech, _wafer, _cms


# ═══════════════════════════════════════════════════════════════════════════
# 初始化
# ═══════════════════════════════════════════════════════════════════════════

def init_oa():
    """初始化 OpenAccess（所有 Lab 第一步）
    
    正确初始化顺序 (参考 py4oa SWIG designInit):
    1. oaBaseInitAppBuild("22.61.d003")
    2. oaDesignInit(apiMajorRev, apiMinorRev, dataModelRev)
    
    oaDesignInit 内部会初始化 Base + DM + Design 三层。
    """
    _base.oaBaseInitAppBuild('22.61.d003')
    _design.oaDesignInit(6, 651, 6)


# ═══════════════════════════════════════════════════════════════════════════
# oaString 工具
# ═══════════════════════════════════════════════════════════════════════════

def c_str(s):
    """将 oaString 转换为 Python str"""
    if isinstance(s, str):
        return s
    c_str_op = getattr(s, 'operator const oaChar *', None)
    if c_str_op:
        return c_str_op()
    return str(s)


def c_str2(name, ns):
    """将 oaScalarName 通过 namespace 转换为 Python str"""
    if isinstance(name, str):
        return name
    out = _base.oaString()
    name.get(ns, out)
    return c_str(out)


def str_char_at(s, idx):
    """获取 oaString 中索引 idx 处的字符"""
    op = getattr(s, 'operator[]')
    return op(idx)


def str_concat(s, other):
    """oaString 拼接 (operator+= 的 Python 包装)"""
    op = getattr(s, 'operator+=')
    op(str(other))
    return s


def str_substr(s, count):
    """oaString 子串 — 提取前 count 个字符"""
    out = make_oa_string()
    s.substr(out, count)
    return c_str(out)


def make_oa_string(s=None):
    """创建 oaString"""
    if s is None:
        return _base.oaString()
    return _base.oaString(str(s))


# ═══════════════════════════════════════════════════════════════════════════
# Name 工具
# ═══════════════════════════════════════════════════════════════════════════

def make_oa_name(ns, name_str):
    """用给定 namespace 创建 oaScalarName"""
    if isinstance(ns, str):
        ns = get_namespace(ns)
    return _base.oaScalarName(ns, str(name_str))


def get_namespace(name='native'):
    """获取 OA namespace 实例"""
    ns_map = {
        'native': _base.oaNativeNS,
        'cdba': _base.oaCdbaNS,
        'unix': _base.oaUnixNS,
        'win': _base.oaWinNS,
        'lef': _base.oaLefNS,
        'def': _base.oaDefNS,
        'verilog': _base.oaVerilogNS,
        'vhdl': _base.oaVhdlNS,
        'spice': _base.oaSpiceNS,
        'spef': _base.oaSpefNS,
        'spf': _base.oaSpfNS,
    }
    cls = ns_map.get(name, _base.oaNativeNS)
    return cls()


# ═══════════════════════════════════════════════════════════════════════════
# Library 工具
# ═══════════════════════════════════════════════════════════════════════════

def create_lib(lib_name, lib_path):
    """创建 OA Library
    
    Args:
        lib_name: 逻辑库名 (str)
        lib_path: 物理路径 (str, 相对或绝对)
    Returns:
        (sn_lib, lib) 元组
    """
    ns = get_namespace('native')
    sn_lib = make_oa_name(ns, lib_name)
    lib_mode = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
    
    # 确保目录存在
    os.makedirs(lib_path, exist_ok=True)
    
    # 使用 oaLib.create 直接创建 (内部处理 lib.defs)
    lib = _dm.oaLib.create(sn_lib, make_oa_string(lib_path))
    return sn_lib, lib


def open_lib(lib_name, lib_path):
    """打开已有 OA Library"""
    ns = get_namespace('native')
    sn_lib = make_oa_name(ns, lib_name)
    lib_mode = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
    lib = _dm.oaLib.open(sn_lib, make_oa_string(lib_path), make_oa_string(lib_path), lib_mode)
    return lib


# ═══════════════════════════════════════════════════════════════════════════
# Design 工具
# ═══════════════════════════════════════════════════════════════════════════

def open_design(cell_name, view_name, sn_lib, mode='w', view_type_str='schematic'):
    """打开/创建设计
    
    Args:
        cell_name: Cell 名 (str)
        view_name: View 名 (str)
        sn_lib: oaScalarName 库名
        mode: 'r'/'w'/'a'
        view_type_str: ViewType 字符串
    Returns:
        (view, view_type) 元组
    """
    ns = get_namespace('native')
    sn_cell = make_oa_name(ns, cell_name)
    sn_view = make_oa_name(ns, view_name)
    
    # 查找或创建 ViewType
    vt = _dm.oaViewType.find(make_oa_string(view_type_str))
    if vt is None:
        vt = _dm.oaViewType.create(make_oa_string(view_type_str))
    
    view = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, mode)
    return view, vt


def is_msg_3107(exc):
    text = str(exc)
    return "msgId=3107" in text or "already exists with viewType" in text


def open_design_stable(cell_name, view_name, sn_lib, mode='w', view_type_str='schematic'):
    """打开/创建设计，带最小化的 Python 侧 3107 规避。

    说明：
    - 保持 `oapy` 绑定层薄，不改 OA 原始 API 语义
    - 仅供 labs / smoke / Python 二次开发使用
    - 主要处理 `oaDesign.open(..., vt, 'w'/'a')` 偶发 `msgId=3107`
    """
    ns = get_namespace('native')
    sn_cell = make_oa_name(ns, cell_name)
    sn_view = make_oa_name(ns, view_name)

    vt = _dm.oaViewType.find(make_oa_string(view_type_str))
    if vt is None:
        vt = _dm.oaViewType.create(make_oa_string(view_type_str))

    try:
        return _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, mode), vt
    except Exception as exc:
        if mode == 'r' or not is_msg_3107(exc):
            raise

    existing = _design.oaDesign.find(sn_lib, sn_cell, sn_view)
    if existing is not None:
        try:
            existing.reopen(mode)
        except Exception:
            pass
        return existing, vt

    existing, _ = open_design(cell_name, view_name, sn_lib, 'r', view_type_str)
    try:
        existing.reopen(mode)
    except Exception:
        pass
    return existing, vt


# ═══════════════════════════════════════════════════════════════════════════
# Block / Net / Term 工具
# ═══════════════════════════════════════════════════════════════════════════

def create_block(view, visible_to_module=True):
    """创建 Block"""
    return _design.oaBlock.create(view, visible_to_module)


def create_net(block, name, sig_type=None, num_bits=1):
    """创建 ScalarNet
    
    Args:
        block: oaBlock
        name: net 名 (str)
        sig_type: 信号类型，默认自动推断
        num_bits: 位宽，默认 1
    """
    ns = get_namespace('native')
    sn = make_oa_name(ns, name)
    if sig_type is None:
        name_upper = name.upper()
        if name_upper in ('VDD', 'VCC', 'VPWR', 'PWR'):
            st = _design.oaSigTypeEnum.oacPowerSigType
        elif name_upper in ('VSS', 'GND', 'VGND'):
            st = _design.oaSigTypeEnum.oacGroundSigType
        else:
            st = _design.oaSigTypeEnum.oacSignalSigType
    else:
        st = sig_type
    return _design.oaScalarNet.create(block, sn, _design.oaSigType(st), num_bits, 
                                       _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock))


def create_term(net, name, term_type=None):
    """创建 ScalarTerm
    
    Args:
        net: oaScalarNet
        name: term 名 (str)
        term_type: 'input', 'output', 'inout', 'power', 'ground' 或 None
    """
    ns = get_namespace('native')
    term = _design.oaScalarTerm.create(net, make_oa_name(ns, name))
    if term_type:
        type_map = {
            'input': _design.oacInputTermType,
            'output': _design.oacOutputTermType,
            'inout': _design.oacInOutTermType,
            'power': _design.oacPowerTermType,
            'ground': _design.oacGroundTermType,
        }
        tt = type_map.get(term_type)
        if tt is not None:
            term.setTermType(_design.oaTermType(tt))
    return term


# ═══════════════════════════════════════════════════════════════════════════
# Shape 工具
# ═══════════════════════════════════════════════════════════════════════════

def create_rect(block, layer_num, purpose_num, x1, y1, x2, y2):
    """创建 oaRect"""
    bbox = _base.oaBox(x1, y1, x2, y2)
    return _design.oaRect.create(block, layer_num, purpose_num, bbox)
