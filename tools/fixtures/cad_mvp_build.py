"""Hand-authored typed compiler fixtures. No evaluation data or description hashes."""
import json
from pathlib import Path

SPEC_DIR = Path(__file__).resolve().parent / "mvp"
SUITE_INPUTS = ("P1", "P2", "P3", "P4", "P5")
HELD_OUT = {"H_RECT_CHAMFER": ("rect_prism", "top_chamfer"),
            "H_RECT_FILLET": ("rect_prism", "top_fillet"),
            "H_RECT_STACK": ("rect_stack",),
            "H_SHAFT": ("stepped_shaft",)}


def typed_spec(name):
    if name not in SUITE_INPUTS and name not in HELD_OUT:
        raise ValueError("unknown_fixture")
    return json.loads((SPEC_DIR / (name + ".json")).read_text(encoding="utf-8"))


def held_out_specs():
    return {name: typed_spec(name) for name in HELD_OUT}
