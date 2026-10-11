"""New negative smoke wrapper; the legacy fixture remains untouched."""
from fixtures.cad_run_a_build import build_without_fillet as _build


def build(doc):
    return _build(doc)
