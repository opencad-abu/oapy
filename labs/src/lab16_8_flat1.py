#!/usr/bin/env python3
"""
oapy Lab 16-8: Flat1 — 展平设计层次结构

功能:
  - 遍历设计层次结构
  - 将所有叶子级实例复制到展平的设计中
  - 使用层次路径名作为新实例名
  - 添加 IsALeaf 属性标记叶子实例

依赖: Lab 16-7 (schematic) 必须已运行，LibSchematic 必须存在

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab16_8_flat1.py
"""

import os
from utils import init_oa, get_namespace
from oapy._oa import _design, _base, _dm, _tech


LIB_PINS = "LibPins16"
LIB_SCHEMATIC = "LibSchematic"
LIB_PINS_DIR = "../data/LibPins16_dir"
LIB_SCHEMATIC_DIR = "../data/LibSchematic_dir"
VIEW_SYMBOL = "symbol"
VIEW_SCHEMATIC = "schematic"
VIEW_FLAT1 = "flat1"


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


def open_lib(ns, lib_name, lib_dir):
    """Open or find a library."""
    sn_lib = _base.oaScalarName(ns, lib_name)
    lib = _dm.oaLib.find(sn_lib)
    if not lib:
        try:
            lib = _dm.oaLib.open(sn_lib, _base.oaString(lib_dir),
                                  _base.oaString(lib_dir),
                                  _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode))
            print(f"  Opened {lib_name}")
        except:
            print(f"  ⚠️  {lib_name} not found!")
            return None
    else:
        print(f"  {lib_name} already open")
    return lib


def flatten_design(ns, source, copy):
    """
    Walk the instance hierarchy and flatten leaf instances.
    """
    # Create top block for the flattened design
    flatten_block = _design.oaBlock.create(copy, True)
    print(f"  Created flatten block")

    nns = _base.oaNativeNS()

    def at_inst(current_inst, trans, hier_str):
        """
        Create flattened instance if it's a leaf.
        """
        # If we're at the top, do nothing
        if current_inst is None:
            return

        # Check if it's a scalar instance
        # oacScalarInstType = 50 (from oaType.h); enum not yet bound in oapy
        if current_inst.getType() != 50:
            return

        # Get the master
        master = current_inst.getMaster()
        if not master:
            return

        # Check if master has instances (if yes, it's not a leaf)
        master_block = master.getTopBlock()
        if master_block:
            insts = master_block.getInsts(0)
            if not insts.isEmpty():
                return  # Not a leaf

        # Create the instance in the flattened design
        if not hier_str:
            print(f"  WARNING: empty hier_str, skipping")
            return

        copy_name = _base.oaScalarName(nns, hier_str)
        bv = _design.oaBlockDomainVisibilityEnum
        bdv = _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock)
        ps = _design.oaPlacementStatusEnum
        _design.oaScalarInst.create(flatten_block, master, copy_name, trans,
                                     _base.oaParamArray(0), bdv,
                                     _design.oaPlacementStatus(ps.oacUnplacedPlacementStatus))

        print(f"    Instance copied = {hier_str}")

        # Create IsALeaf property on the current instance
        try:
            prop = _design.oaProp.find(current_inst, _base.oaString("IsALeaf"))
            if not prop:
                _design.oaBooleanProp.create(current_inst, _base.oaString("IsALeaf"), True)
        except:
            pass  # Property might already exist

    def append_name_to_hier(hier_str, inst_name_simple):
        """Append instance name to hierarchy string with '|' separator."""
        inst_str = _base.oaString()
        inst_name_simple.get(nns, inst_str)
        name_str = str(inst_str)
        if hier_str:
            return hier_str + "|" + name_str
        else:
            return name_str

    def walk(current_inst, trans, hier_str):
        """
        Walk the instance hierarchy recursively.
        """
        # Get current design
        if current_inst:
            cv_current = current_inst.getMaster()
        else:
            cv_current = source

        if not cv_current:
            return

        block_current = cv_current.getTopBlock()
        if not block_current:
            return

        # Process this instance
        at_inst(current_inst, trans, hier_str)

        # Iterate over instance headers
        headers = block_current.getInstHeaders()
        iter_headers = _design.oaIter_oaInstHeader(headers)
        header = iter_headers.getNext()
        while header:
            # Check for unbound instance header
            master = header.getMaster()
            if not master:
                lib_str = _base.oaString()
                cell_str = _base.oaString()
                view_str = _base.oaString()
                header.getLibName(nns, lib_str)
                header.getCellName(nns, cell_str)
                header.getViewName(nns, view_str)
                print(f"  WARNING: Design {lib_str} {cell_str} {view_str} "
                      f"does not exist. Unbound instance found")

            # Iterate over all instances of this header
            insts = header.getInsts(0)
            iter_insts = _design.oaIter_oaInst(insts)
            inst = iter_insts.getNext()
            while inst:
                # Get instance transform
                inst_trans = _base.oaTransform()
                inst.getTransform(inst_trans)

                # Concatenate transforms: inst_trans * trans -> result
                result = _base.oaTransform()
                inst_trans.concat(trans, result)

                # Get instance name
                inst_name = _base.oaSimpleName()
                inst.getName(inst_name)

                # Append to hierarchy string
                new_hier = append_name_to_hier(hier_str, inst_name)

                # Recurse
                walk(inst, result, new_hier)

                inst = iter_insts.getNext()

            header = iter_headers.getNext()

    # Start walking from top with identity transform
    top_trans = _base.oaTransform()
    walk(None, top_trans, "")


