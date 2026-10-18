"""Read native datum properties without loading the GUI."""
import FreeCAD as App
import json
d = App.newDocument("InspectDatum")
for type_id in ("PartDesign::CoordinateSystem", "App::LocalCoordinateSystem", "Assembly::AssemblyObject", "Assembly::JointGroup"):
    try:
        o = d.addObject(type_id, "Inspect")
        print(json.dumps({"requested": type_id, "type": o.TypeId, "properties": o.PropertiesList,
                          "methods": [x for x in dir(o) if "ttach" in x or "olve" in x]}))
    except Exception as exc:
        print(repr(exc))
