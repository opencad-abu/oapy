#!/usr/bin/env python3
"""
Lab 16-4: BBPlugin — 使用外部插件的 IText 自定义 BBox 计算器


功能:
  - 加载外部编译的 IText 插件 (si2bbplugin)
  - 创建 Text 和 TextDisplay 对象，触发插件的 BBox 计算回调
  - 修改高度/字体/内容，观察 BBox 变化
  - 调用 invalidate() 强制重新计算

运行: cd oapy && bash labs/run_lab.sh labs/lab16_4_bbplugin.py
"""
import os
import sys
import shutil
from oapy._oa import _base, _design, _dm, _tech
import utils

LAYER_TEXT = 5
PURPOSE_TEXT = 101

PLUGIN_DIR = "/workarea/ai/openclaw/oa22.61-cpplabs/16-4.bbplugin"
PLUGIN_CLASSID = "si2bbplugin"


def print_bbox(box, label=""):
    print(f"      {label}({box.left()},{box.bottom()})({box.right()},{box.top()})")


def process_text_or_textdisplay(shape, multiplier):
    """处理 Text 或 TextDisplay 对象"""
    # 第一次获取 BBox
    print("      Get bbox 1st time:")
    bBox = shape.getBBox()
    print_bbox(bBox)

    # 第二次获取（应该用缓存）
    print("      Get bbox 2nd time:")
    bBox = shape.getBBox()
    print_bbox(bBox)

    # 修改高度
    old_height = shape.getHeight()
    new_height = old_height * multiplier
    print(f"      Reset height: {old_height} -> {new_height}")
    shape.setHeight(new_height)
    bBox = shape.getBBox()
    print_bbox(bBox, "After height reset: ")

    # 修改字体
    font = shape.getFont()
    print(f"      Current font \"{font.getName()}\"")
    if shape.isTextDisplay():
        new_font = _design.oaFont(_design.oaFontEnum.oacMilSpecFont)
    else:
        new_font = _design.oaFont(_design.oaFontEnum.oacMathFont)
    print(f"      Reset to font \"{new_font.getName()}\"")
    shape.setFont(new_font)
    bBox = shape.getBBox()
    print_bbox(bBox, "After font reset: ")

    # 修改文本内容（仅 Text，TextDisplay 不能改）
    if not shape.isTextDisplay() and hasattr(shape, 'setText'):
        print("      Change contents: -> \"New contents change bbox!\"")
        shape.setText("New contents change bbox!")
        bBox = shape.getBBox()
        print_bbox(bBox, "After text change: ")


def get_bbox_from_shape(shape):
    """从 shape 获取 BBox，区分 Text / TextDisplay / 其他"""
    type_name_obj = shape.getType().getName()
    type_name = utils.c_str(type_name_obj)
    bBox = shape.getBBox()
    print(f"  {type_name}: ({bBox.left()},{bBox.bottom()})({bBox.right()},{bBox.top()})")


def print_shapes_in_block(block):
    """遍历 Block 中所有 Shape 并打印 BBox"""
    print("  Printing bbox of each Shape in the Block:")
    shapes = block.getShapes()
    it = _design.oaIter_oaShape(shapes)
    shape = it.getNext()
    while shape:
        get_bbox_from_shape(shape)
        shape = it.getNext()


def invalidate_bboxes(block):
    """使 Block 中所有文本 BBox 失效"""
    print("  Invalidating Text BBoxes:")
    itext = _design.oaTextLink.getIText()
    if itext:
        print(f"    IText plugin: {itext}")
        # 调用 ITextInvalidate 接口
        inv = _design.oaTextLink.getITextInvalidate()
        if inv:
            inv.invalidate(block)


