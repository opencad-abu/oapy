#!/usr/bin/env python3
"""Minimal test for oaDMTurbo plugin loading"""
import sys
sys.path.insert(0, '/workarea/ai/openclaw/oapy/build')
sys.path.insert(0, '/workarea/ai/openclaw/oapy')

from oapy._oa import _base, _dm

print("Initializing OA...")
_base.oaInit()

print("Creating namespace...")
ns = _base.oaNativeNS()

print("Creating lib name...")
sn_lib = _base.oaScalarName(ns, "test_dmturbo")

print("Creating lib with oaDMTurbo...")
try:
    lib = _dm.oaLib.create(
        sn_lib,
        _base.oaString("/tmp/test_dmturbo_lib"),
        _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
        _base.oaString("oaDMTurbo"),
        _dm.oaDMAttrArray(0)
    )
    print("SUCCESS: Library created")
except Exception as e:
    print(f"FAILED: {e}")
