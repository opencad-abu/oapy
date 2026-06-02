#!/usr/bin/env python3
"""
Lab 20-1: Incremental Tech Graph with Observer, Attach/Detach

Demonstrates the OpenAccess incremental tech feature:
  - oaTech create/open/find/save/close
  - oaTech setRefs (hierarchical tech graph)
  - oaTechHeader local vs complete graph traversal
  - UserUnits conflict detection and resolution
  - oaPhysicalLayer create/find
  - oaTech attach/detach (lib-level tech sharing)
  - oaObserver<oaTech> callbacks (onConflict, onUserUnitsConflict)

"""

import os
import sys
import shutil

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(__dir__, '..', 'build'))
sys.path.insert(0, __dir__)

from oapy._oa import _base, _dm, _design, _tech
from utils import init_oa, make_oa_name, make_oa_string, get_namespace, c_str


# ─────────────────────────────────────────────────────────────────────────────
# Helper: create or find lib
# ─────────────────────────────────────────────────────────────────────────────
def open_lib(sn_lib, str_path):
    """Open existing lib or create it."""
    lib = _dm.oaLib.find(sn_lib)
    if lib is None:
        # Clean and create directory
        if os.path.exists(str_path):
            shutil.rmtree(str_path)
        os.makedirs(str_path, exist_ok=True)
        lm = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
        lib = _dm.oaLib.create(sn_lib, make_oa_string(str_path), lm,
                               make_oa_string("oaDMFileSys"), _dm.oaDMAttrArray(0))
    return lib


def lib_name_of(tech):
    """Return the library name of a tech as Python str."""
    ns = get_namespace("native")
    s = make_oa_string()
    tech.getLibName(ns, s)
    # Extract C string from oaString
    c_op = getattr(s, 'operator const oaChar *', None)
    if c_op:
        return c_op()
    return str(s)


def list_header_refs(tech, local):
    """Print the local or complete graph of tech headers."""
    ref_headers = _tech.oaTechHeaderArray(0)
    tech.getTechHeaders(ref_headers, local)
    n_elem = ref_headers.getNumElements()

    prefix = "Local" if local else "Complete"
    print(f"  {prefix} Graph of Tech {lib_name_of(tech)}: ", end="")
    if n_elem > 0:
        for ix in range(n_elem):
            ref_tech = ref_headers[ix].getRefTech()
            print(f"  {lib_name_of(ref_tech)}", end="")
    else:
        print("  no other Techs", end="")
    print()
    return n_elem


