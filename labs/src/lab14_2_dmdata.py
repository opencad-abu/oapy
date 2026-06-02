#!/usr/bin/env python3
"""
oapy Lab 14-2: dmdata — DM Data Operations

功能: 演示 DM data 对象操作 (oaLibDMData, oaCellDMData, oaCellViewDMData)
      Props 在 DM 对象上不持久化（load/save 后丢失）
      测试 oaDMFileSys 和 oaDMTurbo 两种 DM 系统

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab14_2_dmdata.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, c_str
from oapy._oa import _design, _base, _dm


LIB = "lab14_2"
LIB_PATH = "../data/LibDir14_2"
CELL = "testCell"
VIEW = "testView"


def get_dir_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except:
                pass
    return total


def test_dm(plugin):
    print(f"\n{'='*60}")
    print(f"  Testing DM system: {plugin}")
    print(f"{'='*60}")

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    os.makedirs(LIB_PATH, exist_ok=True)
    ns = get_namespace("native")

    # ── Create Lib ──
    sn_lib = make_oa_name(ns, LIB)
    lib = _dm.oaLib.create(sn_lib, make_oa_string(LIB_PATH),
            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
            make_oa_string(plugin), _dm.oaDMAttrArray(0))
    print(f"\n  Created Lib '{LIB}' at '{LIB_PATH}' ({plugin})")

    # ── Create Prop on Lib (oaDMContainer) ──
    print(f"\n  --- Props on Lib (DMContainer) ---")
    try:
        prop = _base.oaIntProp.create(lib, make_oa_string("prop_Lib_1"), 89)
        print(f"  Created IntProp: prop_Lib_1 = {prop.getValue()}")
        print(f"  Lib.hasProp() = {lib.hasProp()}")
    except Exception as e:
        print(f"  ⚠️ Props on Lib: {e}")

    # ── Create Prop on DMFile ──
    print(f"\n  --- Props on DMFile ---")
    try:
        dmfile = _dm.oaDMFile.create(lib, make_oa_string("dmfile_lib"))
        prop_dm = _base.oaIntProp.create(dmfile, make_oa_string("prop_dmfile_lib"), 9)
        print(f"  Created DMFile 'dmfile_lib'")
        print(f"  DMFile.hasProp() = {dmfile.hasProp()}")
    except Exception as e:
        print(f"  ⚠️ Props on DMFile: {e}")

    # ── Reopen Lib: Props do NOT survive persistence ──
    print(f"\n  --- Reopen: Props should NOT survive ---")
    lib.close()
    lib = _dm.oaLib.open(sn_lib, make_oa_string(LIB_PATH),
                          make_oa_string(LIB_PATH),
                          _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode))
    print(f"  Lib reopened, hasProp() = {lib.hasProp()} (expected False/0)")

    # ── Create Design ──
    print(f"\n  --- Create Design ---")
    sn_cell = make_oa_name(ns, CELL)
    sn_view = make_oa_name(ns, VIEW)
    vt = _dm.oaViewType.find(make_oa_string("netlist"))
    view = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
    block = _design.oaBlock.create(view, True)
    view.save()
    view.close()
    print(f"  Created Design: {LIB}/{CELL}/{VIEW}")

    # ── Open DM Data Objects ──
    print(f"\n  --- DM Data Objects ---")

    # oaCellViewDMData
    dmd_cv = _dm.oaCellViewDMData.open(sn_lib, sn_cell, sn_view, 'w')
    print(f"  ✅ oaCellViewDMData: {CELL}/{VIEW}")
    dmd_cv.close()

    # oaCellDMData
    dmd_cell = _dm.oaCellDMData.open(sn_lib, sn_cell, 'w')
    print(f"  ✅ oaCellDMData: {CELL}")
    dmd_cell.close()

    # oaLibDMData
    dmd_lib = _dm.oaLibDMData.open(sn_lib, 'w')
    print(f"  ✅ oaLibDMData: {LIB}")
    dmd_lib.close()

    # oaViewDMData (not supported for oaDMFileSys)
    if plugin != "oaDMFileSys":
        try:
            dmd_view = _dm.oaViewDMData.open(sn_lib, sn_view, vt, 'w')
            print(f"  ✅ oaViewDMData: {VIEW}")
            dmd_view.close()
        except Exception as e:
            print(f"  ⚠️ oaViewDMData: {e}")
    else:
        print(f"  ⏭️ oaViewDMData: not supported for oaDMFileSys")

    # ── Disk contents ──
    print(f"\n  --- Disk Contents ({plugin}) ---")
    total_size = 0
    for root, dirs, files in os.walk(LIB_PATH):
        level = root.replace(LIB_PATH, '').count(os.sep)
        indent = '    ' + '  ' * level
        bn = os.path.basename(root) or LIB_PATH
        print(f"  {indent}{bn}/")
        for f in sorted(files):
            full = os.path.join(root, f)
            try:
                sz = os.path.getsize(full)
                total_size += sz
            except:
                sz = 0
            print(f"  {indent}  {f} ({sz} bytes)")
    print(f"  Total size: {total_size} bytes")

    lib.close()

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))


def main():
    print("=" * 60)
    print("oapy Lab 14-2: DM Data Operations")
    print("=" * 60)

    init_oa()

    plugins = ["oaDMFileSys"]
    if os.environ.get("OAPY_ENABLE_DMTURBO_LAB") == "1":
        plugins.append("oaDMTurbo")
    else:
        print("\n  ⏭️ oaDMTurbo 子测试默认不运行：当前 OA/oacpp 组合下创建 DMTurbo lib 会在进程内崩溃。")
        print("     需要专项验证时设置 OAPY_ENABLE_DMTURBO_LAB=1 单独跑。")

    for plugin in plugins:
        try:
            test_dm(plugin)
        except RuntimeError as e:
            print(f"\n  ⚠️ {plugin} not available: {e}")

    print(f"\n{'='*60}")
    print(f"✅ oapy Lab 14-2 完成!")


if __name__ == "__main__":
    main()
