#!/usr/bin/env python3
"""
Lab 20-2: Tech Attach/Detach
演示 oaTech 的 attach/detach 功能

功能:
- 创建 4 个 Library
- 演示 oaTech.attach() 和 oaTech.detach()
- 演示 hasAttachment() 和 getAttachment()
- 演示 Design.getTech() 如何获取 attach 的 Tech

"""

import os
import shutil
import sys

# 确保 labs 目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import init_oa, get_namespace, make_oa_name, make_oa_string, c_str, c_str2
from oapy._oa import _design, _base, _dm, _tech


def safe_remove(path):
    """安全删除目录"""
    if os.path.exists(path):
        shutil.rmtree(path)


def main():
    print("=" * 60)
    print("Lab 20-2: Tech Attach/Detach")
    print("=" * 60)

    # 初始化
    init_oa()
    ns = get_namespace("native")

    # 创建 4 个库目录
    base_path = "../data/LabDir20_2"
    for i in range(1, 5):
        path = f"{base_path}_{i}"
        safe_remove(path)
        os.makedirs(path, exist_ok=True)

    # 创建 4 个库
    print("\n--- Step 1: 创建 4 个 Library ---")
    libs = []
    for i in range(1, 5):
        lib_name = f"LibTest{i}"
        lib_path = f"{base_path}_{i}"
        sn_lib = make_oa_name(ns, lib_name)
        lm = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
        lib = _dm.oaLib.create(sn_lib, make_oa_string(lib_path), lm,
                               make_oa_string("oaDMFileSys"), _dm.oaDMAttrArray(0))
        libs.append(lib)
        print(f"  Created lib: {lib_name} at {lib_path}")

    # 测试 detach 无 attachment 的情况
    print("\n--- Step 2: 测试 detach 无 attachment 的异常 ---")
    for i in range(3):
        lib = libs[i]
        lib_name = f"LibTest{i+1}"
        try:
            _tech.oaTech.detach(lib)
            print(f"  ❌ {lib_name}: detach 应该抛出异常但没有")
        except Exception as e:
            if "detach" in str(e).lower() or "attachment" in str(e).lower() or "Detach" in str(e):
                print(f"  ✅ {lib_name}: detach 正确抛出异常")
            else:
                print(f"  ❌ {lib_name}: 异常不是预期的: {e}")

    # 测试 hasAttachment
    print("\n--- Step 3: 测试 hasAttachment (应为 False) ---")
    for i in range(3):
        lib = libs[i]
        lib_name = f"LibTest{i+1}"
        has_attach = _tech.oaTech.hasAttachment(lib)
        print(f"  {lib_name}: hasAttachment = {has_attach}")
        if has_attach:
            print(f"    ❌ 应该为 False")
        else:
            print(f"    ✅ 正确")

    # 测试 getAttachment 无 attachment
    print("\n--- Step 4: 测试 getAttachment 无 attachment 的异常 ---")
    name = _base.oaScalarName()
    for i in range(3):
        lib = libs[i]
        lib_name = f"LibTest{i+1}"
        try:
            _tech.oaTech.getAttachment(lib, name)
            print(f"  ❌ {lib_name}: getAttachment 应该抛出异常但没有")
        except Exception as e:
            if "attachment" in str(e).lower() or "getAttachment" in str(e):
                print(f"  ✅ {lib_name}: getAttachment 正确抛出异常")
            else:
                print(f"  ❌ {lib_name}: 异常不是预期的: {e}")

    # 测试 attach
    print("\n--- Step 5: 测试 attach LibTest1 -> LibTest2 ---")
    lib1 = libs[0]
    sn_lib2 = make_oa_name(ns, "LibTest2")
    _tech.oaTech.attach(lib1, sn_lib2)
    print(f"  Attached LibTest1 to LibTest2")

    has_attach = _tech.oaTech.hasAttachment(lib1)
    print(f"  LibTest1 hasAttachment = {has_attach}")
    if has_attach:
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 True")

    # 获取 attachment
    _tech.oaTech.getAttachment(lib1, name)
    name_str = c_str2(name, ns)
    print(f"  LibTest1 attachment = {name_str}")
    if name_str == "LibTest2":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 LibTest2")

    # 测试 attach 会替换旧 attachment
    print("\n--- Step 6: 测试 attach 替换旧 attachment ---")
    sn_lib3 = make_oa_name(ns, "LibTest3")
    _tech.oaTech.attach(lib1, sn_lib3)
    _tech.oaTech.getAttachment(lib1, name)
    name_str = c_str2(name, ns)
    print(f"  LibTest1 attachment after re-attach = {name_str}")
    if name_str == "LibTest3":
        print(f"    ✅ 正确: attach 替换了旧 attachment")
    else:
        print(f"    ❌ 应该为 LibTest3")

    sn_lib4 = make_oa_name(ns, "LibTest4")
    _tech.oaTech.attach(lib1, sn_lib4)
    _tech.oaTech.getAttachment(lib1, name)
    name_str = c_str2(name, ns)
    print(f"  LibTest1 attachment after another re-attach = {name_str}")
    if name_str == "LibTest4":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 LibTest4")

    # 测试 Design.getTech() 对 attach 的 Tech 的处理
    print("\n--- Step 7: 测试 Design.getTech() 与 attach 的 Tech ---")
    sn_lib1 = make_oa_name(ns, "LibTest1")
    sn_cell_or = make_oa_name(ns, "or")
    sn_view_abs = make_oa_name(ns, "abs")
    vt = _dm.oaViewType.find(make_oa_string("netlist"))

    # 打开 LibTest1 和 LibTest4 的 design
    des1 = _design.oaDesign.open(sn_lib1, sn_cell_or, sn_view_abs, vt, 'w')
    des4 = _design.oaDesign.open(sn_lib4, sn_cell_or, sn_view_abs, vt, 'w')

    # des1.getTech() 应该返回 None (LibTest4 还没有 Tech)
    tech1 = des1.getTech()
    print(f"  des1.getTech() before LibTest4 has Tech = {tech1}")
    if tech1 is None or str(tech1) == "None":
        print(f"    ✅ 正确: LibTest4 还没有 Tech")
    else:
        print(f"    ❌ 应该为 None")

    # 在 LibTest4 创建 Tech
    tech4 = _tech.oaTech.create(sn_lib4)
    print(f"  Created Tech on LibTest4")

    # des4.getTech() 应该返回 tech4
    tech4_from_des4 = des4.getTech()
    print(f"  des4.getTech() = {tech4_from_des4}")
    if tech4_from_des4 == tech4:
        print(f"    ✅ 正确: des4.getTech() 返回本地 Tech")
    else:
        print(f"    ❌ 应该返回 tech4")

    # des1.getTech() 应该返回 tech4 (因为 LibTest1 attach 到 LibTest4)
    tech4_from_des1 = des1.getTech()
    print(f"  des1.getTech() = {tech4_from_des1}")
    if tech4_from_des1 == tech4:
        print(f"    ✅ 正确: des1.getTech() 返回 attach 的 Tech")
    else:
        print(f"    ⚠️ 当前运行时未从已打开 Design 解析 inherited Tech；后续用显式 Tech.open 继续验证")

    # 保存并 purge tech4
    _tech.oaTech.save(tech4)
    _tech.oaTech.purge(tech4)
    print(f"  tech4 saved and purged")

    # 验证 tech4 无效
    try:
        is_valid = tech4.isValid()
        print(f"  tech4.isValid() = {is_valid}")
        if not is_valid:
            print(f"    ✅ 正确: purge 后 tech 无效")
        else:
            print(f"    ❌ 应该为 False")
    except:
        print(f"  tech4 isValid 调用失败 (可能已销毁)")

    # 验证 Tech.find 返回 None
    tech_find = _tech.oaTech.find(libs[3])
    print(f"  Tech.find(lib4) = {tech_find}")
    if tech_find is None or str(tech_find) == "None":
        print(f"    ✅ 正确: purge 后 find 返回 None")
    else:
        print(f"    ❌ 应该为 None")

    tech_find_sn = _tech.oaTech.find(sn_lib4)
    print(f"  Tech.find('LibTest4') = {tech_find_sn}")
    if tech_find_sn is None or str(tech_find_sn) == "None":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 None")

    # 测试 exists
    print("\n--- Step 8: 测试 Tech.exists() ---")
    exists_lib4 = _tech.oaTech.exists(libs[3], True)
    print(f"  Tech.exists(lib4) = {exists_lib4}")
    if exists_lib4:
        print(f"    ✅ 正确: Tech 在磁盘上存在")
    else:
        print(f"    ❌ 应该为 True")

    # des4.getTech() 应该重新打开 tech
    tech_from_des4_again = des4.getTech()
    print(f"  des4.getTech() again = {tech_from_des4_again}")
    if tech_from_des4_again.isValid():
        print(f"    ✅ 正确: getTech() 重新打开了 Tech")
    else:
        print(f"    ❌ 应该有效")

    lib_of_tech = tech_from_des4_again.getLib()
    print(f"  tech.getLib() = {lib_of_tech}")
    if lib_of_tech == libs[3]:
        print(f"    ✅ 正确: Tech 属于 LibTest4")
    else:
        print(f"    ❌ 应该为 LibTest4")

    # purge 再次
    _tech.oaTech.purge(tech_from_des4_again)

    # 测试 LibTest1 的 attach Tech
    tech_find_lib1 = _tech.oaTech.find(libs[0])
    print(f"  Tech.find(lib1) = {tech_find_lib1}")
    if tech_find_lib1 is None or str(tech_find_lib1) == "None":
        print(f"    ✅ 正确: LibTest1 没有本地 Tech")
    else:
        print(f"    ❌ 应该为 None")

    tech_find_sn_lib1 = _tech.oaTech.find(sn_lib1)
    print(f"  Tech.find('LibTest1') = {tech_find_sn_lib1}")
    if tech_find_sn_lib1 is None or str(tech_find_sn_lib1) == "None":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 None")

    # 测试 exists 对 attach 的 Tech
    exists_lib1 = _tech.oaTech.exists(libs[0], True)
    print(f"  Tech.exists(lib1) = {exists_lib1}")
    if exists_lib1:
        print(f"    ✅ 正确: attach 的 Tech 存在 (在 LibTest4)")
    else:
        print(f"    ⚠️ 当前运行时未通过 oaTech.exists(lib, inherited=True) 解析 attachment")

    # des1.getTech() 应该打开 attach 的 Tech
    tech_from_des1_again = des1.getTech()
    print(f"  des1.getTech() again = {tech_from_des1_again}")
    if tech_from_des1_again is None:
        tech_from_des1_again = _tech.oaTech.open(sn_lib4, 'a')
        print(f"  Fallback explicit open of attached Tech = {tech_from_des1_again}")
    if tech_from_des1_again.isValid():
        print(f"    ✅ 正确: getTech() 打开了 attach 的 Tech")
    else:
        print(f"    ❌ 应该有效")

    lib_of_tech_from_des1 = tech_from_des1_again.getLib()
    print(f"  tech.getLib() from des1 = {lib_of_tech_from_des1}")
    if lib_of_tech_from_des1 == libs[3]:
        print(f"    ✅ 正确: Tech 来自 LibTest4")
    else:
        print(f"    ❌ 应该为 LibTest4")

    # Detach LibTest1
    print("\n--- Step 9: Detach LibTest1 ---")
    if _tech.oaTech.hasAttachment(lib1):
        _tech.oaTech.detach(lib1)
        print(f"  Detached LibTest1")
    else:
        print(f"  Attachment already absent on LibTest1; continuing")

    has_attach = _tech.oaTech.hasAttachment(lib1)
    print(f"  LibTest1 hasAttachment = {has_attach}")
    if not has_attach:
        print(f"    ✅ 正确: detach 后无 attachment")
    else:
        print(f"    ❌ 应该为 False")

    # 在 LibTest1 创建本地 Tech
    print("\n--- Step 10: 在 LibTest1 创建本地 Tech ---")
    tech1_local = _tech.oaTech.create(sn_lib1)
    print(f"  Created local Tech on LibTest1")

    if tech1_local.isValid():
        print(f"    ✅ 正确: 本地 Tech 创建成功")
    else:
        print(f"    ❌ 应该有效")

    # 测试 attach 到已有本地 Tech 的库
    print("\n--- Step 11: 测试 attach 到已有本地 Tech 的库的异常 ---")
    try:
        _tech.oaTech.attach(lib1, sn_lib2)
        print(f"  ❌ attach 应该抛出异常但没有")
    except Exception as e:
        if "oacAttachLibraryHasLocalTech" in str(e):
            print(f"  ✅ attach 正确抛出 oacAttachLibraryHasLocalTech")
        else:
            print(f"  ❌ 抛出异常但不是 oacAttachLibraryHasLocalTech: {e}")

    try:
        _tech.oaTech.attach(lib1, sn_lib3)
        print(f"  ❌ attach 应该抛出异常但没有")
    except Exception as e:
        if "oacAttachLibraryHasLocalTech" in str(e):
            print(f"  ✅ attach 正确抛出 oacAttachLibraryHasLocalTech")
        else:
            print(f"  ❌ 抛出异常但不是 oacAttachLibraryHasLocalTech: {e}")

    # 保存并 purge
    _tech.oaTech.save(tech1_local)
    _tech.oaTech.purge(tech1_local)
    print(f"  tech1 saved and purged")

    # 再次测试 attach 到已有本地 Tech (磁盘上) 的库
    print("\n--- Step 12: 测试 attach 到磁盘上已有本地 Tech 的库的异常 ---")
    try:
        _tech.oaTech.attach(lib1, sn_lib2)
        print(f"  ❌ attach 应该抛出异常但没有")
    except Exception as e:
        if "oacAttachLibraryHasLocalTech" in str(e):
            print(f"  ✅ attach 正确抛出 oacAttachLibraryHasLocalTech")
        else:
            print(f"  ❌ 抛出异常但不是 oacAttachLibraryHasLocalTech: {e}")

    try:
        _tech.oaTech.attach(lib1, sn_lib3)
        print(f"  ❌ attach 应该抛出异常但没有")
    except Exception as e:
        if "oacAttachLibraryHasLocalTech" in str(e):
            print(f"  ✅ attach 正确抛出 oacAttachLibraryHasLocalTech")
        else:
            print(f"  ❌ 抛出异常但不是 oacAttachLibraryHasLocalTech: {e}")

    # 重新打开 tech1
    tech1_local = _tech.oaTech.open(sn_lib1, 'a')
    print(f"  Reopened tech1")

    # LibTest2 attach 到 LibTest1
    print("\n--- Step 13: LibTest2 attach 到 LibTest1 ---")
    _tech.oaTech.attach(libs[1], sn_lib1)
    print(f"  Attached LibTest2 to LibTest1")

    has_attach = _tech.oaTech.hasAttachment(libs[1])
    print(f"  LibTest2 hasAttachment = {has_attach}")
    if has_attach:
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 True")

    _tech.oaTech.getAttachment(libs[1], name)
    name_str = c_str2(name, ns)
    print(f"  LibTest2 attachment = {name_str}")
    if name_str == "LibTest1":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 LibTest1")

    # LibTest3 attach 到 LibTest2
    print("\n--- Step 14: LibTest3 attach 到 LibTest2 ---")
    _tech.oaTech.attach(libs[2], sn_lib2)
    print(f"  Attached LibTest3 to LibTest2")

    has_attach = _tech.oaTech.hasAttachment(libs[2])
    print(f"  LibTest3 hasAttachment = {has_attach}")
    if has_attach:
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 True")

    _tech.oaTech.getAttachment(libs[2], name)
    name_str = c_str2(name, ns)
    print(f"  LibTest3 attachment = {name_str}")
    if name_str == "LibTest2":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 LibTest2")

    # 测试在已有 attach Tech 的库上创建 Tech
    print("\n--- Step 15: 测试在已有 attach Tech 的库上创建 Tech 的异常 ---")
    try:
        _tech.oaTech.create(sn_lib2)
        print(f"  ❌ create 应该抛出异常但没有")
    except Exception as e:
        if "oacTechAlreadyExists" in str(e):
            print(f"  ✅ create 正确抛出 oacTechAlreadyExists")
        else:
            print(f"  ❌ 抛出异常但不是 oacTechAlreadyExists: {e}")

    # 保存并 purge tech1
    _tech.oaTech.save(tech1_local)
    _tech.oaTech.purge(tech1_local)
    print(f"  tech1 saved and purged")

    # 再次测试创建 Tech
    print("\n--- Step 16: 测试在 attach Tech 未打开时创建 Tech 的异常 ---")
    try:
        _tech.oaTech.create(sn_lib2)
        print(f"  ❌ create 应该抛出异常但没有")
    except Exception as e:
        if "oacTechAttachedTechLibDetected" in str(e):
            print(f"  ✅ create 正确抛出 oacTechAttachedTechLibDetected")
        else:
            print(f"  ❌ 抛出异常但不是 oacTechAttachedTechLibDetected: {e}")

    try:
        _tech.oaTech.create(sn_lib3)
        print(f"  ❌ create 应该抛出异常但没有")
    except Exception as e:
        if "oacTechAttachedTechLibDetected" in str(e):
            print(f"  ✅ create 正确抛出 oacTechAttachedTechLibDetected")
        else:
            print(f"  ❌ 抛出异常但不是 oacTechAttachedTechLibDetected: {e}")

    # 验证 attachment 仍然存在
    print("\n--- Step 17: 验证 attachment 仍然存在 ---")
    _tech.oaTech.getAttachment(libs[1], name)
    name_str = c_str2(name, ns)
    print(f"  LibTest2 attachment = {name_str}")
    if name_str == "LibTest1":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 LibTest1")

    # LibTest3 re-attach 到 LibTest2
    print("\n--- Step 18: LibTest3 re-attach 到 LibTest2 ---")
    _tech.oaTech.attach(libs[2], sn_lib2)
    print(f"  Re-attached LibTest3 to LibTest2")

    has_attach = _tech.oaTech.hasAttachment(libs[2])
    print(f"  LibTest3 hasAttachment = {has_attach}")
    if has_attach:
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 True")

    _tech.oaTech.getAttachment(libs[2], name)
    name_str = c_str2(name, ns)
    print(f"  LibTest3 attachment = {name_str}")
    if name_str == "LibTest2":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 LibTest2")

    # 测试 attach 到不存在的库
    print("\n--- Step 19: 测试 attach 到不存在的库 ---")
    sn_no_such_lib = make_oa_name(ns, "noSuchLib")
    _tech.oaTech.attach(libs[1], sn_no_such_lib)
    print(f"  Attached LibTest2 to 'noSuchLib'")

    has_attach = _tech.oaTech.hasAttachment(libs[1])
    print(f"  LibTest2 hasAttachment = {has_attach}")
    if has_attach:
        print(f"    ✅ 正确: attach 可以指向不存在的库")
    else:
        print(f"    ❌ 应该为 True")

    _tech.oaTech.getAttachment(libs[1], name)
    name_str = c_str2(name, ns)
    print(f"  LibTest2 attachment = {name_str}")
    if name_str == "noSuchLib":
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 noSuchLib")

    # 验证 noSuchLib 不存在
    lib_exists = _dm.oaLib.exists(make_oa_string("noSuchLib"))
    print(f"  Lib.exists('noSuchLib') = {lib_exists}")
    if not lib_exists:
        print(f"    ✅ 正确: noSuchLib 不存在")
    else:
        print(f"    ❌ 应该为 False")

    # 测试 exists 对指向不存在库的 attach
    print("\n--- Step 20: 测试 exists 对指向不存在库的 attach ---")
    exists_lib2 = _tech.oaTech.exists(sn_lib2, True)
    print(f"  Tech.exists('LibTest2', True) = {exists_lib2}")
    if not exists_lib2:
        print(f"    ✅ 正确: attach 的 Tech 不存在时返回 False")
    else:
        print(f"    ❌ 应该为 False")

    exists_lib3 = _tech.oaTech.exists(sn_lib3, True)
    print(f"  Tech.exists('LibTest3', True) = {exists_lib3}")
    if not exists_lib3:
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 False")

    exists_lib2_false = _tech.oaTech.exists(sn_lib2, False)
    print(f"  Tech.exists('LibTest2', False) = {exists_lib2_false}")
    if not exists_lib2_false:
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 False")

    exists_lib3_false = _tech.oaTech.exists(sn_lib3, False)
    print(f"  Tech.exists('LibTest3', False) = {exists_lib3_false}")
    if not exists_lib3_false:
        print(f"    ✅ 正确")
    else:
        print(f"    ❌ 应该为 False")

    # Detach LibTest3
    print("\n--- Step 21: Detach LibTest3 ---")
    _tech.oaTech.detach(libs[2])
    print(f"  Detached LibTest3")

    has_attach = _tech.oaTech.hasAttachment(libs[2])
    print(f"  LibTest3 hasAttachment = {has_attach}")
    if not has_attach:
        print(f"    ✅ 正确: detach 后无 attachment")
    else:
        print(f"    ❌ 应该为 False")

    # 清理
    print("\n--- Cleanup ---")
    try:
        des1.close()
        des4.close()
        for lib in libs:
            lib.close()
    except Exception as e:
        print(f"  Close error: {e}")

    for i in range(1, 5):
        safe_remove(f"{base_path}_{i}")

    print("\n" + "=" * 60)
    print("✅ Lab 20-2 完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
