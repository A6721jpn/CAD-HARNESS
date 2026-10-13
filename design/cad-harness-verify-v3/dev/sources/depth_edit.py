import FreeCAD as App
import Part
import Sketcher
import math

def build_dev_roller(doc, radius=14.5, bore_radius=3.5, length=37.0, groove_z=(13.0, 19.0), groove_depth=1.25):
    body = doc.addObject("PartDesign::Body", "FixtureBody")
    
    # Base Annulus
    s1 = body.newObject("Sketcher::SketchObject", "Annulus")
    s1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    c1 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c1, radius))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c1, 3, -1))
    c2 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_radius), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c2, bore_radius))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c2, 3, -1))
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Roller")
    pad.Profile = s1
    pad.Length = length
    pad.Type = 0
    body.Tip = pad
    doc.recompute()
    return body, pad, s1

def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r = 14.5
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    # Original depth 1.25 -> radius 13.25
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 13.25), False)
    con = s2.addConstraint(Sketcher.Constraint("Radius", c_bot, 13.25))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()

    # Edit parameter: delta +0.5 mm -> depth becomes 1.75, inner radius becomes 12.75
    s2.setDatum(con, 12.75)
    doc.recompute()
    return body
