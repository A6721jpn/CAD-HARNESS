# Existing output contracts (verbatim)

## Spec
Return one build-spec JSON matching this schema, or {"unsupported":["reason"]} or {"needs_clarification":["question"]}. Do not return source or grading values. Units default to mm. Unless placement is specified, center XY and put the bottom at Z=0. These placement defaults are binding; do not ask clarification for unspecified origin/placement. Region bounds require exactly six numbers: [x_min,x_max,y_min,y_max,z_min,z_max]; region z is required, never optional. List regions bottom-up, base first; each higher region starts at a previous region's top and is contained in its XY bounds. Pocket bounds require four XY numbers; top_z and depth are required, and pockets cut down from top_z. Hole z is required as [bottom,top] and must equal the full z interval of the pierced region. Pocket/hole overlap, overlapping holes/pockets, and blocked hole openings are unsupported.
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CAD harness declarative build specification v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema",
    "family"
  ],
  "properties": {
    "schema": {
      "const": "cad-harness.build-spec.v1"
    },
    "family": {
      "enum": [
        "rect_prism",
        "rect_stack",
        "stepped_shaft"
      ]
    },
    "units": {
      "enum": [
        "mm",
        "cm",
        "m"
      ],
      "default": "mm"
    },
    "frame": {
      "const": "world",
      "default": "world"
    },
    "regions": {
      "type": "array",
      "description": "Bottom-up, base first. Each region requires six bounds including z_min/z_max; higher regions start at a prior top and lie inside that region in XY.",
      "minItems": 1,
      "maxItems": 8,
      "items": {
        "$ref": "#/$defs/region"
      }
    },
    "center_xy": {
      "$ref": "#/$defs/pair"
    },
    "steps": {
      "type": "array",
      "minItems": 1,
      "maxItems": 8,
      "items": {
        "$ref": "#/$defs/step"
      }
    },
    "pockets": {
      "type": "array",
      "maxItems": 8,
      "default": [],
      "items": {
        "$ref": "#/$defs/pocket"
      }
    },
    "holes": {
      "type": "array",
      "maxItems": 64,
      "default": [],
      "items": {
        "$ref": "#/$defs/hole"
      }
    },
    "finish": {
      "oneOf": [
        {
          "type": "null"
        },
        {
          "$ref": "#/$defs/finish"
        }
      ],
      "default": null
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "family": {
            "const": "rect_prism"
          }
        }
      },
      "then": {
        "required": [
          "regions"
        ],
        "properties": {
          "regions": {
            "maxItems": 1
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "family": {
            "const": "rect_stack"
          }
        }
      },
      "then": {
        "required": [
          "regions"
        ],
        "properties": {
          "regions": {
            "minItems": 2
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "family": {
            "const": "stepped_shaft"
          }
        }
      },
      "then": {
        "required": [
          "steps"
        ]
      }
    }
  ],
  "$defs": {
    "pair": {
      "type": "array",
      "minItems": 2,
      "maxItems": 2,
      "items": {
        "type": "number"
      }
    },
    "bounds4": {
      "type": "array",
      "description": "Exactly [x_min,x_max,y_min,y_max]. Pocket top_z and depth are separate required fields.",
      "minItems": 4,
      "maxItems": 4,
      "items": {
        "type": "number"
      }
    },
    "bounds6": {
      "type": "array",
      "description": "Exactly [x_min,x_max,y_min,y_max,z_min,z_max]; both z coordinates are required.",
      "minItems": 6,
      "maxItems": 6,
      "items": {
        "type": "number"
      }
    },
    "region": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "bounds"
      ],
      "properties": {
        "bounds": {
          "$ref": "#/$defs/bounds6"
        }
      }
    },
    "step": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "diameter",
        "z"
      ],
      "properties": {
        "diameter": {
          "type": "number",
          "exclusiveMinimum": 0
        },
        "z": {
          "$ref": "#/$defs/pair"
        }
      }
    },
    "pocket": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "bounds",
        "top_z",
        "depth"
      ],
      "properties": {
        "bounds": {
          "$ref": "#/$defs/bounds4"
        },
        "top_z": {
          "type": "number"
        },
        "depth": {
          "type": "number",
          "exclusiveMinimum": 0
        }
      }
    },
    "hole": {
      "type": "object",
      "description": "Through hole: required z equals the pierced region's full [bottom,top]. No pocket/hole or hole/hole overlap, nor blocked openings.",
      "additionalProperties": false,
      "required": [
        "center_xy",
        "diameter",
        "z"
      ],
      "properties": {
        "center_xy": {
          "$ref": "#/$defs/pair"
        },
        "diameter": {
          "type": "number",
          "exclusiveMinimum": 0
        },
        "z": {
          "$ref": "#/$defs/pair"
        }
      }
    },
    "finish": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "kind",
        "size",
        "target"
      ],
      "properties": {
        "kind": {
          "enum": [
            "fillet",
            "chamfer"
          ]
        },
        "size": {
          "type": "number",
          "exclusiveMinimum": 0
        },
        "target": {
          "const": "top_outer"
        }
      }
    }
  }
}


## Compiler capabilities
The compiler supports exactly rect_prism, rect_stack, stepped_shaft. Rectangular families support axis-aligned connected stock regions, rectangular top pockets, Z through holes and top_outer fillet/chamfer within the build schema and compiler limits. stepped_shaft supports coaxial solid steps only, without bore, holes, pockets or finish. Tapers, curved pipes, ribs, circular flanges, hollow/grooved rollers and other unrepresentable features must return a well-formed unsupported list. Do not invent new families or fields.

## Clarification
VERIFY clarification contract: needs_clarification is a list of necessary missing field IDs only, never natural-language questions or invented values. Allowed field IDs: plate_thickness, hole_positions, hole_diameter, pocket_depth, pocket_size, stock_dimensions, axis, finish_size.

## Source
Return only complete Python source defining build(doc) and returning its Body. Allowed imports: FreeCAD, Part, Sketcher, math. No file, shell, network, document lifecycle, save or probe operations.

## Repair
Retain this output path for CAD repair; no unsupported or clarification fallback.
Keep user-stated dimensions editable on the geometry that they control. A radial groove depth can be a constrained radial span between the actual stock and bottom boundaries, a difference of their driven radii, or half a difference of their driven diameters. Groove width can be an operative length or driven axial boundary difference; half-width requires active symmetry proving both boundaries and their driven center. Use native constraints/features, not detached numbers or inactive properties. No unstated derived dimension is independently required.
