"""New negative smoke wrapper; the legacy fixture remains untouched."""
from fixtures.cad_run_b_build import build_without_chamfer as _build


def build(doc):
    return _build(doc)
