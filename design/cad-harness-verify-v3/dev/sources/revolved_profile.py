import FreeCAD as App
import Part
import Sketcher

def build(doc):
    body = doc.addObject("PartDesign::Body", "FixtureBody")
    # Roller profile with annular groove, using Pad + Pocket
    # To ensure complete robustness, pad with radius difference
    s1 = body.newObject("Sketcher::SketchObject", "Annulus")
    s1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    c1 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 14.5), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c1, 14.5))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c1, 3, -1))
    c2 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 3.5), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c2, 3.5))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c2, 3, -1))
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Roller")
    pad.Profile = s1
    pad.Length = 37.0
    pad.Type = 0
    body.Tip = pad
    doc.recompute()

    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, 19.0), App.Rotation())
    gc1 = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 14.5), False)
    s2.addConstraint(Sketcher.Constraint("Radius", gc1, 14.5))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", gc1, 3, -1))
    gc2 = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 13.25), False)
    s2.addConstraint(Sketcher.Constraint("Radius", gc2, 13.25))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", gc2, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = 6.0
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
