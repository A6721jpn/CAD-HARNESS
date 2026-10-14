"""Offline, data-only extraction and integrity checks for addendum B pilot bundles."""
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat

if __package__:
    from . import cad_verify_v4_ledger as ledger
else:
    import cad_verify_v4_ledger as ledger

SCHEMA = "cad-harness.pilot-bundle.v4"
CONTEXT_SCHEMA = "cad-harness.pilot-context.v4"
ATTACHMENTS_SCHEMA = "cad-harness.pilot-attachments.v4"
WINDOW_CHARS = 40000
TEXT_TYPES = frozenset(("input_text", "output_text", "text"))


def _fail(code, detail):
    raise ValueError(f"{code}:{detail}")


def _private(path, code):
    # Check lexical spelling before any filesystem operation, including resolve/stat.
    parts = str(path).replace("\\", "/").casefold().split("/")
    if "v4-holdout-private" in parts:
        _fail(code, "private_holdout_path_forbidden")


def _safe_source(value, code, *, absolute=False):
    if not isinstance(value, (str, os.PathLike)) or not str(value):
        _fail(code, "invalid_path")
    _private(value, code)
    path = Path(value)
    if ".." in str(value).replace("\\", "/").split("/"):
        _fail(code, "path_traversal")
    if absolute and not path.is_absolute():
        _fail(code, "attachment_path_not_absolute")
    path = path.absolute()
    _private(path, code)
    try:
        for part in reversed((path, *path.parents)):
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                _fail(code, "linked_path")
    except OSError as exc:
        _fail(code, f"missing_or_unreadable_path:{exc}")
    return path


def _read_bytes(path, code):
    try:
        return path.read_bytes()
    except OSError as exc:
        _fail(code, f"unreadable_file:{exc}")


def _json(raw, code):
    try:
        # Reuse the ledger's parser, including its rejection of nonfinite numbers.
        return ledger.cad_agent.loads(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeError, TypeError) as exc:
        _fail(code, f"malformed_json:{exc}")


def _hash_file(path, code):
    try:
        return ledger.file_sha(path)
    except OSError as exc:
        _fail(code, f"unreadable_file:{exc}")


def _text_message(row, line, ordinal):
    payload = row.get("payload")
    if row.get("type") == "response_item" and (not isinstance(payload, dict) or not isinstance(payload.get("type"), str)):
        _fail("E6", "malformed_response_item")
    if row.get("type") != "response_item" or not isinstance(payload, dict):
        return None, ordinal
    if payload.get("type") != "message":
        return None, ordinal
    ordinal += 1
    if payload.get("role") not in ("user", "assistant") or payload.get("channel") == "analysis":
        return None, ordinal
    content = payload.get("content")
    if not isinstance(content, list):
        _fail("E6", "message_content_not_blocks")
    blocks = []
    for index, block in enumerate(content, 1):
        if not isinstance(block, dict) or not isinstance(block.get("type"), str):
            _fail("E6", "malformed_content_block")
        if block.get("type") in TEXT_TYPES and block.get("channel") != "analysis":
            if not isinstance(block.get("text"), str):
                _fail("E6", "malformed_text_block")
            blocks.append(dict(index=index, type=block["type"], text=block["text"]))
    if not blocks:
        return None, ordinal
    return dict(line=line, ordinal=ordinal, role=payload["role"], blocks=blocks,
                chars=sum(len(block["text"]) for block in blocks)), ordinal


