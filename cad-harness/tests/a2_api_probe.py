"""Record the installed Pocket enum before choosing its exact native spelling."""
import FreeCAD as App
import json
import os
from pathlib import Path

doc = App.newDocument("A2ApiProbe")
body = doc.addObject("PartDesign::Body", "Body")
pocket = body.newObject("PartDesign::Pocket", "Pocket")
data = {"pocket_type_enum": pocket.getEnumerationsOfProperty("Type"),
        "origin_features": [(obj.Name, obj.TypeId) for obj in body.Origin.OriginFeatures]}
print(json.dumps(data))
Path(os.environ["A2_PROBE_JSON"]).write_text(json.dumps(data, indent=2), encoding="utf-8")
