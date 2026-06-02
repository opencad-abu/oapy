#!/usr/bin/env python3
"""
oapy Lab 16-6: Pins — 在 Symbol 上创建 Pin 图形

目标: 使用 saveAs 复制 symbol，为每个 cell 创建 Term/Pin/stub/文本

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab16_6_pins.py
"""

import os, shutil
from utils import init_oa, get_namespace, create_lib
from oapy._oa import _design, _base, _dm, _tech


# Layer/Purpose numbers
LAYER_DEV = 230
PURPOSE_DEV = 100       # drawing
LAYER_TEXT = 229
PURPOSE_TEXT = 1013     # labels
LAYER_PIN = 231
PURPOSE_PIN = 1014      # connections
PURPOSE_STUB = 1015     # stubs

# Pin access direction
oacRightPinAccessDir = 1
oacTopPinAccessDir = 2
oacBottomPinAccessDir = 4
oacLeftPinAccessDir = 8

LIB_SYMBOL = "LibSymbol16"
LIB_PINS = "LibPins16"
LIB_SYMBOL_DIR = "../data/LibSymbol16_dir"
LIB_PINS_DIR = "../data/LibPins16_dir"


def main():
    print("=" * 60)
    print("oapy Lab 16-6: Symbol Pin Creation")
    print("=" * 60)

    init_oa()

    ns = _base.oaNativeNS()
    vt = _dm.oaViewType.get(_dm.oaReservedViewType(
        _dm.oaReservedViewTypeEnum.oacSchematicSymbol))
    tt = _design.oaTermTypeEnum
    st = _design.oaSigTypeEnum
    sig_signal = _design.oaSigType(st.oacSignalSigType)

    # ── Step 0: Create LibSymbol16 (clean stale data first) ──
    print("\n--- Ensure LibSymbol16 ---")
    sn_sym = _base.oaScalarName(ns, LIB_SYMBOL)
    if os.path.exists(LIB_SYMBOL_DIR):
        shutil.rmtree(LIB_SYMBOL_DIR)
    os.makedirs(LIB_SYMBOL_DIR)

    # 直接创建新库
    lib_sym = _dm.oaLib.create(sn_sym, _base.oaString(LIB_SYMBOL_DIR),
                                _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
                                _base.oaString("oaDMFileSys"),
                                _dm.oaDMAttrArray(0))
    tech = _tech.oaTech.create(lib_sym)
    tech.setUserUnits(vt, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacMicron))
    tech.setDBUPerUU(vt, 3000)
    for (pname, pnum) in [("drawing", PURPOSE_DEV), ("labels", PURPOSE_TEXT)]:
        try:
            _tech.oaPurpose.create(tech, _base.oaString(pname), pnum)
        except Exception:
            pass  # purpose already exists
    for (lname, lnum) in [("device", LAYER_DEV), ("text", LAYER_TEXT)]:
        _tech.oaPhysicalLayer.create(tech, _base.oaString(lname), lnum, _tech.oaMaterial(_tech.oaMaterialEnum.oacOtherMaterial), 0)
    tech.save()
    tech.close()
    # Create minimal symbol designs
    for cell in ["And", "Or", "Xor", "HalfAdder", "FullAdder"]:
        des = _design.oaDesign.open(sn_sym, _base.oaScalarName(ns, cell),
                                     _base.oaScalarName(ns, "symbol"), vt, 'w')
        _design.oaBlock.create(des, True)
        des.save()
        des.close()
    print(f"  Created {LIB_SYMBOL}")

    # ── Create Pins library ──
    print("\n--- Create Pins Library ---")
    if os.path.exists(LIB_PINS_DIR):
        shutil.rmtree(LIB_PINS_DIR)
    sn_pins = _base.oaScalarName(ns, LIB_PINS)
    lib_pins = _dm.oaLib.create(sn_pins, _base.oaString(LIB_PINS_DIR),
                                 _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
                                 _base.oaString("oaDMFileSys"),
                                 _dm.oaDMAttrArray(0))
    print(f"  Created {LIB_PINS}")

    # Create Tech in pins lib
    tech = _tech.oaTech.create(lib_pins)
    tech.setUserUnits(vt, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacMicron))
    tech.setDBUPerUU(vt, 3000)
    for (pname, pnum) in [("drawing", PURPOSE_DEV), ("labels", PURPOSE_TEXT),
                            ("connections", PURPOSE_PIN), ("stubs", PURPOSE_STUB)]:
        try:
            _tech.oaPurpose.create(tech, _base.oaString(pname), pnum)
        except:
            pass
    for (lname, lnum) in [("device", LAYER_DEV), ("text", LAYER_TEXT),
                            ("pin", LAYER_PIN)]:
        try:
            _tech.oaPhysicalLayer.create(tech, _base.oaString(lname), lnum, _tech.oaMaterial(_tech.oaMaterialEnum.oacOtherMaterial), 0)
        except:
            pass
    tech.save()
    tech.close()

    # ── Helper: copy symbol view from source to pins lib ──
    def copy_symbol_view(cell_name):
        """Clone symbol view from LibSymbol16 to LibPins16"""
        sn_cell = _base.oaScalarName(ns, cell_name)
        sn_view = _base.oaScalarName(ns, "symbol")
        src = _design.oaDesign.open(sn_sym, sn_cell, sn_view, vt, 'r')
        # saveAs to pins lib
        _design.oaDesign.saveAs(src, sn_pins, sn_cell, sn_view)
        src.close()
        # Open in append mode
        dst = _design.oaDesign.open(sn_pins, sn_cell, sn_view, vt, 'a')
        return dst

    # ── Helper: create pin with stub, rect, term, and label ──
    def make_pin(block, x, y, term_name, stub_len, is_output=False):
        """Create a complete pin on the symbol"""
        bv = _design.oaBlockDomainVisibilityEnum
        bdv = _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock)

        # Create net + term in block domain
        net = _design.oaScalarNet.create(block, _base.oaScalarName(ns, term_name),
                                           sig_signal, 1, bdv)
        term_type = _design.oaTermType(tt.oacOutputTermType if is_output else tt.oacInputTermType)
        term = _design.oaScalarTerm.create(net, _base.oaScalarName(ns, term_name))
        term.setTermType(term_type)

        width_pin = 2
        length_pin = 3

        if is_output:
            # Output pin on right side
            pin_x = x + stub_len
            access_dir = oacTopPinAccessDir | oacBottomPinAccessDir | oacRightPinAccessDir
            if stub_len > 0:
                _design.oaRect.create(block, LAYER_PIN, PURPOSE_STUB,
                                             _base.oaBox(x, y, x + stub_len, y + 1))
        else:
            # Input pin on left side
            pin_x = x - stub_len - length_pin
            access_dir = oacTopPinAccessDir | oacBottomPinAccessDir | oacLeftPinAccessDir
            if stub_len > 0:
                _design.oaRect.create(block, LAYER_PIN, PURPOSE_STUB,
                                             _base.oaBox(x - stub_len, y, x, y + 1))

        # Pin rectangle
        _design.oaRect.create(block, LAYER_PIN, PURPOSE_PIN,
                                     _base.oaBox(pin_x, y - width_pin//2,
                                                  pin_x + length_pin, y + width_pin//2))

        # Create oaPin with access direction
        pin = _design.oaPin.create(term, access_dir)
        print(f"    Pin: {term_name} type={'output' if is_output else 'input'} accessDir={access_dir}")

        # Label
        label_x = pin_x - 5 if not is_output else pin_x + length_pin + 1
        label_y = y + width_pin//2 + 1
        font = _design.oaFont(_design.oaFontEnum.oacFixedFont)
        align = _design.oaTextAlign(_design.oaTextAlignEnum.oacLowerLeftTextAlign)
        orient = _base.oaOrient(_base.oaOrientEnum.oacR0)
        _design.oaText.create(block, LAYER_TEXT, PURPOSE_TEXT,
                                    _base.oaString(term_name),
                                    _base.oaPoint(label_x, label_y),
                                    align, orient, font, 3, 0, 1, 1)

    # ── Process each cell ──
    cells_pins = [
        ("And",     [("A", 0, 19, 9, False), ("B", 0, 5, 9, False), ("Y", 16, 12, 9, True)]),
        ("Or",      [("A", 10, 19, 9, False), ("B", 10, 5, 9, False), ("Y", 16, 12, 9, True)]),
        ("Xor",     [("A", 10, 19, 9, False), ("B", 10, 5, 9, False), ("Y", 22, 12, 9, True)]),
        ("HalfAdder", [("A", 0, 38, 5, False), ("B", 0, 12, 5, False),
                        ("C", 64, 38, 3, True), ("S", 64, 12, 3, True)]),
        ("FullAdder", [("A", 3, 83, 0, False), ("B", 3, 57, 0, False),
                        ("Ci", 144, 3, 0, False), ("Co", 144, 95, 0, True),
                        ("S", 159, 20, 0, True)]),
    ]

    for cell_name, pin_list in cells_pins:
        print(f"\n--- Processing {cell_name} ---")
        des = copy_symbol_view(cell_name)
        block = des.getTopBlock()
        for term_name, x, y, stub_len, is_output in pin_list:
            make_pin(block, x, y, term_name, stub_len, is_output)
        des.save()
        des.close()
        print(f"  ✅ {cell_name}: {len(pin_list)} pins")

    lib_sym.close() if hasattr(lib_sym, 'close') else None
    lib_pins.close()

    # Verify
    print(f"\n--- Pins Library Files ---")
    for root, dirs, files in os.walk(LIB_PINS_DIR):
        for f in sorted(files):
            print(f"  {root}/{f}")

    print(f"\n✅ oapy Lab 16-6 完成！")


if __name__ == "__main__":
    main()