def _extract(source, locator, request, conversation_id):
    before = _hash_file(source, "E6")
    raw = _read_bytes(source, "E6")
    if ledger.sha(raw) != before:
        _fail("E6", "source_changed")
    if type(locator) is not int or locator < 1:
        _fail("E6", "locator_not_physical_line")
    if conversation_id is not None and (not isinstance(conversation_id, str) or not conversation_id):
        _fail("E6", "invalid_conversation_id")
    prior, target, session_ids, ordinal = [], None, [], 0
    # split on LF, not Unicode splitlines: a JSONL locator is a physical file line.
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    for line, encoded in enumerate(lines, 1):
        row = _json(encoded, "E6")
        if not isinstance(row, dict) or not isinstance(row.get("type"), str):
            _fail("E6", "malformed_jsonl_record")
        if row["type"] == "session_meta":
            payload = row.get("payload")
            if not isinstance(payload, dict) or not isinstance(payload.get("id"), str) or not payload["id"]:
                _fail("E6", "malformed_session_meta")
            session_ids.append(payload["id"])
        message, ordinal = _text_message(row, line, ordinal)
        if line == locator:
            target = message
        elif line < locator and message is not None:
            prior.append(message)
    if len(set(session_ids)) > 1:
        _fail("E6", "multiple_conversations")
    actual_id = session_ids[0] if session_ids else None
    if conversation_id is not None and actual_id != conversation_id:
        _fail("E6", "conversation_id_mismatch")
    if target is None or target["role"] != "user":
        _fail("E6", "target_not_found_at_locator")
    if request not in "".join(block["text"] for block in target["blocks"]):
        _fail("E6", "locator_request_mismatch")
    count, start = 0, len(prior)
    for index in range(len(prior)-1, -1, -1):
        if count + prior[index]["chars"] > WINDOW_CHARS:
            break
        count += prior[index]["chars"]
        start = index
    selected = prior[start:]
    after = _hash_file(source, "E6")
    if after != before:
        _fail("E6", "source_changed")
    context = dict(schema=CONTEXT_SCHEMA, source_sha256=before, conversation_id=actual_id,
                   locator=dict(line=locator, ordinal=target["ordinal"]),
                   window=dict(limit_chars=WINDOW_CHARS, chars=count, eligible_messages=len(prior),
                               included_messages=len(selected), omitted_messages=start, cut=start > 0,
                               first_line=selected[0]["line"] if selected else None,
                               last_line=selected[-1]["line"] if selected else None),
                   messages=selected)
    return context, target, before


def _inventory(path):
    """List only real regular files/directories, without following links or junctions."""
    path = _safe_source(path, "E7", absolute=True)
    entries = []

    def visit(current, relative):
        _safe_source(current, "E7", absolute=True)
        info = current.lstat()
        if stat.S_ISREG(info.st_mode):
            entries.append(dict(relative=relative, kind="file", bytes=info.st_size,
                                sha256=_hash_file(current, "E7")))
        elif stat.S_ISDIR(info.st_mode):
            entries.append(dict(relative=relative, kind="directory"))
            for child in sorted(current.iterdir(), key=lambda item: item.name):
                # Names must also be safe when serialized as portable bundle paths.
                _relative(child.name)
                visit(child, f"{relative}/{child.name}" if relative else child.name)
        else:
            _fail("E7", "attachment_not_regular_file_or_directory")

    try:
        visit(path, "")
    except OSError as exc:
        _fail("E7", f"unreadable_attachment:{exc}")
    return entries


def _relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        _fail("E7", "invalid_bundle_path")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts) or PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        _fail("E7", "bundle_path_traversal")
    _private(value, "E7")
    return value


def _inside(root, relative):
    _relative(relative)
    path = _safe_source(root / relative, "E7", absolute=True)
    if not path.is_relative_to(root):
        _fail("E7", "bundle_path_outside_root")
    return path


def _file_record(path, relative, original_path=None):
    record = dict(path=relative, sha256=_hash_file(path, "E7"), bytes=path.stat().st_size)
    if original_path is not None:
        record["original_path"] = str(original_path)
    return record


