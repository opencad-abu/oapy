#!/usr/bin/env python3
"""
oapy Lab 16-2: Text — 创建不同字体/对齐/方向的文本对象

目标: 测试 oaFont::calcBBox vs oaText::create 的 bounding box
      (oaTextAlign 包装为 oaTextAlign 对象，不是枚举值)

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab16_2_text.py
"""

import os, shutil
from utils import init_oa, get_namespace, create_lib
from oapy._oa import _design, _base, _dm, _tech


def dump_box(box):
    """Format oaBox as string"""
    w = box.right() - box.left()
    h = box.top() - box.bottom()
    return f"({box.left():>5},{box.bottom():>5})({box.right():>5},{box.top():>5})  {w:>5} x {h:<5}"


def main():
    print("=" * 60)
    print("oapy Lab 16-2: Text")
    print("=" * 60)

    init_oa()
    lib_dir = "../data/LabDir16_2"
    for d in [lib_dir, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    ns = _base.oaNativeNS()
    sn_lib, lib = create_lib("lab16_2", lib_dir)
    print("✅ Library created")

    vt = _dm.oaViewType.find(_base.oaString("netlist"))
    if not vt:
        vt = _dm.oaViewType.create(_base.oaString("netlist"))

    # ── Create Tech ──
    print("\n--- Tech Setup ---")
    tech = _tech.oaTech.create(lib)
    tech.setUserUnits(vt, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacInch))
    tech.setDBUPerUU(vt, 72)  # 72 points per inch
    print(f"  DBUPerUU: {tech.getDBUPerUU(vt)}")

    test_string = "ij"
    layer_num, purpose_num, height = 5, 6, 100

    # Font enums
    fe = _design.oaFontEnum
    font_vals = [fe.oacGothicFont, fe.oacFixedFont, fe.oacRomanFont,
                 fe.oacStickFont, fe.oacSwedishFont]
    font_names = ["Gothic", "Fixed", "Roman", "Stick", "Swedish"]
    n_fonts = len(font_vals)

    # Align enums by index
    align_names = ["LowerLeft", "LowerCenter", "LowerRight",
                   "CenterLeft", "Center", "CenterRight",
                   "UpperLeft", "UpperCenter", "UpperRight"]
    n_aligns = 9

    # Orient names
    orient_names = ["R0", "R90", "R180", "R270", "MX", "MXR90", "MY", "MYR90"]
    orient_vals  = [
        _base.oaOrientEnum.oacR0, _base.oaOrientEnum.oacR90,
        _base.oaOrientEnum.oacR180, _base.oaOrientEnum.oacR270,
        _base.oaOrientEnum.oacMX, _base.oaOrientEnum.oacMXR90,
        _base.oaOrientEnum.oacMY, _base.oaOrientEnum.oacMYR90,
    ]

    print(f"\n  {'ORIENT':<12} {'BOUNDING BOX':<30} {'WIDTH x HT':<13}")
    print(f"  {'------':<12} {'------------':<30} {'----------':<13}")

    for font_idx in range(n_fonts):
        font_val = font_vals[font_idx]
        font = _design.oaFont(font_val)
        fname = font_names[font_idx]

        for align_idx in range(n_aligns):
            aname = align_names[align_idx]
            align_val = _design.oaTextAlignEnum(align_idx)
            align_obj = _design.oaTextAlign(align_val)

            # Open a new design for each font/align combo  
            cell_no_mirror = f"top_{fname}-{aname}"
            des = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, cell_no_mirror),
                                         _base.oaScalarName(ns, "netlist"), vt, 'w')
            block = _design.oaBlock.create(des, True)

            for orient_val, orient_name in zip(orient_vals, orient_names):
                orient_obj = _base.oaOrient(orient_val)
                contents = f"{test_string}{orient_name}"

                # Calculate bbox
                box_calc = font.calcBBox(_base.oaPoint(0, 0), _base.oaString(contents), height,
                             align_obj, orient_obj, 0)

                # Create text and get actual bbox
                try:
                    text_obj = _design.oaText.create(block, layer_num, purpose_num,
                                                       _base.oaString(contents),
                                                       _base.oaPoint(0, 0),
                                                       align_obj, orient_obj, font,
                                                       height, 0, 1, 1)
                    box_actual = text_obj.getBBox()
                    match = "✅" if (box_calc.left() == box_actual.left() and
                                    box_calc.bottom() == box_actual.bottom() and
                                    box_calc.right() == box_actual.right() and
                                    box_calc.top() == box_actual.top()) else "❌ MISMATCH"
                except Exception as e:
                    box_actual = box_calc
                    match = f"⚠️ {e}"

                print(f"  {orient_name:<12} {dump_box(box_calc)} {match}")

                # Test with overbar
                contents_ob = f"{test_string}{orient_name}"
                box_calc2 = font.calcBBox(_base.oaPoint(0, 0), _base.oaString(contents_ob), height,
                              align_obj, orient_obj, 1)
                try:
                    text_obj2 = _design.oaText.create(block, layer_num, purpose_num,
                                                        _base.oaString(contents_ob),
                                                        _base.oaPoint(0, 0),
                                                        align_obj, orient_obj, font,
                                                        height, 1, 1, 1)
                    box_actual2 = text_obj2.getBBox()
                    match2 = "✅" if (box_calc2.left() == box_actual2.left() and
                                     box_calc2.bottom() == box_actual2.bottom() and
                                     box_calc2.right() == box_actual2.right() and
                                     box_calc2.top() == box_actual2.top()) else "❌ MISMATCH"
                except Exception:
                    match2 = "⚠️"

                print(f"  {'':12} {dump_box(box_calc2)} {match2}  with OVERBAR")

            des.save()
            des.close()

    # ── Print Tech info ──
    print(f"\n  DBU/UU = {tech.getDBUPerUU(vt)}")

    tech.close()
    lib.close()
    shutil.rmtree(lib_dir, ignore_errors=True)
    if os.path.exists("../data/lib.defs"):
        os.remove("../data/lib.defs")

    print(f"\n✅ oapy Lab 16-2 完成！")


if __name__ == "__main__":
    main()
