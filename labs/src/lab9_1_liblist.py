#!/usr/bin/env python3
"""
oapy Lab 9-1: LibList — 库定义列表操作

演示 oaLibDefList / oaLibDef / oaLibDefListMem 的创建、读取、修改

运行: cd /workarea/ai/openclaw/oapy/labs && bash run_lab.sh src/lab9_1_liblist.py
"""
import os, shutil
from utils import init_oa, c_str, make_oa_string, make_oa_name, get_namespace
from oapy._oa import _dm, _base


def get_lib(sc_name, str_path):
    """Open or create a lib at the given path."""
    ns = get_namespace("native")
    str_name = make_oa_string()
    sc_name.get(ns, str_name)
    name = c_str(str_name)
    print(f"    get_lib({name}, {str_path})")

    lib = _dm.oaLib.find(sc_name)
    print(f"    find -> {lib}")
    if lib is not None:
        status = "was already open"
    else:
        # Convert Python str to oaString for exists()
        oa_path = make_oa_string(str_path)
        lib_exists = _dm.oaLib.exists(oa_path)
        print(f"    exists({c_str(oa_path)}) -> {lib_exists}")
        if lib_exists:
            # open needs: scName, path, path, mode
            lib = _dm.oaLib.open(sc_name, make_oa_string(str_path), make_oa_string(str_path),
                                _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode))
            print(f"    open -> {lib}")
            status = "had to be opened"
        else:
            os.makedirs(str_path, exist_ok=True)
            lm = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
            lib = _dm.oaLib.create(sc_name, make_oa_string(str_path), lm,
                                   make_oa_string("oaDMFileSys"), _dm.oaDMAttrArray(0))
            print(f"    create -> {lib}")
            status = "had to be created"

    full_path = make_oa_string()
    lib.getFullPath(full_path)
    print(f"  Lib {name} at {c_str(full_path)} {status}")
    return lib


def delete_old_path(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def ensure_readable_lib_defs(path):
    """Create a minimal default lib.defs when OA reports a path that is absent."""
    if path and os.path.isfile(path) and os.access(path, os.R_OK):
        return

    defs_path = path or "lib.defs"
    parent = os.path.dirname(defs_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(defs_path, "w") as f:
        f.write("DEFINE LibA ../data/LibA\n")
    print(f"  Created readable lib defs at {defs_path}")


def main():
    print("=" * 60)
    print("Lab 9-1: LibList")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    # ── 1. Get default lib.defs path ──
    print("\n--- Step 1: Get default lib.defs path ---")
    str_path_lib_defs = make_oa_string()
    _dm.oaLibDefList.getDefaultPath(str_path_lib_defs)
    path_str = c_str(str_path_lib_defs)
    no_lib_defs = str_path_lib_defs.isEmpty()

    if no_lib_defs:
        print("  ***Must define a default library definition list file.")
        print("  Creating a minimal lib.defs for testing...")
        defs_path = os.path.join(os.getcwd(), "lib.defs")
        with open(defs_path, "w") as f:
            f.write("DEFINE LibA ../data/LibA\n")
        str_path_lib_defs = make_oa_string(defs_path)
        path_str = defs_path
        print(f"  Created lib.defs at {defs_path}")
    else:
        ensure_readable_lib_defs(path_str)

    print(f"  Default lib.defs path: {path_str}")

    # ── 2. Top list (should be invalid before openLibs) ──
    print("\n--- Step 2: TopList before openLibs ---")
    ldl = _dm.oaLibDefList.getTopList()
    assert ldl is None or not ldl.isValid(), "TopList should be invalid before openLibs"
    print(f"  [PASS] TopList is invalid before openLibs")

    # ── 3. Read lib.defs ──
    print("\n--- Step 3: Read lib.defs ---")
    ldl = _dm.oaLibDefList.get(str_path_lib_defs, 'r')
    assert ldl.isValid(), "LibDefList should be valid after get()"
    print(f"  [PASS] LibDefList is valid after get()")

    # TopList still not valid
    top2 = _dm.oaLibDefList.getTopList()
    assert top2 is None or not top2.isValid()
    print(f"  [PASS] TopList still invalid after get()")

    # ── 4. Get first member ──
    print("\n--- Step 4: Get first LibDef member ---")
    members = ldl.getMembers()
    ldl_mems = _dm.oaIter_oaLibDefListMem(members)
    ld_mem = ldl_mems.getNext()
    assert ld_mem is not None, "Should have at least one member"
    
    # Downcast from oaLibDefListMem to oaLibDef (downcast)
    ld = _dm.oaLibDef.downcast(ld_mem)
    assert ld is not None, "Downcast should succeed"

    str_path = make_oa_string()
    sc_name_lib = _base.oaScalarName()
    ld.getLibPath(str_path)
    ld.getLibName(sc_name_lib)

    lib_path = c_str(str_path)
    lib_name = c_str(sc_name_lib.get(ns, make_oa_string())) if False else ""
    # Get name properly
    name_str = make_oa_string()
    sc_name_lib.get(ns, name_str)
    lib_name = c_str(name_str)

    print(f"  First member: {lib_name} -> {lib_path}")

    # ── 5. Create/open lib ──
    print("\n--- Step 5: Create/open Lib ---")
    delete_old_path(lib_path)
    lib = get_lib(sc_name_lib, lib_path)
    lib.close()
    lib = get_lib(sc_name_lib, lib_path)
    lib = get_lib(sc_name_lib, lib_path)
    print(f"  [PASS] Lib create/open/find cycle works")

    # ── 6. Add a new LibDef ──
    print("\n--- Step 6: Add new LibDef ---")
    n_members_before = ldl.getMembers().getCount()
    
    new_name = _base.oaScalarName(ns, "myName")
    new_path = make_oa_string("/tmp/otherPath")
    _dm.oaLibDef.create(ldl, new_name, new_path)

    n_members = ldl.getMembers().getCount()
    assert n_members == n_members_before + 1, f"Expected {n_members_before + 1} members, got {n_members}"
    print(f"  [PASS] nMembers = {n_members} (was {n_members_before}, added 1)")

    # ── 7. Save as lib.defs2 ──
    print("\n--- Step 7: Save as lib.defs2 ---")
    ldl.saveAs(make_oa_string("lib.defs2"))
    assert os.path.exists("lib.defs2"), "lib.defs2 should exist"
    print(f"  [PASS] Saved lib.defs2")
    with open("lib.defs2") as f:
        print(f"  Content:\n{f.read()}")

    # ── 8. TopList still invalid ──
    print("\n--- Step 8: TopList at end ---")
    ldl_top = _dm.oaLibDefList.getTopList()
    assert ldl_top is None or not ldl_top.isValid()
    print(f"  [PASS] TopList still invalid")

    # ── 9. openLibs sets TopList ──
    print("\n--- Step 9: openLibs ---")
    _dm.oaLibDefList.openLibs()
    ldl_top = _dm.oaLibDefList.getTopList()
    assert ldl_top.isValid(), "TopList should be valid after openLibs"
    print(f"  [PASS] TopList is valid after openLibs")

    n_members = ldl_top.getMembers().getCount()
    assert n_members > 0, f"Expected at least 1 member after openLibs, got {n_members}"
    print(f"  [PASS] nMembers = {n_members}")

    # ── Cleanup ──
    print("\n--- Cleanup ---")
    for f in ["lib.defs", "lib.defs2"]:
        if os.path.exists(f):
            os.remove(f)
    delete_old_path(lib_path)
    print("  Cleaned up")

    print("\n" + "=" * 60)
    print("✅ Lab 9-1 (LibList) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