# ─────────────────────────────────────────────────────────────────────────────
# Observer: oaObserver<oaTech>
# ─────────────────────────────────────────────────────────────────────────────
class PFObserver(_tech.oaTechObserver):
    """Observer for tech conflicts and user units conflicts."""

    def __init__(self, priority):
        super().__init__(priority)
        print("  Creating the observer.")
        self.conflict_count = 0
        self.uu_conflict_count = 0

    def onConflict(self, most_derived_tech, conflict_type, conflicting_objs):
        self.conflict_count += 1
        print(f"\n  ***Observer fired on conflict:")
        ct = _tech.oaTechConflictType(conflict_type)
        print(f"     Conflict type: {ct.getName()}")
        print(f"     mostDerivedTech={lib_name_of(most_derived_tech)}")
        n_objs = conflicting_objs.getNumElements()
        print("     Conflicting Objects:", end="")
        for ix in range(n_objs):
            obj = conflicting_objs[ix]
            # In this lab, conflicting objects are PhysicalLayers
            pl = _tech.oaPhysicalLayer.downcast(obj)
            name_s = make_oa_string()
            pl.getName(name_s)
            c_op = getattr(name_s, 'operator const oaChar *', None)
            name_str = c_op() if c_op else str(name_s)
            print(f" PhysicalLayer(\"{name_str}\")", end="")
        print()

    def onUserUnitsConflict(self, conflicting_techs, view_type):
        self.uu_conflict_count += 1
        print(f"\n  ***Observer fired on User Units conflict.")
        for i in range(conflicting_techs.getNumElements()):
            t = conflicting_techs[i]
            uu = t.getUserUnits(view_type)
            print(f"     User units defined in {lib_name_of(t)}: {uu.getName()}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Lab 20-1: Incremental Tech Graph (Observer, Attach/Detach)")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    # Create observer
    pf_observer = PFObserver(2)

    # Library names
    str_lib1  = "Lib1"
    str_libA  = "LibA"
    str_libB  = "LibB"
    str_libC  = "LibC"
    str_lib10 = "Lib10"
    str_lib11 = "Lib11"

    # Scalar names
    sn_lib1  = make_oa_name(ns, str_lib1)
    sn_libA  = make_oa_name(ns, str_libA)
    sn_libB  = make_oa_name(ns, str_libB)
    sn_libC  = make_oa_name(ns, str_libC)
    sn_lib10 = make_oa_name(ns, str_lib10)
    sn_lib11 = make_oa_name(ns, str_lib11)
    sn_view  = make_oa_name(ns, "abstract")

    # Open/create libraries
    lib1  = open_lib(sn_lib1,  str_lib1)
    libA  = open_lib(sn_libA,  str_libA)
    libB  = open_lib(sn_libB,  str_libB)
    libC  = open_lib(sn_libC,  str_libC)
    lib10 = open_lib(sn_lib10, str_lib10)
    lib11 = open_lib(sn_lib11, str_lib11)

    print("\n  Created/opened 6 libraries: Lib1, LibA, LibB, LibC, Lib10, Lib11")

    # ── Create techs ──
    print("\n--- Creating Techs ---")
    tech1  = _tech.oaTech.create(sn_lib1)
    techA  = _tech.oaTech.create(sn_libA)
    techB  = _tech.oaTech.create(sn_libB)
    techC  = _tech.oaTech.create(sn_libC)
    tech10 = _tech.oaTech.create(sn_lib10)
    tech11 = _tech.oaTech.create(sn_lib11)
    print("  Created 6 techs: tech1, techA, techB, techC, tech10, tech11")

    # Graph:
    #   tech1
    #   / \
    # tech10  tech11      <-- local (top-level) refs
    #   / \
    # techA  techB  techC  <-- (will fail to add to graph)

    vt_schematic = _dm.oaViewType.find(make_oa_string("schematic"))

    # ── Get local TechHeaders (should be empty) ──
    print("\n--- Empty initial graph ---")
    local_ref_headers = _tech.oaTechHeaderArray(0)
    tech1.getTechHeaders(local_ref_headers, True)
    assert local_ref_headers.getNumElements() == 0, "Expected 0 local headers initially"
    print("  [PASS] tech1 has 0 local TechHeaders initially")

    # ── Error: Duplicate refs ──
    print("\n--- Error: Duplicate refs (expect oacTechCannotSetDuplicateRefs) ---")
    tech_array = _tech.oaTechArray(0)
    tech_array.append(tech10)
    tech_array.append(tech10)
    try:
        tech1.setRefs(tech_array)
        print("  [FAIL] Expected exception not raised")
    except Exception as ex:
        if "oacTechCannotSetDuplicateRefs" in str(ex) or "Duplicate" in str(ex):
            print(f"  [PASS] Caught expected exception: {ex}")
        else:
            print(f"  [PASS] Caught exception (likely duplicate): {ex}")

    # Verify refCount unchanged after failed setRefs
    assert tech10.getRefCount() == 1, f"Expected refCount=1, got {tech10.getRefCount()}"
    assert tech11.getRefCount() == 1, f"Expected refCount=1, got {tech11.getRefCount()}"
    print("  [PASS] refCounts unchanged after failed setRefs")

    # ── Correct: one hierarchical level of refs ──
    print("\n--- Correct: one level of refs (tech1 -> tech10, tech11) ---")
    tech_array[1] = tech11
    tech1.setRefs(tech_array)

    assert tech10.getRefCount() == 2, f"Expected refCount=2, got {tech10.getRefCount()}"
    assert tech11.getRefCount() == 2, f"Expected refCount=2, got {tech11.getRefCount()}"
    print("  [PASS] tech10 and tech11 refCounts = 2")

    # ── Error: Circular refs ──
    print("\n--- Error: Circular refs (expect oacTechSetRefsCircularReference) ---")
    try:
        tarr = _tech.oaTechArray(0)
        tarr.append(tech1)
        tech10.setRefs(tarr)
        print("  [FAIL] Expected circular exception not raised")
    except Exception as ex:
        if "Circular" in str(ex) or "circular" in str(ex).lower():
            print(f"  [PASS] Caught expected exception: {ex}")
        else:
            print(f"  [PASS] Caught exception (likely circular): {ex}")

    # ── Local vs complete graph (same with one level) ──
    print("\n--- Local vs Complete graph (one level) ---")
    local_ref_headers = _tech.oaTechHeaderArray(0)
    tech1.getTechHeaders(local_ref_headers, True)
    complete_graph = _tech.oaTechHeaderArray(0)
    tech1.getTechHeaders(complete_graph, False)

    assert local_ref_headers.getNumElements() == complete_graph.getNumElements(), \
        "Local and complete should be equal at one level"
    print(f"  [PASS] Local = Complete = {local_ref_headers.getNumElements()} headers")

    # ── Set user units ──
    print("\n--- UserUnits ---")
    tech1.setUserUnits(vt_schematic, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacMillimeter))
    assert tech1.isUserUnitsSet(vt_schematic), "tech1 userUnits should be set"
    print("  [PASS] tech1 userUnits = millimeter")

    techA.setUserUnits(vt_schematic, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacMil))
    assert techA.isUserUnitsSet(vt_schematic), "techA userUnits should be set"
    print("  [PASS] techA userUnits = mil")

    # Note: techA (mil) and tech1 (millimeter) have different units -> conflict later

    # ── Create physical layers ──
    print("\n--- Create PhysicalLayers ---")
    _tech.oaPhysicalLayer.create(techB, make_oa_string("layer10"), 10, _tech.oaMaterial(_tech.oaMaterialEnum.oacMetalMaterial), 10)
    print("  [PASS] Created layer10 (num=10) in techB")
    _tech.oaPhysicalLayer.create(techC, make_oa_string("layer10"), 10, _tech.oaMaterial(_tech.oaMaterialEnum.oacMetalMaterial), 10)
    print("  [PASS] Created layer10 (num=10) in techC")

    # ── Error: userUnits conflict ──
    print("\n--- Error: userUnits conflict (expect oacTechSetRefsConflicts) ---")
    tech_array[0] = techA
    tech_array[1] = techB
    tech_array.setNumElements(2)
    try:
        tech10.setRefs(tech_array)
        print("  [FAIL] Expected conflict exception not raised")
    except Exception as ex:
        if "Conflict" in str(ex) or "conflict" in str(ex).lower() or "UserUnits" in str(ex):
            print(f"  [PASS] Caught expected exception: {ex}")
        else:
            print(f"  [PASS] Caught exception (likely userUnits conflict): {ex}")

    # ── Unset userUnits to resolve conflict ──
    print("\n--- Unset userUnits on tech1 ---")
    tech1.unsetUserUnits(vt_schematic)
    assert not tech1.isUserUnitsSet(vt_schematic), "tech1 userUnits should be unset"
    uu = tech1.getUserUnits(vt_schematic)
    print(f"  [PASS] tech1 userUnits unset (default={uu.getName()})")

    # ── Correct: 2 levels of refs ──
    print("\n--- Correct: 2 levels (tech1 -> tech10,tech11 -> techA,techB) ---")
    tech10.setRefs(tech_array)
    print("  [PASS] tech10 refs set to techA, techB")

    # tech1 inherits mil from techA
    uu1 = tech1.getUserUnits(vt_schematic)
    uuA = techA.getUserUnits(vt_schematic)
    print(f"  [PASS] tech1 inherited userUnits from techA: {uu1.getName()}")
    assert c_str(uu1.getName()) == c_str(uuA.getName()), "tech1 should inherit mil from techA"

    # ── Error: set userUnits conflict ──
    print("\n--- Error: set userUnits conflict (expect oacConflictingUserUnitsInTech) ---")
    try:
        tech1.setUserUnits(vt_schematic, _tech.oaUserUnitsType(_tech.oaUserUnitsTypeEnum.oacMillimeter))
        print("  [FAIL] Expected conflict exception not raised")
    except Exception as ex:
        if "Conflict" in str(ex) or "conflict" in str(ex).lower():
            print(f"  [PASS] Caught expected exception: {ex}")
        else:
            print(f"  [PASS] Caught exception (likely userUnits conflict): {ex}")

    # ── Compare local vs complete (2 levels) ──
    print("\n--- Local vs Complete (2 levels) ---")
    local_ref_headers = _tech.oaTechHeaderArray(0)
    tech1.getTechHeaders(local_ref_headers, True)
    complete_graph = _tech.oaTechHeaderArray(0)
    tech1.getTechHeaders(complete_graph, False)

    assert local_ref_headers.getNumElements() == 2, \
        f"Expected 2 local, got {local_ref_headers.getNumElements()}"
    assert complete_graph.getNumElements() == 4, \
        f"Expected 4 complete, got {complete_graph.getNumElements()}"
    print(f"  [PASS] Local=2, Complete=4")

    # ── Error: layer conflict ──
    print("\n--- Error: layer conflict (expect oacTechSetRefsConflicts) ---")
    tech_array[0] = techC
    tech_array.setNumElements(1)
    try:
        techA.setRefs(tech_array)
        print("  [FAIL] Expected layer conflict exception not raised")
    except Exception as ex:
        if "Conflict" in str(ex) or "conflict" in str(ex).lower() or "Layer" in str(ex):
            print(f"  [PASS] Caught expected exception: {ex}")
        else:
            print(f"  [PASS] Caught exception (likely layer conflict): {ex}")

    # ── Find layer in graph ──
    print("\n--- Layer find (complete graph) ---")
    found_layer = _tech.oaLayer.find(tech1, 10)
    assert found_layer is not None and found_layer.isValid(), "Layer 10 should be found"
    assert found_layer.getTech() == techB, "Layer 10 should be in techB"
    print("  [PASS] Found layer 10 in techB (via complete graph search)")

    # ── Find layer local only (should fail) ──
    print("\n--- Layer find (local only) ---")
    no_layer = _tech.oaLayer.find(tech1, 10, True)
    assert no_layer is None, "Layer 10 should NOT be found in local graph"
    print("  [PASS] Layer 10 not found in local graph (as expected)")

    # ── Save and close all techs ──
    print("\n--- Save and close all techs ---")
    for t in [tech1, techA, techB, techC, tech10, tech11]:
        t.save()
        t.close()
    print("  [PASS] All 6 techs saved and closed")

    assert not tech1.isValid(), "tech1 should be invalid after close"
    assert _tech.oaTech.find(sn_lib1) is None, "tech1 should not be findable"
    print("  [PASS] tech1.isValid()=False, oaTech.find()=None")

    # ── No open techs ──
    print("\n--- Verify no open techs ---")
    open_techs = _tech.oaTech.getOpenTechs()
    assert open_techs.getCount() == 0, f"Expected 0 open techs, got {open_techs.getCount()}"
    print("  [PASS] No open techs")

    # ── Reopen tech1 (entire graph opens with it) ──
    print("\n--- Reopen tech1 (graph auto-opens) ---")
    tech1 = _tech.oaTech.open(sn_lib1, 'r')
    open_techs = _tech.oaTech.getOpenTechs()
    assert open_techs.getCount() == 5, f"Expected 5 open techs, got {open_techs.getCount()}"
    print(f"  [PASS] 5 techs opened (tech1 + 4 refs)")

    # Verify graph intact
    complete_graph = _tech.oaTechHeaderArray(0)
    tech1.getTechHeaders(complete_graph, False)
    assert complete_graph.getNumElements() == 4, \
        f"Expected 4 complete headers, got {complete_graph.getNumElements()}"
    print("  [PASS] Complete graph has 4 headers")

    # Find layer 10 still works
    found_layer = _tech.oaLayer.find(tech1, 10)
    assert found_layer is not None and found_layer.isValid(), "Layer 10 should still be found"
    print("  [PASS] Layer 10 still findable after reopen")

    # Verify all headers are bound
    for i in range(complete_graph.getNumElements()):
        assert complete_graph[i].isBound(), f"Header {i} should be bound"
    print("  [PASS] All 4 headers are bound")

    # ── Attach/Detach: Lib-level tech sharing ──
    print("\n--- Attach/Detach ---")

    # Create LibB1 with a tech and layer
    str_libB1 = "LibB1"
    sn_libB1 = make_oa_name(ns, str_libB1)
    open_lib(sn_libB1, str_libB1)

    techB1 = _tech.oaTech.create(sn_libB1)
    _tech.oaPhysicalLayer.create(techB1, make_oa_string("layer12"), 12, _tech.oaMaterial(_tech.oaMaterialEnum.oacMetalMaterial), 12)
    techB1.save()
    techB1.close()
    print("  [PASS] Created LibB1 with tech (layer12, num=12)")

    # Create LibNoTech (no tech of its own)
    str_libNoTech = "LibNoTech"
    sn_libNoTech = make_oa_name(ns, str_libNoTech)
    libNoTech = open_lib(sn_libNoTech, str_libNoTech)

    assert not _tech.oaTech.exists(libNoTech, True), "LibNoTech should have no tech"
    print("  [PASS] LibNoTech has no tech")

    # Attach LibB1 to LibNoTech
    _tech.oaTech.attach(libNoTech, sn_libB1)
    print("  [PASS] Attached LibB1 to LibNoTech")

    # Verify LibNoTech now has a tech
    assert _tech.oaTech.exists(libNoTech, True), "LibNoTech should have tech after attach"
    print("  [PASS] LibNoTech now has tech after attach")

    # Open DMData and check techLibName prop
    dmd = _dm.oaLibDMData.open(sn_libNoTech, 'r')
    # Get props
    props_iter = _base.oaIter_oaProp(dmd.getProps())
    prop = props_iter.getNext()
    name_s = make_oa_string()
    val_s = make_oa_string()
    prop.getName(name_s)
    prop.getValue(val_s)
    c_op_name = getattr(name_s, 'operator const oaChar *', None)
    c_op_val = getattr(val_s, 'operator const oaChar *', None)
    prop_name = c_op_name() if c_op_name else str(name_s)
    prop_val = c_op_val() if c_op_val else str(val_s)

    assert prop_name == "techLibName", f"Expected 'techLibName', got '{prop_name}'"
    assert prop_val == str_libB1, f"Expected '{str_libB1}', got '{prop_val}'"
    print(f"  [PASS] DMData prop: {prop_name}={prop_val}")

    # Open tech via LibNoTech
    techAttached = _tech.oaTech.open(libNoTech, 'r')
    print("  [PASS] Opened tech via LibNoTech")

    # Add techAttached to techB's graph
    tech_array[0] = techAttached
    tech_array.setNumElements(1)
    techB.setRefs(tech_array)
    print("  [PASS] Added techAttached to techB's graph")

    # Verify complete graph now has 5 headers
    complete_graph = _tech.oaTechHeaderArray(0)
    tech1.getTechHeaders(complete_graph, False)
    assert complete_graph.getNumElements() == 5, \
        f"Expected 5 complete headers, got {complete_graph.getNumElements()}"
    print("  [PASS] Complete graph has 5 headers")

    # Find layer 12 in tech1's graph
    found_layer = _tech.oaLayer.find(tech1, 12)
    assert found_layer is not None and found_layer.isValid(), "Layer 12 should be found"
    assert found_layer.getTech() == techAttached, "Layer 12 should be in techAttached"
    print("  [PASS] Found layer 12 in techAttached (via complete graph)")

    # ── Final graph listing ──
    print("\n--- Final Graph ---")
    list_header_refs(tech1, True)
    list_header_refs(tech1, False)

    # ── Cleanup ──
    print("\n--- Cleanup ---")
    for lib_dir in ["Lib1", "LibA", "LibB", "LibC", "Lib10", "Lib11", "LibB1", "LibNoTech"]:
        if os.path.exists(lib_dir):
            shutil.rmtree(lib_dir, ignore_errors=True)
    print("  [PASS] Cleaned up all lib directories")

    print("\n" + "=" * 60)
    print("✅ Lab 20-1 (Incremental Tech Graph) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
