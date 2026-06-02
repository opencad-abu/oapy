#!/bin/bash
# oapy lab runner — 使用 oacpp 自编译 OA 库 (包含完整 DM 插件)
# Usage: ./run_lab.sh lab_script.py [args...]

LABS_DIR="$(cd "$(dirname "$0")" && pwd)"
OAPY_ROOT="$(dirname "$LABS_DIR")"
SRC_DIR="${LABS_DIR}/src"
DATA_DIR="${LABS_DIR}/data"

PY_LIB="/software/pkgs/python/3.12.9/lib"
OAPY_OA="${OAPY_ROOT}/oapy/_oa"
OACPP_LIB="/workarea/ai/openclaw/oacpp/lib/linux_rhel70_gcc93x_64/opt"
OA_LIB="/software/pkgs/oa/22.61/lib/linux_rhel70_gcc93x_64/opt"
CPPLABS_PLUGIN_LIBS="/workarea/ai/openclaw/oa22.61-cpplabs/16-4.bbplugin:/workarea/ai/openclaw/oa22.61-cpplabs/18-5.pcplugin"
if [ -z "$1" ]; then
    echo "Usage: ./run_lab.sh <lab_script.py> [args...]"
    echo ""
    echo "Available labs:"
    ls "${SRC_DIR}"/lab*.py 2>/dev/null | xargs -n1 basename | sed 's/^/  /'
    exit 1
fi

LAB_SCRIPT="$(basename "$1")"

export LD_LIBRARY_PATH="${PY_LIB}:${OAPY_OA}:${CPPLABS_PLUGIN_LIBS}:${OACPP_LIB}:${OA_LIB}:${LD_LIBRARY_PATH}"

case "${LAB_SCRIPT}" in
  lab16_9_rq.py|lab16_10_rqeasy.py)
    # RegionQuery uses the official oaRQXYTree plug-in. It is ABI-incompatible
    # with the oacpp-preloaded OA libraries, so run these labs against official OA.
    export LD_LIBRARY_PATH="${PY_LIB}:${OAPY_OA}:${OA_LIB}:${LD_LIBRARY_PATH}"
    unset LD_PRELOAD
    ;;
  *)
    # 预加载所有 oacpp 库以覆盖官方版本（确保 ABI 一致性）
    # 顺序无关紧要，每个库都会被强制加载
    export LD_PRELOAD="${OACPP_LIB}/liboaBase.so:${OACPP_LIB}/liboaCommon.so:${OACPP_LIB}/liboaPlugIn.so:${OACPP_LIB}/liboaDM.so:${OACPP_LIB}/liboaDMFileSysBase.so:${OACPP_LIB}/liboaDMFileSys.so:${OACPP_LIB}/liboaDMTurboBase.so:${OACPP_LIB}/liboaDMTurbo.so:${OACPP_LIB}/liboaDesign.so:${OACPP_LIB}/liboaTech.so:${OACPP_LIB}/liboaWafer.so:${OACPP_LIB}/liboaCM.so:${OACPP_LIB}/liboaNativeLibDef.so:${OACPP_LIB}/liboaNativeLock.so:${OACPP_LIB}/liboaNativeText.so:${OACPP_LIB}/liboaCMExportSample.so:${OACPP_LIB}/liboaCMTrackingSample.so:${OACPP_LIB}/liboaVCSample.so:${OACPP_LIB}/liboaAiviLibDef.so:${OACPP_LIB}/liboaLockAIVI.so"
    ;;
esac

export PYTHONPATH="${OAPY_ROOT}/build:${OAPY_ROOT}:${SRC_DIR}:${PYTHONPATH}"

# 设置 OA_PLUGIN_PATH 让 OA 能发现插件的 .plg 文件
export OA_PLUGIN_PATH="/workarea/ai/openclaw/oa22.61-cpplabs/data/plugins:/software/pkgs/oa/22.61/cpp.labs/data/plugins:/software/pkgs/oa/22.61/data/plugins:${OA_PLUGIN_PATH}"

cd "${SRC_DIR}"
exec /software/pkgs/python/3.12.9/bin/python3 -u "${LAB_SCRIPT}" "${@:2}"
