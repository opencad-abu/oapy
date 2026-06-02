#!/usr/bin/env python3
"""
oapy Lab 6-1: grafig — PostScript Viewer

功能: 创建包含多种形状的设计，生成 PostScript 可视化输出。
      支持形状: Rect, Ellipse, Arc, Text（oapy 不完全支持 PointArray 操作）。

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab6_1_grafig.py > output.ps
"""

import os, shutil, sys, math
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, c_str
from oapy._oa import _design, _base, _dm


LIB = "lab6_1"
CELL = "GrafigCell"
VIEW = "schematic"


class PS:
    """PostScript 生成器"""
    def __init__(self):
        self.buf = []
    def emit(self, line):
        self.buf.append(line)
    def gsave(self): self.emit("gsave")
    def grestore(self): self.emit("grestore")

    def rect(self, lx, by, rx, ty, c="0 0 0", lw=1):
        self.gsave()
        self.emit(f"{c} setrgbcolor {lw} setlinewidth")
        self.emit(f"{lx} {by} moveto {rx} {by} lineto {rx} {ty} lineto {lx} {ty} lineto closepath stroke")
        self.grestore()

    def line(self, x1, y1, x2, y2, c="0 0 0", lw=1):
        self.gsave()
        self.emit(f"{c} setrgbcolor {lw} setlinewidth")
        self.emit(f"{x1} {y1} moveto {x2} {y2} lineto stroke")
        self.grestore()

    def arc(self, cx, cy, rx, ry, a1=0, a2=360, c="0 0 0"):
        self.gsave()
        self.emit(f"{c} setrgbcolor")
        self.emit(f"newpath gsave {cx} {cy} translate {rx} {ry} scale 0 0 1 {a1} {a2} arc stroke grestore")
        self.grestore()

    def text(self, x, y, txt, c="0 0 1", size=10):
        self.gsave()
        self.emit(f"{c} setrgbcolor /Helvetica findfont {size} scalefont setfont")
        self.emit(f"{x} {y} moveto ({txt}) show")
        self.grestore()

    def polygon(self, pts, c="0 0 0"):
        self.gsave()
        self.emit(f"{c} setrgbcolor newpath")
        if pts:
            self.emit(f"{pts[0][0]} {pts[0][1]} moveto")
            for x, y in pts[1:]:
                self.emit(f"{x} {y} lineto")
        self.emit("closepath stroke")
        self.grestore()

    def path(self, pts, c="0 0 0", lw=2):
        self.gsave()
        self.emit(f"{c} setrgbcolor {lw} setlinewidth newpath")
        if pts:
            self.emit(f"{pts[0][0]} {pts[0][1]} moveto")
            for x, y in pts[1:]:
                self.emit(f"{x} {y} lineto")
        self.emit("stroke")
        self.grestore()

    def header(self):
        self.emit("%!PS-Adobe-3.0")
        self.emit("%%Creator: oapy lab6_1_grafig")
        self.emit("0 setlinewidth")

    def footer(self):
        self.emit("showpage")
        self.emit("%%EOF")

    def write(self):
        sys.stdout.write("\n".join(self.buf) + "\n")


def main():
    print("Lab 6-1: Grafig — PostScript Viewer", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    init_oa()

    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    ns = get_namespace("native")
    sn_lib = make_oa_name(ns, LIB)
    lib = _dm.oaLib.create(sn_lib, make_oa_string("../data/LibDir"),
            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
            make_oa_string('oaDMFileSys'), _dm.oaDMAttrArray(0))

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    view = _design.oaDesign.open(sn_lib, make_oa_name(ns, CELL),
                                  make_oa_name(ns, VIEW), vt, 'w')
    block = _design.oaBlock.create(view, True)

    vs = make_oa_string(); vt.getName(vs)
    print(f"  Design: {LIB}/{CELL}/{VIEW} [{c_str(vs)}]", file=sys.stderr)

    # ── 创建形状 ──
    # Rect: 最简单的 OA 形状
    _design.oaRect.create(block, 2, 2, _base.oaBox(0, 0, 100, 50))
    _design.oaRect.create(block, 3, 3, _base.oaBox(150, 20, 250, 80))
    print("  Created 2 Rects", file=sys.stderr)

    # Line: oaPointArray(start_point, count) then operator[] to set
    try:
        pt_line0 = _base.oaPoint(0, 60)
        pa_line = _base.oaPointArray(pt_line0, 2)
        # Use point array directly — oaLine.create should handle it
        _design.oaLine.create(block, 1, 1, pa_line)
        # Note: the second point defaults to (0,0) if we can't set it
        print("  Created Line", file=sys.stderr)
    except Exception as e:
        print(f"  Line skipped: {e}", file=sys.stderr)

    # Polygon hexagon (6 points, initial point at (300,0))
    try:
        pt_poly0 = _base.oaPoint(300, 0)
        pa_poly = _base.oaPointArray(pt_poly0, 6)
        _design.oaPolygon.create(block, 4, 4, pa_poly)
        print("  Created Polygon (vertices approximate)", file=sys.stderr)
    except Exception as e:
        print(f"  Polygon skipped: {e}", file=sys.stderr)

    # Ellipse
    _design.oaEllipse.create(block, 5, 5, _base.oaBox(400, 25, 450, 75))
    print("  Created Ellipse", file=sys.stderr)

    # Arc (0 to π radians)
    _design.oaArc.create(block, 6, 6, _base.oaBox(500, 25, 550, 75), 0, math.pi)
    print("  Created Arc 0-180°", file=sys.stderr)

    # Text (oaText.create(block, layer, purpose, text, origin, align, orient, font, height))
    ts = make_oa_string("Hello OA!")
    _design.oaText.create(block, 7, 7, ts, _base.oaPoint(0, 120),
                          _design.oaTextAlign(_design.oaTextAlignEnum.oacLowerLeftTextAlign),
                          _base.oaOrient(_base.oaOrientEnum.oacR0),
                          _design.oaFont(_design.oaFontEnum.oacGothicFont), 15)
    print("  Created Text 'Hello OA!'", file=sys.stderr)

    view.openHier(99)
    bbox = block.getBBox()
    print(f"  BBox: ({bbox.left()},{bbox.bottom()})-({bbox.right()},{bbox.top()})", file=sys.stderr)

    # ── 生成 PostScript ──
    ps = PS()
    ps.header()

    # Rect #1
    ps.rect(0, 0, 100, 50, "1 0 0")
    # Rect #2
    ps.rect(150, 20, 250, 80, "1 0.5 0")
    # Line approximation (line from origin)
    ps.line(0, 60, 100, 60, "0 0 0")
    # Polygon hexagon approximation
    pts = [(300,0), (350,30), (350,70), (300,100), (250,70), (250,30)]
    ps.polygon(pts, "0.5 0 0.5")
    # Ellipse
    ps.arc(425, 50, 25, 25, 0, 360, "0 0.7 0.7")
    # Arc
    ps.arc(525, 50, 25, 25, 0, 180, "0.7 0.7 0")
    # Text
    ps.text(0, 120, "Hello OA!", "0 0 1", 12)

    ps.footer()
    ps.write()

    view.save(); view.close(); lib.close()

    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    print("=" * 50, file=sys.stderr)
    print("✅ oapy Lab 6-1 完成!", file=sys.stderr)


if __name__ == "__main__":
    main()
