#!/usr/bin/env python3
"""
oapy Lab 16-5: Symbol — 创建 schematic symbol CellViews

功能:
  为 And, Or, Xor, HalfAdder, FullAdder 创建 symbol 视图
  (用 oaRect, oaLine, oaArc, oaText 绘制符号图形)

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab16_5_symbol.py
"""

import os
import shutil
from utils import init_oa, get_namespace, create_lib, make_oa_string, make_oa_name, open_design
from oapy._oa import _design, _base, _dm, _tech


LIB_SYMBOL = "LibSymbol16"
VIEW_SYMBOL = "symbol"

# Layer / Purpose
LAYER_DEV = 230
LAYER_TEXT = 229
PURPOSE_DEV = 100   # drawing
PURPOSE_TEXT = 1013 # labels


def setup_layer_purpose(tech, layer_name, layer_num, purp_name, purp_num):
    """在 Tech 中创建/查找 Layer 和 Purpose"""
    purpose = _tech.oaPurpose.find(tech, make_oa_string(purp_name))
    if purpose:
        print(f"  Found Purpose: {purp_name} num={purp_num}")
    else:
        _tech.oaPurpose.create(tech, make_oa_string(purp_name), purp_num)
        print(f"  Created Purpose: {purp_name} num={purp_num}")

    layer = _tech.oaLayer.find(tech, make_oa_string(layer_name))
    if layer:
        print(f"  Found Layer: {layer_name} num={layer_num}")
    else:
        _tech.oaPhysicalLayer.create(tech, make_oa_string(layer_name), layer_num, _tech.oaMaterial(_tech.oaMaterialEnum.oacOtherMaterial), 0)
        print(f"  Created Layer: {layer_name} num={layer_num}")


def create_symbol_design(ns, cell_name):
    """创建一个空的 symbol 设计"""
    sn_lib = make_oa_name(ns, LIB_SYMBOL)
    sn_cell = make_oa_name(ns, cell_name)
    sn_view = make_oa_name(ns, VIEW_SYMBOL)
    vt = _dm.oaViewType.find(make_oa_string("netlist"))
    if not vt:
        vt = _dm.oaViewType.create(make_oa_string("netlist"))

    des = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
    assert des is not None, f"Cannot create symbol design: {LIB_SYMBOL}/{cell_name}/{VIEW_SYMBOL}"

    if des.getTopBlock() is None:
        _design.oaBlock.create(des, True)

    print(f"  Created symbol design: {cell_name}")
    return des


def make_label(block, label_position):
    """在指定位置创建 cell name 标签"""
    des = block.getDesign()
    cell_name = des.getCellName()
    
    # Convert oaScalarName to oaString
    ns = get_namespace('native')
    cell_str = make_oa_string('')
    cell_name.get(ns, cell_str)
    
    font = _design.oaFont(_design.oaFontEnum.oacFixedFont)
    align = _design.oaTextAlign(_design.oaTextAlignEnum.oacLowerLeftTextAlign)
    orient = _base.oaOrient(_base.oaOrientEnum.oacR0)
    
    _design.oaText.create(block, LAYER_TEXT, PURPOSE_TEXT,
                         cell_str, label_position,
                         align, orient, font, 4, 0, 1, 1)
    print(f"  Created label = {cell_str}")
    return cell_str


def save_close_design(des):
    """保存并关闭 design"""
    cell_name = des.getCellName()
    lib_name = des.getLibName()
    print(f'  Saving "{cell_name}" in symbol library named "{lib_name}"')
    des.save()
    des.close()


def make_and_symbol(ns):
    """创建 AND 符号

         0,24              16,24
            .---------------+
            |                    +
            |                       +
            |                         +
            |                          +
            |                           +
            |                           o <--- 28,12
            |                          +
            |                         +
            |                       +
            |                    +
            .---------------+
          0,0              16,0
    """
    print("\n=== MakeAndSymbol ===")
    des = create_symbol_design(ns, "And")
    block = des.getTopBlock()

    # 左半边：三边开口的框（oaLine）
    array = _base.oaPointArray(4)
    array.set(0, _base.oaPoint(16, 0))
    array.set(1, _base.oaPoint(0, 0))
    array.set(2, _base.oaPoint(0, 24))
    array.set(3, _base.oaPoint(16, 24))
    array.setNumElements(4)
    _design.oaLine.create(block, LAYER_DEV, PURPOSE_DEV, array)

    # 右半边：圆弧 (半椭圆，从 -90° 到 +90°)
    bbox = _base.oaBox(4, 0, 28, 24)
    _design.oaArc.create(block, LAYER_DEV, PURPOSE_DEV, bbox, -1.571, 1.571)

    make_label(block, _base.oaPoint(2, 2))
    save_close_design(des)


