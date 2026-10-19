"""A1 contracts: validate JSON at the boundary without FreeCAD or dependencies."""
from .validation import ValidationError, apply_parameters, load, transition_job, validate

__all__ = ["ValidationError", "validate", "load", "apply_parameters", "transition_job"]