def bundle(source_jsonl, locator, request_path, attachments_path, run_dir, *, conversation_id=None):
    """Prepare data only, using a 1-based physical JSONL line locator.

    Message ordinals count every response_item message, including excluded roles
    and analysis messages, independently of physical lines. Missing session ids
    remain null unless conversation_id explicitly requires a matching session.
    ValueError prefixes E6/E7 identify source/attachment exclusions respectively.
    """
    source = _safe_source(source_jsonl, "E6")
    request_source = _safe_source(request_path, "E6")
    descriptor_source = _safe_source(attachments_path, "E7")
    _private(run_dir, "E7")
    request_raw = _read_bytes(request_source, "E6")
    try:
        request = request_raw.decode("utf-8")
    except UnicodeError as exc:
        _fail("E6", f"request_not_utf8:{exc}")
    if not request:
        _fail("E6", "empty_request")
    context, target, source_hash = _extract(source, locator, request, conversation_id)
    descriptor_raw = _read_bytes(descriptor_source, "E7")
    descriptor_hash = ledger.sha(descriptor_raw)
    descriptor = _json(descriptor_raw, "E7")
    if (not isinstance(descriptor, dict) or set(descriptor) != {"schema", "required"}
            or descriptor.get("schema") != ATTACHMENTS_SCHEMA or not isinstance(descriptor.get("required"), list)):
        _fail("E7", "attachments_schema")
    required = []
    for original in descriptor["required"]:
        path = _safe_source(original, "E7", absolute=True)
        if any(path == existing[0] for existing in required):
            _fail("E7", "duplicate_required_attachment")
        required.append((path, _inventory(path)))
    output_path = Path(run_dir).absolute()
    if any(output_path == path or output_path.is_relative_to(path) for path, _ in required):
        _fail("E7", "output_inside_attachment")
    # Reject junctions on existing ancestors as well as the ledger's symlink checks.
    for ancestor in output_path.parents:
        if ancestor.exists():
            _safe_source(ancestor, "E7", absolute=True)
            break
    out = ledger.new_directory(run_dir)
    with (out / "request.txt").open("xb") as file:
        file.write(request_raw)
    ledger.write_json(out / "context.json", context)
    with (out / "attachments.json").open("xb") as file:
        file.write(descriptor_raw)
    mappings = []
    for index, (original, inventory) in enumerate(required, 1):
        prefix = f"attachments/{index:04d}/data"
        entries = []
        for member in inventory:
            relative = prefix + ("/" + member["relative"] if member["relative"] else "")
            destination = out / relative
            source_member = original / member["relative"] if member["relative"] else original
            if member["kind"] == "directory":
                destination.mkdir(parents=True, exist_ok=False)
                entries.append(dict(path=relative, kind="directory"))
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            _safe_source(source_member, "E7", absolute=True)
            if _hash_file(source_member, "E7") != member["sha256"]:
                _fail("E7", "attachment_changed")
            try:
                with source_member.open("rb") as reader, destination.open("xb") as writer:
                    shutil.copyfileobj(reader, writer)
            except OSError as exc:
                _fail("E7", f"attachment_copy_failed:{exc}")
            if (_hash_file(source_member, "E7") != member["sha256"]
                    or _hash_file(destination, "E7") != member["sha256"]):
                _fail("E7", "attachment_changed")
            entries.append(dict(path=relative, kind="file", sha256=member["sha256"], bytes=member["bytes"]))
        if _inventory(original) != inventory:
            _fail("E7", "attachment_changed")
        mappings.append(dict(original_path=descriptor["required"][index-1], path=prefix,
                             kind=inventory[0]["kind"], entries=entries))
    if _hash_file(source, "E6") != source_hash:
        _fail("E6", "source_changed")
    if _hash_file(descriptor_source, "E7") != descriptor_hash:
        _fail("E7", "attachments_descriptor_changed")
    document = dict(schema=SCHEMA, source=dict(path=str(source), sha256=source_hash),
                    conversation_id=context["conversation_id"],
                    locator=dict(line=locator, ordinal=target["ordinal"]),
                    request=_file_record(out / "request.txt", "request.txt", request_source),
                    context=_file_record(out / "context.json", "context.json"),
                    attachments_descriptor=_file_record(out / "attachments.json", "attachments.json", descriptor_source),
                    attachments=mappings)
    ledger.write_json(out / "bundle.json", document)
    return document


def _check_file(root, record, expected=None):
    if not isinstance(record, dict) or not {"path", "sha256", "bytes"}.issubset(record):
        _fail("E7", "bundle_file_schema")
    allowed = {"path", "sha256", "bytes"}
    if expected in ("request.txt", "attachments.json"):
        allowed.add("original_path")
    elif expected is None:
        allowed.add("kind")
    if set(record) != allowed:
        _fail("E7", "bundle_file_schema")
    if "original_path" in record:
        if not isinstance(record["original_path"], str):
            _fail("E7", "bundle_file_schema")
        _private(record["original_path"], "E7")
    if expected is not None and record["path"] != expected:
        _fail("E7", "bundle_file_path")
    path = _inside(root, record["path"])
    if not path.is_file() or type(record["bytes"]) is not int or record["bytes"] < 0 or not _digest(record["sha256"]):
        _fail("E7", "bundle_file_schema")
    if path.stat().st_size != record["bytes"] or _hash_file(path, "E7") != record["sha256"]:
        _fail("E7", "bundle_hash_mismatch")
    return path


