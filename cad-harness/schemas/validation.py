"""Interpreter for the deliberately small JSON Schema subset in contract.schema.json.

Standard keywords handle structure. x-mm-range, x-geometry and x-job-history
are mandatory language-neutral extensions documented in README.md.
Unsupported schema keywords fail closed; this is not a general JSON Schema engine.
"""
import copy
import json
import re
from decimal import Decimal
from pathlib import Path


class ValidationError(ValueError):
    """Invalid boundary data, including a path and violated condition."""


SCHEMA = json.loads(Path(__file__).with_name("contract.schema.json").read_text(encoding="utf-8"))
KEYWORDS = {
    "$schema", "$id", "$defs", "$ref", "title", "description", "$comment",
    "type", "properties", "required", "additionalProperties", "minProperties",
    "enum", "const", "pattern", "minLength", "items", "minItems", "maxItems",
    "uniqueItems", "minimum", "maximum", "oneOf", "x-mm-range", "x-geometry",
    "x-job-history", "x-transitions", "x-observation-links", "x-revision-links", "x-job-links",
}


def _fail(path, condition):
    raise ValidationError(f"{path}: {condition}")


def _mm(value):
    return Decimal(value[:-3])


def _check(value, schema, path):
    unsupported = set(schema) - KEYWORDS
    if unsupported:
        _fail(path, f"unsupported schema keywords: {sorted(unsupported)}")
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            _fail(path, "only local definition references are supported")
        _check(value, SCHEMA["$defs"][ref.removeprefix("#/$defs/")], path)
    if "oneOf" in schema:
        matches = 0
        errors = []
        for branch in schema["oneOf"]:
            try:
                _check(value, branch, path)
                matches += 1
            except ValidationError as exc:
                errors.append(str(exc))
        if matches != 1:
            _fail(path, f"expected exactly one operation variant ({matches} matched): {errors}")
    kind = schema.get("type")
    valid_type = {
        "object": type(value) is dict,
        "array": type(value) is list,
        "string": type(value) is str,
        "integer": type(value) is int,
        "boolean": type(value) is bool,
        "null": value is None,
    }
    if kind is not None and not valid_type.get(kind, False):
        _fail(path, f"expected {kind}")
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        _fail(path, f"expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        _fail(path, f"expected one of {schema['enum']}")
    if kind == "object":
        properties = schema["properties"]
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            _fail(path, f"missing keys: {sorted(missing)}")
        extra = value.keys() - properties.keys()
        if extra and schema.get("additionalProperties") is False:
            _fail(path, f"unknown keys: {sorted(extra)}")
        if len(value) < schema.get("minProperties", 0):
            _fail(path, "too few properties")
        for key, item in value.items():
            if key in properties:
                _check(item, properties[key], f"{path}.{key}")
    if kind == "string":
        if len(value) < schema.get("minLength", 0):
            _fail(path, "empty string")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            _fail(path, f"does not match {schema['pattern']}")
    if kind == "integer":
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            _fail(path, "integer outside range")
    if kind == "array":
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            _fail(path, "array length outside range")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            _fail(path, "duplicate array items")
        for index, item in enumerate(value):
            _check(item, schema["items"], f"{path}[{index}]")
    if "x-mm-range" in schema:
        low, high = map(Decimal, map(str, schema["x-mm-range"]))
        if not low <= _mm(value) <= high:
            _fail(path, f"length outside [{low}, {high}] mm")
    if "x-geometry" in schema:
        dimensions = {k: _mm(v) for k, v in value["dimensions"].items()}
        for rule in schema["x-geometry"]:
            lhs = sum(Decimal(str(factor)) * dimensions[key] for key, factor in rule["terms"].items())
            if lhs <= Decimal(str(rule["greater_than"])):
                _fail(path, rule["condition"])
    if schema.get("x-job-history"):
        history = value["history"]
        if history[0] != "queued" or history[-1] != value["state"]:
            _fail(path, "history must start queued and end at state")
        transitions = SCHEMA["$defs"]["Job"]["x-transitions"]
        for before, after in zip(history, history[1:]):
            if after not in transitions[before]:
                _fail(path, f"illegal job transition {before} -> {after}")
    if schema.get("x-observation-links"):
        visual = value["visual"]
        if visual["status"] == "ready":
            images = visual["images"]
            revision = value["identification"]["revision_id"]
            if {item["view"] for item in images} != {"top", "isometric"}:
                _fail(path, "preview requires top and isometric views")
            if any(item["revision_id"] != revision for item in images):
                _fail(path, "preview revision differs from observation")
    if schema.get("x-revision-links"):
        base = value["base_revision"]
        if base == value["revision_id"]:
            _fail(path, "revision cannot be its own base")
        if (base is None) != (value["candidate_id"] is None):
            _fail(path, "root has null base/candidate; derived revision requires both IDs")
    if schema.get("x-job-links"):
        if value["document_id"] != value["revision"]["document_id"]:
            _fail(path, "job and revision document IDs differ")
        if value["state"] in {"validated", "committed"} and value["revision"]["candidate_id"] is None:
            _fail(path, "validated/committed job requires a candidate")


def validate(type_name, value):
    """Validate a named contract, return an independent JSON value or raise."""
    if type_name not in {"PlateSpec", "Operation", "Observation", "Revision", "Job"}:
        raise ValidationError(f"unknown contract: {type_name}")
    _check(value, SCHEMA["$defs"][type_name], type_name)
    return copy.deepcopy(value)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValidationError(f"non-JSON number: {value}")


def load(type_name, path):
    """Read strict JSON (duplicate keys and NaN/Infinity are rejected)."""
    value = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_pairs,
                       parse_constant=_constant)
    return validate(type_name, value)


def apply_parameters(base, operations):
    """Validate an M2 D/T patch against the current PlateSpec, preserving L/W/e.

    Construction operations are schema contracts only; execution belongs to A2.
    Validate every intermediate candidate so an invalid patch cannot be hidden.
    """
    candidate = validate("PlateSpec", base)
    if type(operations) is not list or not operations:
        raise ValidationError("operations: expected a nonempty list")
    keys = {"hole_diameter": "D", "plate_thickness": "T"}
    for operation in operations:
        op = validate("Operation", operation)
        if op["op"] != "set_parameters":
            raise ValidationError("M2 patch accepts only set_parameters")
        for key, value in op["values"].items():
            candidate["dimensions"][keys[key]] = value
        validate("PlateSpec", candidate)
    return candidate


def transition_job(job, state):
    """Return a new validated state; terminal/unknown states cannot publish."""
    candidate = validate("Job", job)
    candidate["history"].append(state)
    candidate["state"] = state
    return validate("Job", candidate)
