#!/usr/bin/env python3
"""
oapy Lab 10-2: datacompress — 测试 Design 数据压缩功能

功能: 创建大量 Nets 和 Shapes 的设计，测试不同数据压缩级别对磁盘存储的影响。

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab10_2_datacompress.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, c_str
from oapy._oa import _design, _base, _dm


LIB = "lab10_2"
LIB_PATH = "../data/LibDir10_2"
NUM_NETS = 100
GRID_X = 20
GRID_Y = 20


def get_disk_size(path):
    """计算目录磁盘使用量"""
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except:
                pass
    return total


def main():
    print("=" * 60)
    print("oapy Lab 10-2: Data Compression")
    print("=" * 60)

    init_oa()

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    os.makedirs(LIB_PATH, exist_ok=True)
    ns = get_namespace("native")

    # ── Create Lib ──
    sn_lib = make_oa_name(ns, LIB)
    lib = _dm.oaLib.create(sn_lib, make_oa_string(LIB_PATH),
            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
            make_oa_string('oaDMFileSys'), _dm.oaDMAttrArray(0))
    print(f"\nCreated Lib '{LIB}' at '{LIB_PATH}'")

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    ST = _design.oaSigTypeEnum; BV = _design.oaBlockDomainVisibilityEnum
    sig = _design.oaSigType(ST.oacSignalSigType)
    vis = _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock)

    # ── Test different compression levels ──
    configs = [
        ("no_compress", None),
        ("low_compress", 3),
        ("high_compress", 9),
    ]

    for cell_name, level in configs:
        print(f"\n--- {cell_name} (level={level}) ---")

        sn_cell = make_oa_name(ns, cell_name)
        sn_view = make_oa_name(ns, "schematic")
        view = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
        block = _design.oaBlock.create(view, True)

        # Try setting compression level
        if level is not None:
            try:
                lib.setDataCompression(level)
                print(f"  Set lib compression level to {level}")
            except Exception as e:
                print(f"  ⚠️ setDataCompression: {e}")

        # Create NUM_NETS nets
        for i in range(NUM_NETS):
            name = f"net_{i}"
            _design.oaScalarNet.create(block, make_oa_name(ns, name), sig, 1, vis)
        print(f"  Created {NUM_NETS} nets")

        # Create shapes on a grid
        for x in range(GRID_X):
            for y in range(GRID_Y):
                _design.oaRect.create(block, 1, 1, _base.oaBox(x*10, y*10, x*10+8, y*10+8))
        print(f"  Created {GRID_X * GRID_Y} rects")

        view.save()
        view.close()
        print(f"  Design saved")

    # ── Verify disk sizes ──
    print(f"\n{'='*60}")
    print("Disk Size Comparison:")
    print(f"{'='*60}")
    lib.close()

    for cell_name, level in configs:
        cell_path = os.path.join(LIB_PATH, cell_name)
        if os.path.exists(cell_path):
            size = get_disk_size(cell_path)
            print(f"  {cell_name:20s} (level={level!s:5s}): {size:>6d} bytes")

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    print(f"\n✅ oapy Lab 10-2 完成!")


if __name__ == "__main__":
    main()