def verify_bundle(path):
    """Validate only copied data, never reopen original source/attachment paths.

    Accept a bundle directory or its bundle.json. Return the validated descriptor.
    Content hashes detect mutation; authenticity of bundle.json is frozen externally.
    """
    selected = _safe_source(path, "E7")
    root = selected if selected.is_dir() else selected.parent
    manifest = root / "bundle.json"
    if selected.is_file() and selected.name != "bundle.json":
        _fail("E7", "bundle_manifest_path")
    document = _json(_read_bytes(_safe_source(manifest, "E7"), "E7"), "E7")
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        _fail("E7", "bundle_schema")
    if set(document) != {"schema", "source", "conversation_id", "locator", "request", "context", "attachments_descriptor", "attachments"}:
        _fail("E7", "bundle_schema")
    source = document["source"]
    locator = document["locator"]
    if (not isinstance(source, dict) or set(source) != {"path", "sha256"}
            or not isinstance(source["path"], str) or not _digest(source["sha256"])
            or not isinstance(locator, dict) or set(locator) != {"line", "ordinal"}
            or any(type(locator[k]) is not int or locator[k] < 1 for k in locator)
            or document["conversation_id"] is not None and not isinstance(document["conversation_id"], str)):
        _fail("E7", "bundle_source_schema")
    _private(source["path"], "E7")
    request_path = _check_file(root, document["request"], "request.txt")
    try:
        if not _read_bytes(request_path, "E7").decode("utf-8"):
            _fail("E7", "empty_request")
    except UnicodeError:
        _fail("E7", "request_not_utf8")
    context_path = _check_file(root, document["context"], "context.json")
    context = _json(_read_bytes(context_path, "E7"), "E7")
    _verify_context(context, document)
    descriptor_path = _check_file(root, document["attachments_descriptor"], "attachments.json")
    descriptor = _json(_read_bytes(descriptor_path, "E7"), "E7")
    mappings = document["attachments"]
    if (not isinstance(descriptor, dict) or set(descriptor) != {"schema", "required"}
            or descriptor.get("schema") != ATTACHMENTS_SCHEMA or not isinstance(descriptor.get("required"), list)
            or not isinstance(mappings, list) or len(mappings) != len(descriptor["required"])):
        _fail("E7", "attachments_schema")
    expected_paths = {"bundle.json", "request.txt", "context.json", "attachments.json"}
    for index, mapping in enumerate(mappings, 1):
        if not isinstance(mapping, dict) or set(mapping) != {"original_path", "path", "kind", "entries"}:
            _fail("E7", "attachment_mapping_schema")
        original = descriptor["required"][index-1]
        if not isinstance(original, str) or mapping["original_path"] != original:
            _fail("E7", "attachment_mapping_source")
        _private(original, "E7")
        if not (Path(original).is_absolute() or PureWindowsPath(original).is_absolute()):
            _fail("E7", "attachment_path_not_absolute")
        if ".." in original.replace("\\", "/").split("/"):
            _fail("E7", "path_traversal")
        prefix = f"attachments/{index:04d}/data"
        if mapping["path"] != prefix or mapping["kind"] not in ("file", "directory"):
            _fail("E7", "attachment_mapping_path")
        entries = mapping["entries"]
        if not isinstance(entries, list) or not entries:
            _fail("E7", "attachment_entries_schema")
        for member in entries:
            if not isinstance(member, dict) or member.get("kind") not in ("file", "directory"):
                _fail("E7", "attachment_entry_schema")
            relative = _relative(member.get("path"))
            if not (relative == prefix or relative.startswith(prefix + "/")) or relative in expected_paths:
                _fail("E7", "attachment_entry_path")
            expected_paths.add(relative)
            if member["kind"] == "file":
                if set(member) != {"path", "kind", "sha256", "bytes"}:
                    _fail("E7", "attachment_entry_schema")
                _check_file(root, member)
            elif set(member) != {"path", "kind"} or not _inside(root, relative).is_dir():
                _fail("E7", "attachment_directory_schema")
        if entries[0]["path"] != prefix or entries[0]["kind"] != mapping["kind"]:
            _fail("E7", "attachment_root_mismatch")
    # No unlisted files (or links) can silently enter the typed runtime data.
    def check_members(directory):
        for item in sorted(directory.iterdir(), key=lambda child: child.name):
            _safe_source(item, "E7", absolute=True)
            relative = item.relative_to(root).as_posix()
            if relative not in expected_paths and not (item.is_dir() and any(p.startswith(relative + "/") for p in expected_paths)):
                _fail("E7", "unlisted_bundle_member")
            if item.is_dir():
                check_members(item)

    try:
        check_members(root)
    except OSError as exc:
        _fail("E7", f"unreadable_bundle:{exc}")
    return document


