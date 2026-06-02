#!/usr/bin/env python3
"""
Lab 16-11: OccShape — 层次化形状遍历

功能:
  - 创建层次化设计：Top → Macro(含 Leaf 实例) → Leaf
  - 手动创建 HierPath 并遍历层次获取 OccShape
  - 获取 OccShape 的变换信息和边界框

注意: 本版本省略了 RegionQuery 回调部分（需要 Director 支持）

运行: cd /workarea/ai/openclaw/oapy && bash labs/run_lab.sh labs/lab16_11_occshape.py
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from oapy._oa import _base, _design, _dm


LIB_NAME = "LibOccShape16"
LIB_DIR = os.path.join(os.path.dirname(__file__), "../data/LibOccShape16_dir")

CELL_TOP = "Top"
CELL_MACRO = "Macro"
CELL_LEAF = "Leaf"
VIEW_NAME = "abstract"

L1 = 101
P1 = 66


def init():
    """Initialize OA, create library"""
    _design.oaDesignInit()
    
    ns = _base.oaCdbaNS()
    
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)
    os.makedirs(LIB_DIR, exist_ok=True)
    
    sn_lib = _base.oaScalarName(ns, LIB_NAME)
    lib_mode = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
    lib = _dm.oaLib.create(sn_lib, _base.oaString(LIB_DIR), lib_mode, _base.oaString("oaDMFileSys"))
    assert lib, f"Failed to create library {LIB_NAME}"
    print(f"  Created library {LIB_NAME}")
    
    return ns, lib


def create_design(ns):
    """Create hierarchical design: Top → Macro → Leaf"""
    sn_lib = _base.oaScalarName(ns, LIB_NAME)
    sn_view = _base.oaScalarName(ns, VIEW_NAME)
    vt = _dm.oaViewType.find(_base.oaString("schematic"))
    if not vt:
        vt = _dm.oaViewType.create(_base.oaString("schematic"))
    
    print("\n  Creating designs...")
    
    # Create Top design
    des_top = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, CELL_TOP), sn_view, vt, 'w')
    block_top = _design.oaBlock.create(des_top, True)
    print(f"    Created {CELL_TOP}")
    
    # Create Macro design
    des_macro = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, CELL_MACRO), sn_view, vt, 'w')
    block_macro = _design.oaBlock.create(des_macro, True)
    print(f"    Created {CELL_MACRO}")
    
    # Create Leaf design
    des_leaf = _design.oaDesign.open(sn_lib, _base.oaScalarName(ns, CELL_LEAF), sn_view, vt, 'w')
    block_leaf = _design.oaBlock.create(des_leaf, True)
    print(f"    Created {CELL_LEAF}")
    
    # ── Create shapes ──
    print("\n  Creating shapes...")
    
    # Leaf shapes (Rects)
    r1 = _design.oaRect.create(block_leaf, L1, P1, _base.oaBox(4, -2, 6, 0))
    r2 = _design.oaRect.create(block_leaf, L1, P1, _base.oaBox(2, -2, 4, 4))
    r1_bbox = r1.getBBox()
    r2_bbox = r2.getBBox()
    print(f"    Leaf: r1=({r1_bbox.left()},{r1_bbox.bottom()})({r1_bbox.right()},{r1_bbox.top()}), "
          f"r2=({r2_bbox.left()},{r2_bbox.bottom()})({r2_bbox.right()},{r2_bbox.top()})")
    
    # Macro shape (Rect)
    r3 = _design.oaRect.create(block_macro, L1, P1, _base.oaBox(2, 1, 8, 2))
    r3_bbox = r3.getBBox()
    print(f"    Macro: r3=({r3_bbox.left()},{r3_bbox.bottom()})({r3_bbox.right()},{r3_bbox.top()})")
    
    # Top shape (Ellipse)
    e1 = _design.oaEllipse.create(block_top, L1, P1, _base.oaBox(1, -3, 3, -1))
    e1_bbox = e1.getBBox()
    print(f"    Top: e1=({e1_bbox.left()},{e1_bbox.bottom()})({e1_bbox.right()},{e1_bbox.top()})")
    
    # ── Create instances ──
    print("\n  Creating instances...")
    
    # leaf1 instance in Macro at (3,1) with R270 rotation
    inst_name_leaf = _base.oaScalarName(ns, "leaf1")
    xform_leaf = _base.oaTransform(_base.oaPoint(3, 1), _base.oaOrient(_base.oaOrientEnum.oacR270))
    bv = _design.oaBlockDomainVisibilityEnum
    ps = _design.oaPlacementStatusEnum
    inst_leaf = _design.oaScalarInst.create(block_macro, des_leaf, inst_name_leaf, xform_leaf,
        _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps.oacUnplacedPlacementStatus))
    print(f"    Created leaf1 in {CELL_MACRO} at (3,1) R270")
    
    # mac1 instance in Top at (-8,-1) with MX (mirror X)
    inst_name_macro = _base.oaScalarName(ns, "mac1")
    xform_macro = _base.oaTransform(_base.oaPoint(-8, -1), _base.oaOrient(_base.oaOrientEnum.oacMX))
    inst_macro = _design.oaScalarInst.create(block_top, des_macro, inst_name_macro, xform_macro,
        _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps.oacUnplacedPlacementStatus))
    print(f"    Created mac1 in {CELL_TOP} at (-8,-1) MX")
    
    # Save all designs
    des_top.save()
    des_macro.save()
    des_leaf.save()
    
    return des_top, block_top, r1, r2, r3, e1, inst_leaf, inst_macro


def dump_bbox(bbox):
    """Format a bbox"""
    w = bbox.right() - bbox.left()
    h = bbox.top() - bbox.bottom()
    return f"({bbox.left()},{bbox.bottom()}) ({bbox.right()},{bbox.top()}) WIDTH={w} HEIGHT={h}"


def part1_manual_hierpath(des_top, r1, r2, r3, e1, inst_leaf, inst_macro):
    """PART 1: Manual creation and navigation of HierPath"""
    print("\n" + "=" * 60)
    print("PART 1: Manual creation of HierPath")
    print("=" * 60)
    
    hp = _design.oaHierPath()
    print(f"\nAfter initial construction of a HierPath before any pushLevel()")
    print(f"  HierPath: Top (i.e., empty hierPath)")
    print(f"    depth={hp.getDepth()}")
    
    # r1, r2, r3 should not be accessible at Top level
    print("\nThere are no Rects at the Top level:")
    for name, shape in [("r1", r1), ("r2", r2), ("r3", r3)]:
        try:
            occ = _design.oaOccShape.get(shape, des_top, hp)
            print(f"  {name}: found (unexpected)")
        except:
            print(f"  {name}: InvalidHierPath (expected)")
    
    # e1 IS accessible at Top level
    print(f"\nBBoxes of OccShapes in Top:")
    occ_e1 = _design.oaOccShape.get(e1, des_top, hp)
    print(f"  e1: {dump_bbox(occ_e1.getBBox())}")
    
    # Push level to Macro
    print("\n" + "-" * 40)
    hp.pushLevel(inst_macro)
    print(f"  HierPath: Macro1")
    print(f"    depth={hp.getDepth()}")
    
    # r1, r2 still not accessible at Macro level
    print("\nThere is no r1 or r2 at the Macro level:")
    for name, shape in [("r1", r1), ("r2", r2)]:
        try:
            occ = _design.oaOccShape.get(shape, des_top, hp)
            print(f"  {name}: found (unexpected)")
        except:
            print(f"  {name}: InvalidHierPath (expected)")
    
    # r3 IS accessible at Macro level
    print(f"\nBBoxes of OccShapes in Macro1, relative to Top coordinate system:")
    occ_r3 = _design.oaOccShape.get(r3, des_top, hp)
    print(f"  r3: {dump_bbox(occ_r3.getBBox())}")
    
    # Push level to Leaf
    print("\n" + "-" * 40)
    hp.pushLevel(inst_leaf)
    print(f"  HierPath: Leaf1")
    print(f"    depth={hp.getDepth()}")
    
    print(f"\nBBoxes in Leaf1, relative to Top coordinate system:")
    occ_r1 = _design.oaOccShape.get(r1, des_top, hp)
    print(f"  r1: {dump_bbox(occ_r1.getBBox())}")
    occ_r2 = _design.oaOccShape.get(r2, des_top, hp)
    print(f"  r2: {dump_bbox(occ_r2.getBBox())}")
    
    # Get HierPath from OccShape and compare transforms
    print(f"\nHierPath comparison (from OccShape vs manual):")
    hp2 = occ_r1.getHierPath()
    print(f"  OccShape.getHierPath() depth: {hp2.getDepth()}")
    print(f"  Manual HierPath depth: {hp.getDepth()}")


def main():
    print("=" * 60)
    print("Lab 16-11: OccShape — 层次化形状遍历")
    print("=" * 60)
    
    ns, lib = init()
    des_top, block_top, r1, r2, r3, e1, inst_leaf, inst_macro = create_design(ns)
    
    part1_manual_hierpath(des_top, r1, r2, r3, e1, inst_leaf, inst_macro)
    
    des_top.close()
    lib.close()
    shutil.rmtree(LIB_DIR)
    
    print("\n" + "=" * 60)
    print("✅ Lab 16-11: OccShape complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
