#!/usr/bin/env python3
"""
oapy Lab 16-7: Schematic — 创建 HalfAdder 和 FullAdder 的 Schematic 视图

功能:
  - 创建 LibSchematic 库
  - 为每个 cell 创建 schematic 视图（从 LibPins16 的 symbol 视图复制或直接创建）
  - 创建实例并设置位置
  - 添加文本标签

依赖: Lab 16-6 (pins) 必须已运行，LibPins16 必须存在

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab16_7_schematic.py
"""

import os, shutil
from utils import init_oa, get_namespace
from oapy._oa import _design, _base, _dm, _tech


LAYER_TEXT = 229
PURPOSE_TEXT = 1013     # labels

LIB_PINS = "LibPins16"
LIB_SCHEMATIC = "LibSchematic"
LIB_PINS_DIR = "../data/LibPins16_dir"
LIB_SCHEMATIC_DIR = "../data/LibSchematic_dir"
VIEW_SYMBOL = "symbol"
VIEW_SCHEMATIC = "schematic"

# Instance configurations: (inst_name, master_cell, x, y)
INST_CONFIGS = {
    "HalfAdder": [
        ("And1", "And", 20, 26),
        ("Xor1", "Xor", 14, 0),
    ],
    "FullAdder": [
        ("Ha1", "HalfAdder", 11, 45),
        ("Ha2", "HalfAdder", 89, 8),
        ("Or1", "Or", 83, 64),
    ],
}


def reserved_view_type(kind):
    return _dm.oaViewType.get(_dm.oaReservedViewType(kind))


def open_design_with_viewtypes(lib_name, cell_name, view_name, mode, *view_types):
    last_exc = None
    seen = set()
    for vt in view_types:
        if vt is None:
            continue
        key = id(vt)
        if key in seen:
            continue
        seen.add(key)
        try:
            return _design.oaDesign.open(lib_name, cell_name, view_name, vt, mode)
        except Exception as exc:
            last_exc = exc
    try:
        return _design.oaDesign.open(lib_name, cell_name, view_name, mode)
    except Exception as exc:
        last_exc = exc
    if last_exc:
        raise last_exc
    raise RuntimeError("No viewType candidates supplied")


def setup_tech(ns, sn_lib_sch):
    """Setup Tech for schematic library."""
    vt_netlist = _dm.oaViewType.find(_base.oaString("netlist"))
    if not vt_netlist:
        vt_netlist = _dm.oaViewType.create(_base.oaString("netlist"))

    tech = _tech.oaTech.find(sn_lib_sch)
    if not tech:
        try:
            tech = _tech.oaTech.open(sn_lib_sch, 'a')
            print("  Opened existing tech for schematic lib")
        except:
            lib_sch = _dm.oaLib.find(sn_lib_sch)
            if lib_sch:
                tech = _tech.oaTech.create(lib_sch)
                print("  Created new tech for schematic lib")

    if tech:
        try:
            tech.setUserUnits(vt_netlist, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacMicron))
            tech.setDBUPerUU(vt_netlist, 3000)
        except:
            pass

        for layer_name, layer_num, purpose_name, purpose_num in [
            ("device", 230, "drawing", 100),
            ("text", LAYER_TEXT, "labels", PURPOSE_TEXT),
            ("pin", 231, "connections", 1014),
            ("pin", 231, "stubs", 1015),
        ]:
            try:
                _tech.oaPhysicalLayer.create(tech, _base.oaString(layer_name), layer_num)
            except:
                pass
            try:
                _design.oaPurpose.create(tech, _base.oaScalarName(ns, purpose_name), purpose_num)
            except:
                pass

        tech.save()
        tech.close()
        print("  Tech setup complete")


def copy_prev_view(ns, cell_name, vt_symbol, vt_schematic, vt_netlist, sn_lib_pins, sn_lib_sch):
    """
    Copy design from LibPins16 (symbol view) to LibSchematic (schematic view).
    Opens source, saves as new view, reopens in append mode.
    """
    sn_cell = _base.oaScalarName(ns, cell_name)
    sn_view_symbol = _base.oaScalarName(ns, VIEW_SYMBOL)
    sn_view_sch = _base.oaScalarName(ns, VIEW_SCHEMATIC)

    # Open the design from Pins lib in read mode
    des = open_design_with_viewtypes(sn_lib_pins, sn_cell, sn_view_symbol, 'r',
                                     vt_symbol, vt_netlist, vt_schematic)
    if not des:
        raise RuntimeError(f"Can't find {VIEW_SYMBOL} Design: {LIB_PINS}/{cell_name}/{VIEW_SYMBOL}")
    source_vt = des.getViewType()
    print(f"  Opened {LIB_PINS}/{cell_name}/{VIEW_SYMBOL}")

    # Save as schematic view in schematic lib
    _design.oaDesign.saveAs(des, sn_lib_sch, sn_cell, sn_view_sch)
    des.close()
    print(f"  Saved as {LIB_SCHEMATIC}/{cell_name}/{VIEW_SCHEMATIC}")

    # Reopen in APPEND mode
    des = open_design_with_viewtypes(sn_lib_sch, sn_cell, sn_view_sch, 'a',
                                     vt_schematic, source_vt, vt_netlist, vt_symbol)
    return des


