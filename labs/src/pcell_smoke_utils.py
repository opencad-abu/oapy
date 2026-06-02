import os
import shutil

from oapy._oa import _base, _design, _dm
from utils import c_str, init_oa, open_design_stable


def oa_str(value):
    return _base.oaString(str(value))


def scalar(ns, value):
    return _base.oaScalarName(ns, str(value))


def clean_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def view_type(name="schematic"):
    vt = _dm.oaViewType.find(oa_str(name))
    if not vt:
        vt = _dm.oaViewType.create(oa_str(name))
    return vt


def setup_library(lib_name, rel_path, vt_name="schematic"):
    init_oa()
    ns = _base.oaNativeNS()
    clean_dir(rel_path)
    sn_lib = scalar(ns, lib_name)
    lib = _dm.oaLib.create(
        sn_lib,
        oa_str(rel_path),
        _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
        oa_str("oaDMFileSys"),
        _dm.oaDMAttrArray(0),
    )
    return ns, sn_lib, lib, view_type(vt_name)


def block_visibility():
    return _design.oaBlockDomainVisibility(
        _design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock)


def placement_status():
    return _design.oaPlacementStatus(
        _design.oaPlacementStatusEnum.oacUnplacedPlacementStatus)


def r0_transform(x=0, y=0):
    return _base.oaTransform(
        _base.oaPoint(x, y),
        _base.oaOrient(_base.oaOrientEnum.oacR0),
    )


def param_array(items=None):
    if items is None:
        items = [("p0param", "NetName"), ("p1param", 1)]
    arr = _base.oaParamArray(len(items))
    for index, (name, value) in enumerate(items):
        arr[index] = _base.oaParam(str(name), value)
    arr.setNumElements(len(items))
    return arr


def create_design_with_block(sn_lib, ns, cell, view, vt):
    view_type_name = "schematic"
    if vt is not None:
        name = _base.oaString()
        vt.getName(name)
        view_type_name = c_str(name)
    des, _ = open_design_stable(str(cell), str(view), sn_lib, "w", view_type_name)
    block = _design.oaBlock.create(des, True)
    return des, block


class SimpleIPcell(_design.IPcell):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self._pcell_def = None
        self.eval_count = 0
        self.bind_count = 0
        self.unbind_count = 0

    def getName(self, name):
        getattr(name, "operator=")(self.name)
        return self.name

    def getPcellDef(self):
        if self._pcell_def is None:
            self._pcell_def = _design.oaPcellDef(self)
        return self._pcell_def

    def calcDiskSize(self, pcellDef):
        return 0

    def onRead(self, design, mapWindow, loc, pcellDef):
        pass

    def onWrite(self, design, mapWindow, loc, pcellDef):
        pass

    def onBind(self, design, pcellDef):
        self.bind_count += 1

    def onUnbind(self, design, pcellDef):
        self.unbind_count += 1

    def onEval(self, design, pcellDef):
        self.eval_count += 1
        block = design.getTopBlock()
        if not block:
            block = _design.oaBlock.create(design, True)
        ns = _base.oaNativeNS()
        name = scalar(ns, f"evalNet_{self.eval_count}")
        try:
            _design.oaScalarNet.create(
                block,
                name,
                _design.oaSigType(_design.oaSigTypeEnum.oacSignalSigType),
                1,
                block_visibility(),
            )
        except Exception:
            pass


def register_ipcell(ip):
    link = _design.oaPcellLink.find(oa_str(ip.name))
    if not link:
        link = _design.oaPcellLink.create(ip)
    return link, ip.getPcellDef()


def define_supermaster(sn_lib, ns, vt, cell, ip_name, params=None):
    ip = SimpleIPcell(ip_name)
    link, pcell_def = register_ipcell(ip)
    des, block = create_design_with_block(sn_lib, ns, cell, "schematic", vt)
    params = params or param_array()
    des.defineSuperMaster(pcell_def, params)
    return ip, link, pcell_def, des, block, params


def instantiate_pcell(block, ns, master, inst_name, params=None, x=0, y=0):
    params = params or param_array()
    inst = _design.oaScalarInst.create(
        block,
        master,
        scalar(ns, inst_name),
        r0_transform(x, y),
        params,
        block_visibility(),
        placement_status(),
    )
    return inst