def make_or_symbol(ns):
    """创建 OR 符号"""
    print("\n=== MakeOrSymbol ===")
    des = create_symbol_design(ns, "Or")
    block = des.getTopBlock()

    # 右圆弧
    arc_right = _design.oaArc.create(block, LAYER_DEV, PURPOSE_DEV,
                                       _base.oaBox(4, 0, 28, 24), -1.571, 1.571)

    # 复制左圆弧（向左平移 16）
    arc_right.copy(_base.oaTransform(-16, 0, _base.oaOrient(_base.oaOrientEnum.oacR0)))

    # 顶部连线
    pa1 = _base.oaPointArray(2)
    pa1.set(0, _base.oaPoint(0, 24))
    pa1.set(1, _base.oaPoint(16, 24))
    pa1.setNumElements(2)
    _design.oaLine.create(block, LAYER_DEV, PURPOSE_DEV, pa1)

    # 底部连线
    pa1.set(0, _base.oaPoint(0, 0))
    pa1.set(1, _base.oaPoint(16, 0))
    pa1.setNumElements(2)
    _design.oaLine.create(block, LAYER_DEV, PURPOSE_DEV, pa1)

    make_label(block, _base.oaPoint(2, 2))
    save_close_design(des)


def make_xor_symbol(ns):
    """创建 XOR 符号 — 类似 OR 但在左侧多一条弧线"""
    print("\n=== MakeXorSymbol ===")
    des = create_symbol_design(ns, "Xor")
    block = des.getTopBlock()

    # 右圆弧（中心 24,12）
    _design.oaArc.create(block, LAYER_DEV, PURPOSE_DEV,
                              _base.oaBox(10, 0, 34, 24), -1.571, 1.571)

    # 中圆弧（中心 18,12）
    _design.oaArc.create(block, LAYER_DEV, PURPOSE_DEV,
                              _base.oaBox(4, 0, 28, 24), -1.571, 1.571)

    # 左圆弧（中心 0,12）
    _design.oaArc.create(block, LAYER_DEV, PURPOSE_DEV,
                              _base.oaBox(-12, 0, 12, 24), -1.571, 1.571)

    # 顶部连线
    pa1 = _base.oaPointArray(2)
    pa1.set(0, _base.oaPoint(0, 24))
    pa1.set(1, _base.oaPoint(22, 24))
    pa1.setNumElements(2)
    _design.oaLine.create(block, LAYER_DEV, PURPOSE_DEV, pa1)

    # 底部连线
    pa2 = _base.oaPointArray(2)
    pa2.set(0, _base.oaPoint(0, 0))
    pa2.set(1, _base.oaPoint(22, 0))
    pa2.setNumElements(2)
    _design.oaLine.create(block, LAYER_DEV, PURPOSE_DEV, pa2)

    make_label(block, _base.oaPoint(2, 2))
    save_close_design(des)


def make_ha_symbol(ns):
    """创建 HalfAdder 符号（矩形 + 标签）"""
    print("\n=== MakeHaSymbol ===")
    des = create_symbol_design(ns, "HalfAdder")
    block = des.getTopBlock()

    # 矩形: (0,0) -> (64,50)
    _design.oaRect.create(block, LAYER_DEV, PURPOSE_DEV,
                               _base.oaBox(0, 0, 64, 50))

    make_label(block, _base.oaPoint(2, 25))
    save_close_design(des)


def make_fa_symbol(ns):
    """创建 FullAdder 符号（矩形 + 标签）"""
    print("\n=== MakeFaSymbol ===")
    des = create_symbol_design(ns, "FullAdder")
    block = des.getTopBlock()

    # 矩形: (3,3) -> (159,95)
    _design.oaRect.create(block, LAYER_DEV, PURPOSE_DEV,
                               _base.oaBox(3, 3, 159, 95))

    make_label(block, _base.oaPoint(2, 2))
    save_close_design(des)


def main():
    print("=" * 60)
    print("oapy Lab 16-5: Schematic Symbol Creation")
    print("=" * 60)

    init_oa()
    ns = get_namespace('cdba')

    # 清理旧的库目录
    lib_dir = './' + LIB_SYMBOL + '_dir'
    if os.path.exists(lib_dir):
        shutil.rmtree(lib_dir)

    # 创建符号库
    sn_symbol, lib_symbol = create_lib(LIB_SYMBOL, lib_dir)
    print(f"  Created lib: {LIB_SYMBOL}")

    # 创建 Tech
    tech = _tech.oaTech.create(lib_symbol)

    # 设置单位
    vt_netlist = _dm.oaViewType.find(make_oa_string("netlist"))
    if not vt_netlist:
        vt_netlist = _dm.oaViewType.create(make_oa_string("netlist"))
    tech.setUserUnits(vt_netlist, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacMicron))
    tech.setDBUPerUU(vt_netlist, 3000)

    # 创建 Layer 和 Purpose
    setup_layer_purpose(tech, "device", LAYER_DEV, "drawing", PURPOSE_DEV)
    setup_layer_purpose(tech, "text", LAYER_TEXT, "labels", PURPOSE_TEXT)

    tech.save()
    tech.close()

    # 创建符号
    print("\n--- Creating symbols ---")
    make_and_symbol(ns)
    make_or_symbol(ns)
    make_xor_symbol(ns)
    make_ha_symbol(ns)
    make_fa_symbol(ns)

    print("\n" + "=" * 60)
    print("✅ oapy Lab 16-5: All 5 symbols created successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