def _digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _verify_context(context, document):
    if (not isinstance(context, dict) or set(context) != {"schema", "source_sha256", "conversation_id", "locator", "window", "messages"}
            or context.get("schema") != CONTEXT_SCHEMA or context["source_sha256"] != document["source"]["sha256"]
            or context["conversation_id"] != document["conversation_id"] or context["locator"] != document["locator"]
            or not isinstance(context["messages"], list) or not isinstance(context["window"], dict)):
        _fail("E7", "context_schema")
    previous_line, previous_ordinal, total = 0, 0, 0
    for message in context["messages"]:
        if (not isinstance(message, dict) or set(message) != {"line", "ordinal", "role", "blocks", "chars"}
                or message["role"] not in ("user", "assistant") or not isinstance(message["blocks"], list)
                or type(message["line"]) is not int or not previous_line < message["line"] < document["locator"]["line"]
                or type(message["ordinal"]) is not int or not previous_ordinal < message["ordinal"] < document["locator"]["ordinal"]):
            _fail("E7", "context_message_schema")
        chars, previous_block = 0, 0
        for block in message["blocks"]:
            if (not isinstance(block, dict) or set(block) != {"index", "type", "text"}
                    or type(block["index"]) is not int or block["index"] <= previous_block
                    or not isinstance(block["type"], str) or block["type"] not in TEXT_TYPES or not isinstance(block["text"], str)):
                _fail("E7", "context_block_schema")
            previous_block = block["index"]
            chars += len(block["text"])
        if type(message["chars"]) is not int or chars != message["chars"]:
            _fail("E7", "context_character_count")
        total += chars
        previous_line, previous_ordinal = message["line"], message["ordinal"]
    window = context["window"]
    keys = {"limit_chars", "chars", "eligible_messages", "included_messages", "omitted_messages", "cut", "first_line", "last_line"}
    if (set(window) != keys or window["limit_chars"] != WINDOW_CHARS or window["chars"] != total or total > WINDOW_CHARS
            or any(type(window[k]) is not int or window[k] < 0 for k in ("chars", "eligible_messages", "included_messages", "omitted_messages"))
            or window["included_messages"] != len(context["messages"])
            or window["eligible_messages"] != window["included_messages"] + window["omitted_messages"]
            or type(window["cut"]) is not bool or window["cut"] != (window["omitted_messages"] > 0)
            or window["first_line"] != (context["messages"][0]["line"] if context["messages"] else None)
            or window["last_line"] != (context["messages"][-1]["line"] if context["messages"] else None)):
        _fail("E7", "context_window_schema")