def main():
    print("=" * 60)
    print("Lab 16-4: BBPlugin — 外部插件加载测试")
    print("=" * 60)

    # ── 1. 设置插件路径 ──
    print("\n── 1. 设置 OA_PLUGIN_PATH ──")
    os.environ['OA_PLUGIN_PATH'] = PLUGIN_DIR
    print(f"  OA_PLUGIN_PATH = {PLUGIN_DIR}")

    # ── 2. 初始化 OA ──
    print("\n── 2. 初始化 OA ──")
    utils.init_oa()

    # ── 3. 注册 IText 插件 ──
    print("\n── 3. 加载外部插件 ──")
    print(f"  Plugin ClassID: {PLUGIN_CLASSID}")
    _design.oaTextLink.setIText(_base.oaString(PLUGIN_CLASSID))
    print(f"  setIText(\"{PLUGIN_CLASSID}\") 完成")

    itext = _design.oaTextLink.getIText()
    print(f"  getIText() 返回: {itext}")
    if itext:
        name = _base.oaString("")
        itext.getName(name)
        print(f"  Plugin name: {name}")

    # ── 4. 创建库和设计 ──
    print("\n── 4. 创建库和设计 ──")
    ns = _base.oaNativeNS()
    lib_name = _base.oaScalarName(ns, "LibBBPlugin")
    lib_path = "../data/LibBBPlugin_dir"

    if os.path.exists(lib_path):
        shutil.rmtree(lib_path)
        print(f"  Cleaned up old directory: {lib_path}")

    lib = _dm.oaLib.create(lib_name, _base.oaString(lib_path),
                            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
                            _base.oaString("oaDMFileSys"),
                            _dm.oaDMAttrArray(0))
    print(f"  Created library: LibBBPlugin")

    cell_name = _base.oaScalarName(ns, "top")
    view_name = _base.oaScalarName(ns, "main")
    vt = _dm.oaViewType.find(_base.oaString("schematic"))
    if not vt:
        vt = _dm.oaViewType.create(_base.oaString("schematic"))

    des = _design.oaDesign.open(lib_name, cell_name, view_name, vt, 'w')
    block = _design.oaBlock.create(des, True)
    print(f"  Created design: top/main")

    # ── 5. 创建对象 ──
    print("\n── 5. 创建 Text / TextDisplay / Rect ──")

    print("  Creating Text:")
    text = _design.oaText.create(block, LAYER_TEXT, PURPOSE_TEXT,
                                   _base.oaString("contents of Text"),
                                   _base.oaPoint(100, 100),
                                   _design.oaTextAlign(_design.oaTextAlignEnum.oacLowerCenterTextAlign),
                                   _base.oaOrient(_base.oaOrientEnum.oacR90),
                                   _design.oaFont(_design.oaFontEnum.oacSwedishFont),
                                   10)
    print(f"    Text created at (100,100)")

    print("  Creating TextDisplay:")
    bv = _design.oaBlockDomainVisibilityEnum
    sig = _design.oaSigTypeEnum
    net1 = _design.oaScalarNet.create(block, _base.oaScalarName(ns, "net1"),
                                        _design.oaSigType(sig.oacSignalSigType), 1,
                                        _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock))
    td = _design.oaAttrDisplay.create(net1,
                                         _design.oaAttrType(_design.oaNetAttrTypeEnum.oacNameNetAttrType),
                                         9, 8,
                                         _base.oaPoint(1000, 0),
                                         _design.oaTextAlign(_design.oaTextAlignEnum.oacCenterCenterTextAlign),
                                         _base.oaOrient(_base.oaOrientEnum.oacR90),
                                         _design.oaFont(_design.oaFontEnum.oacStickFont),
                                         20,
                                         _design.oaTextDisplayFormat(_design.oaTextDisplayFormatEnum.oacNameValueTextDisplayFormat),
                                         0, 1, 1)
    print(f"    TextDisplay created at (1000,0)")

    print("  Creating Rect:")
    rect = _design.oaRect.create(block, 3, 4, _base.oaBox(-222, -222, 111, 111))
    print(f"    Rect created: (-222,-222) to (111,111)")

    print("\n  Invalidating all text BBoxes:")
    invalidate_bboxes(block)

    des.save()

    # ── 6. 遍历 Shape 并获取 BBox ──
    print("\n── 6. 遍历 Shape 获取 BBox（触发插件回调）──")
    print_shapes_in_block(block)

    # ── 7. 再次失效并重新遍历 ──
    print("\n── 7. 再次 invalidate 并重新获取 BBox ──")
    invalidate_bboxes(block)
    print_shapes_in_block(block)

    des.close()
    print("\n" + "=" * 60)
    print("Lab 16-4 完成！外部插件加载成功")
    print("=" * 60)


if __name__ == '__main__':
    main()
