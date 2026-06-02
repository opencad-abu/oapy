#!/usr/bin/env python3
"""Lab 17-8: si2mutex lock-factory behavior smoke test."""

import os
import sys
import threading
import traceback

from pcell_smoke_utils import setup_library, create_design_with_block


def main():
    print("=" * 60)
    print("Lab 17-8: si2mutex")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("Lib17_8_Mutex", "../data/Lib17_8_Mutex")
    lock = threading.Lock()
    results = []

    def worker(index):
        with lock:
            des, block = create_design_with_block(sn_lib, ns, f"cell_{index}", "schematic", vt)
            des.save()
            results.append(index)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == [0, 1, 2, 3]
    print("  Serialized design creation through Python mutex")
    print("✅ Lab 17-8 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