def bundle_prepared_request(request_path, input_manifest, prepared_path, run_dir, *, context_path=None):
    """Direct immutable intake; integrity is not eligibility or a pilot result."""
    if __package__:
        from . import cad_verify_v4_inputs as inputs, cad_verify_v4_s1 as s1
    else:
        import cad_verify_v4_inputs as inputs, cad_verify_v4_s1 as s1
    request_path = s1.safe_path(request_path, regular=True)
    input_manifest = s1.safe_path(input_manifest, regular=True)
    prepared_path = s1.safe_path(prepared_path, regular=True)
    manifest = inputs.load_manifest(input_manifest)
    if manifest["evidence_mode"] != "independent_dev":
        _fail("E7", "s1_intake_independent_dev_only")
    inputs.verify_prepared(prepared_path, input_manifest)
    original = {name: ledger.file_sha(path) for name, path in
                (("request", request_path), ("input_manifest", input_manifest), ("prepared", prepared_path))}
    if context_path is not None:
        context_path = s1.safe_path(context_path, regular=True)
        original["context"] = ledger.file_sha(context_path)
    request_raw = request_path.read_bytes()
    request_raw.decode("utf-8")
    out = ledger.new_directory(s1.safe_path(run_dir))
    with (out / "request.txt").open("xb") as file:
        file.write(request_raw)
    reserved = {"request.txt", "inputs.json", "prepared.json", "context.txt", "bundle.json"}
    for asset_id, record in manifest["assets"].items():
        if record["path"] in reserved:
            _fail("E7", "direct_attachment_reserved_path")
        resolved = inputs.resolve_asset(input_manifest, asset_id)
        source = s1.safe_path(resolved["path"], regular=True)
        inventory = _inventory(source)
        destination = out / record["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copyfile(source, destination)
        if (ledger.file_sha(destination) != record["sha256"]
                or destination.stat().st_size != record["bytes"] or _inventory(source) != inventory):
            _fail("E7", "direct_attachment_changed")
    # Preserve manifest and prepared packet bytes, including their original hash
    # provenance. Moving the bundle is safe because asset paths are relative.
    shutil.copyfile(input_manifest, out / "inputs.json")
    shutil.copyfile(prepared_path, out / "prepared.json")
    inputs.verify_prepared(out / "prepared.json", out / "inputs.json")
    if context_path is not None:
        context_raw = context_path.read_bytes()
        context_raw.decode("utf-8")
        with (out / "context.txt").open("xb") as file:
            file.write(context_raw)
    sources = dict(request=request_path, input_manifest=input_manifest, prepared=prepared_path)
    if context_path is not None:
        sources["context"] = context_path
    if any(ledger.file_sha(path) != original[name] for name, path in sources.items()):
        _fail("E7", "direct_source_changed")
    files = {path.relative_to(out).as_posix(): dict(sha256=ledger.file_sha(path), bytes=path.stat().st_size)
             for path in sorted(out.rglob("*")) if path.is_file()}
    document = dict(schema="cad-harness.prepared-request-bundle.v4c", profile="c-s1",
                    origin="direct_user", evidence_mode="independent_dev", source_sha256=original,
                    request="request.txt", input_manifest="inputs.json", prepared="prepared.json",
                    context="context.txt" if context_path is not None else None, files=files,
                    integrity_only=True, eligibility=None, pilot="not_run", live_calls=0)
    ledger.write_json(out / "bundle.json", document)
    verify_prepared_bundle(out / "bundle.json")
    return document


def verify_prepared_bundle(path):
    """Check copied bytes only; never reopen a historical JSONL or source path."""
    if __package__:
        from . import cad_verify_v4_inputs as inputs, cad_verify_v4_s1 as s1
    else:
        import cad_verify_v4_inputs as inputs, cad_verify_v4_s1 as s1
    path = s1.safe_path(path, regular=True)
    document = ledger.read_json(path)
    required = {"schema", "profile", "origin", "evidence_mode", "source_sha256", "request",
                "input_manifest", "prepared", "context", "files", "integrity_only",
                "eligibility", "pilot", "live_calls"}
    if (not isinstance(document, dict) or set(document) != required
            or document.get("schema") != "cad-harness.prepared-request-bundle.v4c"
            or document.get("profile") != "c-s1" or document.get("origin") != "direct_user"
            or document.get("evidence_mode") != "independent_dev"
            or document.get("integrity_only") is not True or document.get("eligibility") is not None
            or document.get("pilot") != "not_run" or document.get("live_calls") != 0
            or document.get("request") != "request.txt" or document.get("input_manifest") != "inputs.json"
            or document.get("prepared") != "prepared.json" or document.get("context") not in (None, "context.txt")
            or not isinstance(document.get("files"), dict)):
        _fail("E7", "direct_bundle_contract")
    expected = set(document["files"]) | {path.name}
    actual = set()
    for item in path.parent.rglob("*"):
        s1.safe_path(item)
        if item.is_file():
            actual.add(item.relative_to(path.parent).as_posix())
    if actual != expected:
        _fail("E7", "direct_bundle_file_set")
    for name, record in document["files"].items():
        candidate = _inside(path.parent, name)
        s1.safe_path(candidate, regular=True)
        if (not isinstance(record, dict) or set(record) != {"sha256", "bytes"}
                or not _digest(record["sha256"]) or type(record["bytes"]) is not int
                or candidate.stat().st_size != record["bytes"]
                or ledger.file_sha(candidate) != record["sha256"]):
            _fail("E7", "direct_bundle_hash")
    mandatory = {document["request"], document["input_manifest"], document["prepared"]}
    if document["context"] is not None:
        mandatory.add(document["context"])
    if not mandatory <= set(document["files"]):
        _fail("E7", "direct_bundle_required_file")
    source_hashes = document["source_sha256"]
    keys = {"request", "input_manifest", "prepared"} | ({"context"} if document["context"] else set())
    if not isinstance(source_hashes, dict) or set(source_hashes) != keys or not all(_digest(v) for v in source_hashes.values()):
        _fail("E7", "direct_bundle_provenance")
    for source, member in (("request", "request.txt"), ("input_manifest", "inputs.json"),
                           ("prepared", "prepared.json"), ("context", document["context"])):
        if member is not None and document["files"][member]["sha256"] != source_hashes[source]:
            _fail("E7", "direct_source_changed")
    manifest = inputs.load_manifest(path.parent / document["input_manifest"])
    if manifest["evidence_mode"] != "independent_dev":
        _fail("E7", "direct_bundle_evidence_mode")
    inputs.verify_prepared(path.parent / document["prepared"], path.parent / document["input_manifest"])
    return document