def flatten_cell(ns, cell_name, vt_schematic, vt_symbol, vt_netlist, sn_lib_sch):
    """Flatten a single cell's design hierarchy"""
    print(f"\n{'='*60}")
    print(f"Flattening {cell_name}")
    print(f"{'='*60}")

    sn_cell = _base.oaScalarName(ns, cell_name)
    sn_view_sch = _base.oaScalarName(ns, VIEW_SCHEMATIC)
    sn_view_flat = _base.oaScalarName(ns, VIEW_FLAT1)

    # Open source design (schematic view from LibSchematic)
    source = open_design_with_viewtypes(sn_lib_sch, sn_cell, sn_view_sch, 'r',
                                        vt_schematic, vt_symbol, vt_netlist)
    if not source:
        print(f"  ⚠️  Cannot open source: {LIB_SCHEMATIC}/{cell_name}/{VIEW_SCHEMATIC}")
        return False
    print(f"  Opened source: {LIB_SCHEMATIC}/{cell_name}/{VIEW_SCHEMATIC}")

    # Create flattened design in same library
    copy = _design.oaDesign.open(sn_lib_sch, sn_cell, sn_view_flat,
                                  source.getViewType(), 'w')
    if not copy:
        print(f"  ⚠️  Cannot create flat design: {LIB_SCHEMATIC}/{cell_name}/{VIEW_FLAT1}")
        source.close()
        return False

    # Set cell type
    copy.setCellType(source.getCellType())

    print(f"  Writing {LIB_SCHEMATIC} {cell_name} {VIEW_FLAT1}")

    # Flatten
    flatten_design(ns, source, copy)

    # Save and close
    copy.save()
    copy.close()
    source.close()

    print(f"  ✅ {cell_name} flattened successfully!")
    return True


def main():
    print("=" * 60)
    print("oapy Lab 16-8: Flat1 — Design Flattening")
    print("=" * 60)

    init_oa()

    ns = _base.oaNativeNS()
    vt_netlist = reserved_view_type(_dm.oaReservedViewTypeEnum.oacNetlist)
    vt_symbol = reserved_view_type(_dm.oaReservedViewTypeEnum.oacSchematicSymbol)
    vt_schematic = reserved_view_type(_dm.oaReservedViewTypeEnum.oacSchematic)

    sn_lib_sch = _base.oaScalarName(ns, LIB_SCHEMATIC)

    # ── Open libraries ──
    print("\n--- Open Libraries ---")
    lib_pins = open_lib(ns, LIB_PINS, LIB_PINS_DIR)
    lib_sch = open_lib(ns, LIB_SCHEMATIC, LIB_SCHEMATIC_DIR)

    if not lib_sch:
        print("  ⚠️  LibSchematic not found — run lab16_7 first!")
        return

    # Flatten both cells
    flatten_cell(ns, "HalfAdder", vt_schematic, vt_symbol, vt_netlist, sn_lib_sch)
    flatten_cell(ns, "FullAdder", vt_schematic, vt_symbol, vt_netlist, sn_lib_sch)

    # Clean up
    if lib_pins:
        lib_pins.close()
    lib_sch.close()

    print(f"\n{'='*60}")
    print("✅ oapy Lab 16-8: All designs flattened!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