def create_and_place_inst(ns, block, inst_name, master_cell, x, y, sn_lib_pins,
                          vt_symbol, vt_schematic, vt_netlist):
    """
    Create an instance with LibPins16 symbol as master, set position, add label.
    """
    # Open master design from LibPins16
    sn_master_cell = _base.oaScalarName(ns, master_cell)
    sn_view_symbol = _base.oaScalarName(ns, VIEW_SYMBOL)

    master = _design.oaDesign.find(sn_lib_pins, sn_master_cell, sn_view_symbol)
    if not master:
        master = open_design_with_viewtypes(sn_lib_pins, sn_master_cell, sn_view_symbol, 'r',
                                            vt_symbol, vt_netlist, vt_schematic)

    if not master:
        print(f"  ⚠️  Can't open master: {LIB_PINS}/{master_cell}/{VIEW_SYMBOL}")
        return None

    # Create transform with position
    xform = _base.oaTransform(_base.oaPoint(x, y), _base.oaOrient(_base.oaOrientEnum.oacR0))

    # Create scalar instance
    sn_inst = _base.oaScalarName(ns, inst_name)
    bv = _design.oaBlockDomainVisibilityEnum
    bdv = _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock)
    ps = _design.oaPlacementStatusEnum
    inst = _design.oaScalarInst.create(block, master, sn_inst, xform,
                                        _base.oaParamArray(0), bdv,
                                        _design.oaPlacementStatus(ps.oacUnplacedPlacementStatus))

    if inst:
        # Verify position
        pt = _base.oaPoint()
        inst.getOrigin(pt)
        print(f"    Created {inst_name} at ({pt.x()},{pt.y()})")

        # Add text label at location + (20, 10)
        label_pt = _base.oaPoint(x + 20, y + 10)
        font = _design.oaFont(_design.oaFontEnum.oacFixedFont)
        align = _design.oaTextAlign(_design.oaTextAlignEnum.oacLowerLeftTextAlign)
        orient = _base.oaOrient(_base.oaOrientEnum.oacR0)
        _design.oaText.create(block, LAYER_TEXT, PURPOSE_TEXT,
                             _base.oaString(inst_name),
                             label_pt,
                             align, orient, font, 2, 0, 1, 1)
        print(f"    Text label '{inst_name}' added")
        return inst
    else:
        print(f"  ⚠️  Failed to create instance {inst_name}")
        return None


def make_schematic(ns, cell_name, vt_symbol, vt_schematic, vt_netlist, sn_lib_pins, sn_lib_sch):
    """Create schematic for a cell (HalfAdder or FullAdder)"""
    print(f"\n{'='*60}")
    print(f"Creating {cell_name} schematic")
    print(f"{'='*60}")

    # Copy design from pins lib to schematic lib
    des = copy_prev_view(ns, cell_name, vt_symbol, vt_schematic, vt_netlist,
                         sn_lib_pins, sn_lib_sch)
    block = des.getTopBlock()

    # Create and place each instance
    configs = INST_CONFIGS[cell_name]
    for inst_name, master_cell, x, y in configs:
        print(f"  Instance: {inst_name} (master={master_cell}) at ({x},{y})")
        create_and_place_inst(ns, block, inst_name, master_cell, x, y, sn_lib_pins,
                              vt_symbol, vt_schematic, vt_netlist)

    print(f'  Save "{cell_name}" schematic Design')
    des.save()
    des.close()
    print(f"  ✅ {cell_name} schematic created!")


def main():
    print("=" * 60)
    print("oapy Lab 16-7: Schematic Creation")
    print("=" * 60)

    init_oa()

    ns = _base.oaNativeNS()
    vt_netlist = reserved_view_type(_dm.oaReservedViewTypeEnum.oacNetlist)
    vt_symbol = reserved_view_type(_dm.oaReservedViewTypeEnum.oacSchematicSymbol)
    vt_schematic = reserved_view_type(_dm.oaReservedViewTypeEnum.oacSchematic)

    sn_lib_pins = _base.oaScalarName(ns, LIB_PINS)
    sn_lib_sch = _base.oaScalarName(ns, LIB_SCHEMATIC)

    # ── Ensure LibPins16 exists ──
    print("\n--- Ensure LibPins16 ---")
    lib_pins = _dm.oaLib.find(sn_lib_pins)
    if not lib_pins:
        try:
            lib_pins = _dm.oaLib.open(sn_lib_pins, _base.oaString(LIB_PINS_DIR),
                                       _base.oaString(LIB_PINS_DIR),
                                       _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode))
            print(f"  Opened {LIB_PINS}")
        except:
            print(f"  ⚠️  {LIB_PINS} not found — run lab16_6 first!")
            return
    else:
        print(f"  {LIB_PINS} already open")

    # ── Create or open LibSchematic ──
    print("\n--- Create LibSchematic ---")
    if os.path.exists(LIB_SCHEMATIC_DIR):
        shutil.rmtree(LIB_SCHEMATIC_DIR)
    os.makedirs(LIB_SCHEMATIC_DIR, exist_ok=True)

    lib_sch = _dm.oaLib.find(sn_lib_sch)
    if not lib_sch:
        try:
            lib_sch = _dm.oaLib.create(sn_lib_sch, _base.oaString(LIB_SCHEMATIC_DIR),
                                        _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
                                        _base.oaString("oaDMFileSys"),
                                        _dm.oaDMAttrArray(0))
            print(f"  Created {LIB_SCHEMATIC}")
        except:
            lib_sch = _dm.oaLib.open(sn_lib_sch, _base.oaString(LIB_SCHEMATIC_DIR),
                                      _base.oaString(LIB_SCHEMATIC_DIR),
                                      _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode))
            print(f"  Opened {LIB_SCHEMATIC}")

    # Setup tech
    setup_tech(ns, sn_lib_sch)

    # Create schematics
    make_schematic(ns, "HalfAdder", vt_symbol, vt_schematic, vt_netlist, sn_lib_pins, sn_lib_sch)
    make_schematic(ns, "FullAdder", vt_symbol, vt_schematic, vt_netlist, sn_lib_pins, sn_lib_sch)

    lib_pins.close()
    lib_sch.close()

    print(f"\n{'='*60}")
    print("✅ oapy Lab 16-7: Both schematics created!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
