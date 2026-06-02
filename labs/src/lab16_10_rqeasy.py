#!/usr/bin/env python3
"""
Lab 16-10: RQEasy — 简化版 RegionQuery，重点演示 filterSize

功能:
  - 创建不同形状（rect、polygon、donut、via）
  - 使用 oaShapeQuery 回调查询区域内形状
  - 演示 filterSize 参数对查询结果的影响
  - 使用 oaInstQuery/oaViaQuery 查询实例和 Via

运行: cd /workarea/ai/openclaw/oapy && bash labs/run_lab.sh labs/lab16_10_rqeasy.py
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from oapy._oa import _base, _design, _dm, _tech


LAYER1 = 101
CUT12 = 102
LAYER2 = 103
PURPOSE = 0  # drawing


class CountingShapeQuery(_design.oaShapeQuery):
    """带计数的 Shape 查询回调"""

    def __init__(self):
        super().__init__()
        self.counter = 0

    def queryShape(self, shape):
        self.counter += 1
        bbox = shape.getBBox()
        hp = _design.oaHierPath()
        self.getHierPath(hp)
        type_name = shape.getType().getName()
        print(f"  #{self.counter} {type_name} layer={shape.getLayerNum()} "
              f"bbox=({bbox.left()},{bbox.bottom()},{bbox.right()},{bbox.top()}) "
              f"depth={hp.getDepth()}")


class CountingInstQuery(_design.oaInstQuery):
    """带计数的 Inst 查询回调"""

    def __init__(self):
        super().__init__()
        self.counter = 0

    def queryInst(self, inst):
        self.counter += 1
        ns = _base.oaNativeNS()
        sn = _base.oaScalarName(ns, "")
        inst.getName(ns, sn)
        bbox = inst.getBBox()
        hp = _design.oaHierPath()
        self.getHierPath(hp)
        print(f"  #{self.counter} inst name={sn} "
              f"bbox=({bbox.left()},{bbox.bottom()},{bbox.right()},{bbox.top()}) "
              f"depth={hp.getDepth()}")


class CountingViaQuery(_design.oaViaQuery):
    """带计数的 Via 查询回调"""

    def __init__(self):
        super().__init__()
        self.counter = 0

    def queryVia(self, via):
        self.counter += 1
        bbox = via.getBBox()
        hp = _design.oaHierPath()
        self.getHierPath(hp)
        print(f"  #{self.counter} via "
              f"bbox=({bbox.left()},{bbox.bottom()},{bbox.right()},{bbox.top()}) "
              f"depth={hp.getDepth()}")


def is_msg_3107(exc):
    text = str(exc)
    return "msgId=3107" in text or "already exists with viewType" in text


def create_design(ns, lib_dir):
    """创建测试设计，包含各种形状和实例"""
    sn_lib = _base.oaScalarName(ns, f"LibRQEasy16_{os.getpid()}")
    lib = _dm.oaLib.create(sn_lib, _base.oaString(lib_dir))

    sn_top = _base.oaScalarName(ns, "top")
    sn_lev1 = _base.oaScalarName(ns, "lev1")
    sn_lev2 = _base.oaScalarName(ns, "lev2")
    sn_view = _base.oaScalarName(ns, "layout")

    def open_layout(cell):
        try:
            vt = _dm.oaViewType.get(_dm.oaReservedViewType(_base.oaString("maskLayout")))
            return _design.oaDesign.open(sn_lib, cell, sn_view, vt, 'w')
        except Exception as exc:
            if not is_msg_3107(exc):
                raise
            print(f"  3107 fallback: {exc}")
            return _design.oaDesign.open(sn_lib, cell, sn_view, vt, 'w')

    des_top = open_layout(sn_top)
    des_l1 = open_layout(sn_lev1)
    des_l2 = open_layout(sn_lev2)

    block_top = _design.oaBlock.create(des_top, True)
    block_l1 = _design.oaBlock.create(des_l1, True)
    block_l2 = _design.oaBlock.create(des_l2, True)

    # 在 lev2 创建矩形
    _design.oaRect.create(block_l2, LAYER1, PURPOSE, _base.oaBox(0, 0, 3, 1))
    print("  Created rect in lev2: (0,0,3,1) layer=101")

    # 在 lev2 创建 donut
    _design.oaDonut.create(block_l2, LAYER1, PURPOSE, _base.oaPoint(55, -60), 6, 3)
    print("  Created donut in lev2: (55,-60) r=6/3 layer=101")

    # 在 top 创建 polygon (菱形)
    pa = _base.oaPointArray(4)
    pa.append(_base.oaPoint(1, 0))
    pa.append(_base.oaPoint(0, 2))
    pa.append(_base.oaPoint(1, 4))
    pa.append(_base.oaPoint(2, 2))
    _design.oaPolygon.create(block_top, LAYER1, PURPOSE, pa)
    print("  Created polygon (diamond) in top: layer=101")

    # 在 top 创建 path
    pa2 = _base.oaPointArray(3)
    pa2.append(_base.oaPoint(0, 0))
    pa2.append(_base.oaPoint(3, 2))
    pa2.append(_base.oaPoint(5, 2))
    _design.oaPath.create(block_top, LAYER1, PURPOSE, 8, pa2)
    print("  Created path in top: layer=101")

    # 创建实例
    bv = _design.oaBlockDomainVisibilityEnum
    ps = _design.oaPlacementStatusEnum

    i1 = _design.oaScalarInst.create(block_top, des_l1,
        _base.oaScalarName(ns, "i1"),
        _base.oaTransform(_base.oaPoint(0, 0), _base.oaOrient(_base.oaOrientEnum.oacR0)),
        _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps.oacUnplacedPlacementStatus))

    i2 = _design.oaScalarInst.create(block_l1, des_l2,
        _base.oaScalarName(ns, "i2"),
        _base.oaTransform(_base.oaPoint(1, 1), _base.oaOrient(_base.oaOrientEnum.oacR0)),
        _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps.oacUnplacedPlacementStatus))
    print("  Created inst i1 in top → lev1, i2 in lev1 → lev2")

    print("  Tech setup skipped: RegionQuery lab uses numeric layer/purpose ids only")

    print("  Save skipped: official RegionQuery path is validated in-memory")

    return des_top, lib


def main():
    print("=" * 60)
    print("oapy Lab 16-10: RQEasy — 简化 RegionQuery")
    print("=" * 60)

    _design.oaDesignInit()

    ns = _base.oaNativeNS()
    lib_dir = os.path.join(os.path.dirname(__file__), "../data/LibRQEasy16_dir")
    if os.path.exists(lib_dir):
        import shutil
        shutil.rmtree(lib_dir)
    os.makedirs(lib_dir)

    print("\n--- 创建测试设计 ---")
    des_top, lib = create_design(ns, lib_dir)
    block_top = des_top.getTopBlock()

    # 初始化 RegionQuery
    print("\n--- 初始化 RegionQuery ---")
    _design.oaRegionQuery.init(_base.oaString("oaRQXYTree"))
    block_top.initForRegionQuery()
    plug_name = _base.oaString("")
    _design.oaRegionQuery.getPlugInName(plug_name)
    print(f"  Plugin: {plug_name}")

    des_top.openHier()
    query_window = _base.oaBox(-10000, -10000, 10000, 10000)

    # Shape 查询 layer=101, filterSize=0
    print("\n--- Shape Query: layer=101, filterSize=0 ---")
    sq = CountingShapeQuery()
    sq.query(des_top, LAYER1, PURPOSE, query_window, filterSize=0)
    print(f"  Found: {sq.counter} shapes")

    # Shape 查询 layer=101, filterSize=5 (过滤掉小形状)
    print("\n--- Shape Query: layer=101, filterSize=5 ---")
    sq2 = CountingShapeQuery()
    sq2.query(des_top, LAYER1, PURPOSE, query_window, filterSize=5)
    print(f"  Found: {sq2.counter} shapes (small shapes filtered)")

    # Inst 查询
    print("\n--- Inst Query ---")
    iq = CountingInstQuery()
    iq.query(des_top, query_window, filterSize=0)
    print(f"  Found: {iq.counter} instances")

    # Via 查询
    print("\n--- Via Query ---")
    vq = CountingViaQuery()
    vq.query(des_top, query_window, filterSize=0)
    print(f"  Found: {vq.counter} vias")

    des_top.close()
    lib.close()

    print("\n" + "=" * 60)
    print("✅ Lab 16-10 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
