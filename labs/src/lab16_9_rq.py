#!/usr/bin/env python3
"""
Lab 16-9: RegionQuery — 区域查询和空间搜索

功能:
  - 初始化 RegionQuery 插件 (oaRQXYTree)
  - 实现 oaShapeQuery 回调，查询指定区域内的形状
  - 实现 oaInstQuery 回调，查询指定区域内的实例
  - 实现 oaViaQuery 回调，查询指定区域内的 Via

运行: cd /workarea/ai/openclaw/oapy && bash labs/run_lab.sh labs/lab16_9_rq.py
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from oapy._oa import _base, _design, _dm


class MyShapeQuery(_design.oaShapeQuery):
    """Shape 查询回调类"""
    
    def __init__(self):
        super().__init__()
        self.shape_count = 0
    
    def queryShape(self, shape):
        """对每个匹配的形状调用"""
        self.shape_count += 1
        bbox = shape.getBBox()
        layer = shape.getLayerNum()
        purpose = shape.getPurposeNum()
        
        # 获取 OccShape 和层次路径
        occ = self.getOccShape(shape)
        hp = _design.oaHierPath()
        self.getHierPath(hp)
        
        print(f"  Shape #{self.shape_count}: layer={layer} purpose={purpose} "
              f"bbox=({bbox.left()},{bbox.bottom()},{bbox.right()},{bbox.top()}) "
              f"depth={hp.getDepth()}")


class MyInstQuery(_design.oaInstQuery):
    """Inst 查询回调类"""
    
    def __init__(self):
        super().__init__()
        self.inst_count = 0
    
    def queryInst(self, inst):
        """对每个匹配的实例调用"""
        self.inst_count += 1
        bbox = inst.getBBox()
        name = inst.getName(_base.oaScalarName(_base.oaNativeNS(), ""))
        
        # 获取变换
        xf = self.getCurrentTransform()
        
        print(f"  Inst #{self.inst_count}: name={name} "
              f"bbox=({bbox.left()},{bbox.bottom()},{bbox.right()},{bbox.top()}) "
              f"xform=({xf.xOffset()},{xf.yOffset()},{xf.orient().getName()})")


class MyViaQuery(_design.oaViaQuery):
    """Via 查询回调类"""
    
    def __init__(self):
        super().__init__()
        self.via_count = 0
    
    def queryVia(self, via):
        """对每个匹配的 Via 调用"""
        self.via_count += 1
        bbox = via.getBBox()
        
        print(f"  Via #{self.via_count}: "
              f"bbox=({bbox.left()},{bbox.bottom()},{bbox.right()},{bbox.top()})")


def is_msg_3107(exc):
    text = str(exc)
    return "msgId=3107" in text or "already exists with viewType" in text


def main():
    print("=" * 60)
    print("oapy Lab 16-9: RegionQuery 区域查询")
    print("=" * 60)
    
    # 初始化 OA
    _design.oaDesignInit()
    
    # 初始化 RegionQuery 插件
    print("\n--- 初始化 RegionQuery ---")
    _design.oaRegionQuery.init(_base.oaString("oaRQXYTree"))
    print("  RegionQuery plugin initialized")
    
    # 创建测试库和设计
    print("\n--- 创建测试设计 ---")
    ns = _base.oaNativeNS()
    lib_dir = os.path.join(os.path.dirname(__file__), "../data/LibRQ16_dir")
    
    if os.path.exists(lib_dir):
        import shutil
        shutil.rmtree(lib_dir)
    os.makedirs(lib_dir)
    
    sn_lib = _base.oaScalarName(ns, f"LibRQ16_{os.getpid()}")
    lib = _dm.oaLib.create(sn_lib, _base.oaString(lib_dir))
    
    sn_cell = _base.oaScalarName(ns, "TestCell")
    sn_view = _base.oaScalarName(ns, "layout")
    try:
        vt = _dm.oaViewType.get(_dm.oaReservedViewType(_base.oaString("maskLayout")))
        des = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
    except Exception as exc:
        if not is_msg_3107(exc):
            raise
        print(f"  3107 fallback: {exc}")
        des = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
    block = _design.oaBlock.create(des, True)
    
    # 创建一些形状
    layer1 = 101
    layer2 = 102
    purpose = 0  # drawing
    
    # 在不同位置创建矩形
    rects = [
        (0, 0, 10, 10, layer1),
        (20, 0, 30, 10, layer1),
        (0, 20, 10, 30, layer2),
        (50, 50, 60, 60, layer1),
    ]
    
    for i, (x1, y1, x2, y2, layer) in enumerate(rects):
        rect = _design.oaRect.create(block, layer, purpose, _base.oaBox(x1, y1, x2, y2))
        print(f"  Created rect #{i+1}: layer={layer} bbox=({x1},{y1},{x2},{y2})")
    
    # 初始化 RegionQuery 索引
    block.initForRegionQuery()
    print("  RegionQuery index initialized")
    
    # 执行 Shape 查询
    print("\n--- Shape 查询 (layer=101, 整个区域) ---")
    sq = MyShapeQuery()
    query_box = _base.oaBox(-100, -100, 200, 200)
    sq.query(des, layer1, purpose, query_box, filterSize=0, startLevel=0, stopLevel=100)
    print(f"  Total shapes found: {sq.shape_count}")
    
    # 执行 Shape 查询 (layer=102)
    print("\n--- Shape 查询 (layer=102, 整个区域) ---")
    sq2 = MyShapeQuery()
    sq2.query(des, layer2, purpose, query_box, filterSize=0, startLevel=0, stopLevel=100)
    print(f"  Total shapes found: {sq2.shape_count}")
    
    # 执行局部区域查询
    print("\n--- Shape 查询 (layer=101, 小区域 [0,0,15,15]) ---")
    sq3 = MyShapeQuery()
    small_box = _base.oaBox(0, 0, 15, 15)
    sq3.query(des, layer1, purpose, small_box, filterSize=0, startLevel=0, stopLevel=100)
    print(f"  Total shapes found: {sq3.shape_count}")
    
    # 执行 Inst 查询 (当前没有实例)
    print("\n--- Inst 查询 ---")
    iq = MyInstQuery()
    iq.query(des, query_box, filterSize=0, startLevel=0, stopLevel=100)
    print(f"  Total instances found: {iq.inst_count}")
    
    # 执行 Via 查询 (当前没有 Via)
    print("\n--- Via 查询 ---")
    vq = MyViaQuery()
    vq.query(des, query_box, filterSize=0, startLevel=0, stopLevel=100)
    print(f"  Total vias found: {vq.via_count}")
    
    # 清理
    des.close()
    lib.close()
    
    print("\n" + "=" * 60)
    print("✅ Lab 16-9 完成！RegionQuery 回调机制工作正常")
    print("=" * 60)


if __name__ == "__main__":
    main()
