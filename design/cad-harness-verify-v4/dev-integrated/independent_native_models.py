"""Independent native development models: FreeCAD/OCCT only, no harness imports.

Dimensions and polynomial coefficients are authored development data, not pilot
values. Ordinary C++ sketches/Pad/Pocket cover C1-C4. The C5 feature deliberately
has its own serialized module and a geometric parameter unrelated to any harness
plan, fitter, proxy or pole-offset property.
"""
import math


def _body(doc):
    return doc.addObject('PartDesign::Body', 'Workpiece')


def _rectangle(body, name, x, y, width, height, z=0):
    import FreeCAD as App
    import Part
    sketch = body.newObject('Sketcher::SketchObject', name)
    points = [(x,y), (x+width,y), (x+width,y+height), (x,y+height)]
    for a,b in zip(points, points[1:]+points[:1]):
        sketch.addGeometry(Part.LineSegment(App.Vector(*a,0), App.Vector(*b,0)), False)
    sketch.Placement.Base.z = z
    return sketch


def _pad(body, sketch, length, name='Rise'):
    pad = body.newObject('PartDesign::Pad', name)
    pad.Profile = sketch
    pad.Length = length
    pad.Refine = True
    body.Tip = pad
    body.Document.recompute()
    return pad


def fixture(doc):
    body = _body(doc)
    _pad(body, _rectangle(body,'Footprint',0,0,28,20), 6)
    sketch = _rectangle(body,'RecessProfile',8,6,10,8,6)
    pocket = body.newObject('PartDesign::Pocket', 'Recess')
    pocket.Profile = sketch
    pocket.Length = 3
    body.Tip = pocket
    doc.recompute()
    return body


def contour(doc):
    import FreeCAD as App
    import Part
    body = _body(doc)
    sketch = body.newObject('Sketcher::SketchObject','RoundedOutline')
    x,y,w,h,r = 4.,4.,34.,22.,3.
    k = r/math.sqrt(2)
    lines = [((x+r,y),(x+w-r,y)), ((x+w,y+r),(x+w,y+h-r)),
             ((x+w-r,y+h),(x+r,y+h)), ((x,y+h-r),(x,y+r))]
    arcs = [((x+w-r,y),(x+w-r+k,y+r-k),(x+w,y+r)),
            ((x+w,y+h-r),(x+w-r+k,y+h-r+k),(x+w-r,y+h)),
            ((x+r,y+h),(x+r-k,y+h-r+k),(x,y+h-r)),
            ((x,y+r),(x+r-k,y+r-k),(x+r,y))]
    for (a,b),(p,m,q) in zip(lines,arcs):
        sketch.addGeometry(Part.LineSegment(App.Vector(*a,0),App.Vector(*b,0)),False)
        sketch.addGeometry(Part.Arc(App.Vector(*p,0),App.Vector(*m,0),App.Vector(*q,0)),False)
    _pad(body,sketch,4)
    return body


def engraving(doc, font_path):
    import FreeCAD as App
    import Part
    from pathlib import Path
    body = _body(doc)
    _pad(body,_rectangle(body,'StockOutline',0,0,20,20),4)
    font = Path(font_path)
    letters = Part.makeWireString('B8',str(font.parent)+'/',font.name,4)
    wires = [wire for letter in letters for wire in letter]
    ink = Part.makeCompound(wires)
    scale = 4/ink.BoundBox.YLength
    matrix = App.Matrix()
    matrix.scale(scale,scale,scale)
    sketch = body.newObject('Sketcher::SketchObject','LetterProfiles')
    for wire in wires:
        wire = wire.transformGeometry(matrix)
        wire.translate(App.Vector(4,5,0))
        for edge in wire.Edges:
            if isinstance(edge.Curve,Part.Line):
                curve = Part.LineSegment(edge.Vertexes[0].Point,edge.Vertexes[-1].Point)
            else:
                curve = edge.Curve.copy()
                curve.segment(edge.FirstParameter,edge.LastParameter)
            sketch.addGeometry(curve,False)
    sketch.Placement.Base.z = 4
    pocket = body.newObject('PartDesign::Pocket','LetterDepth')
    pocket.Profile = sketch
    pocket.Length = .5
    body.Tip = pocket
    doc.recompute()
    return body


def imported_edit(doc, original):
    body = _body(doc)
    imported = body.newObject('PartDesign::Feature','ImportedOriginal')
    imported.Shape = original.copy()
    body.Tip = imported
    doc.recompute()
    _pad(body,_rectangle(body,'AddedLayer',0,0,18,12,7),1,'LayerHeight')
    return body


def _roof(original, lift):
    import FreeCAD as App
    import Part
    # Global polynomial in t=X/28, v=Y/18. t^3 rounds the interior source
    # second-jet jump but agrees exactly with all four source boundary curves.
    coefficients = {(0,0):4., (2,0):.48, (1,1):.07+4*lift, (0,2):.08,
                    (3,2):.48, (3,3):-.96, (3,4):.48,
                    (2,1):-4*lift, (1,2):-4*lift, (2,2):4*lift}
    pu,pv = 3,4
    poles = []
    for i in range(pu+1):
        row = []
        for j in range(pv+1):
            z = sum(c*math.comb(i,a)/math.comb(pu,a)*math.comb(j,b)/math.comb(pv,b)
                    for (a,b),c in coefficients.items() if a<=i and b<=j)
            row.append(App.Vector(28*i/pu,18*j/pv,z))
        poles.append(row)
    surface = Part.BSplineSurface()
    surface.buildFromPolesMultsKnots(poles,[4,4],[5,5],[0.,1.],[0.,1.],False,False,pu,pv)
    cap = surface.toShape()
    others = []
    removed = 0
    for face in original.Faces:
        u0,u1,v0,v1 = face.ParameterRange
        if face.normalAt((u0+u1)/2,(v0+v1)/2).z > .8:
            removed += 1
        else:
            others.append(face.copy())
    if removed != 2:
        raise ValueError('independent_source_expected_two_top_faces')
    shell = Part.makeShell(others+[cap])
    shell.sewShape()
    result = Part.makeSolid(shell)
    if result.Volume < 0:
        result.reverse()
    if result.isNull() or not result.isValid() or len(result.Solids)!=1:
        raise ValueError('independent_analytic_roof_not_a_valid_solid')
    return result


class AnalyticCap:
    def dumps(self):
        return 'independent-analytic-cap:1'

    def loads(self,value):
        if value != self.dumps():
            raise ValueError('independent_native_version')

    def execute(self,obj):
        import Part
        obj.Shape = Part.Shape()
        original = Part.Shape()
        original.importBrepFromString(obj.OriginalBrep)
        obj.Shape = _roof(original,float(obj.InteriorLift))

    def onDocumentRestored(self,obj):
        obj.touch()


def rebuilt_surface(doc, original):
    body = _body(doc)
    cap = body.newObject('PartDesign::FeaturePython','AnalyticBlend')
    cap.addProperty('App::PropertyString','OriginalBrep','Source')
    cap.OriginalBrep = original.exportBrepToString()
    cap.setEditorMode('OriginalBrep',1)
    cap.addProperty('App::PropertyFloat','InteriorLift','Geometry')
    cap.InteriorLift = 0.
    cap.Proxy = AnalyticCap()
    body.Tip = cap
    doc.recompute()
    return body
