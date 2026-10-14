"""Pilot extraction fixtures only: no historical/private data or live CAD/model calls."""
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_pilot as pilot
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


def message(role, text, *, channel=None, blocks=None):
    payload = dict(type="message", role=role, content=blocks if blocks is not None else
                   [dict(type="input_text" if role == "user" else "output_text", text=text)])
    if channel is not None:
        payload["channel"] = channel
    return dict(type="response_item", payload=payload)


class PilotBundle(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).absolute()
        self.source = self.root / "session.jsonl"
        self.request = self.root / "request-source.txt"
        self.attachments = self.root / "required.json"
        self.out = self.root / "prepared"
        self.request.write_bytes("build café\r\n直径 10 😀".encode("utf-8"))
        self.required([])
        self.rows = [dict(type="session_meta", payload=dict(id="fixture-conversation")),
                     message("user", "earlier request"),
                     message("assistant", "earlier answer"),
                     # Decode bytes directly to preserve CRLF in the request.
                     message("user", "wrapper prefix\n" + self.request.read_bytes().decode("utf-8"))]
        self.save()
        for name in ("subprocess.run", "subprocess.Popen"):
            item = patch(name, side_effect=AssertionError("live calls prohibited"))
            item.start()
            self.addCleanup(item.stop)

    def save(self):
        self.source.write_bytes(b"\n".join(json.dumps(row, ensure_ascii=False).encode("utf-8") for row in self.rows) + b"\n")

    def required(self, paths):
        self.attachments.write_text(json.dumps(dict(schema=pilot.ATTACHMENTS_SCHEMA,
                                                   required=[str(path) for path in paths])), encoding="utf-8")

    def prepare(self, *, locator=None, conversation_id="fixture-conversation"):
        return pilot.bundle(self.source, len(self.rows) if locator is None else locator,
                            self.request, self.attachments, self.out, conversation_id=conversation_id)

    def context(self):
        return json.loads((self.out / "context.json").read_text(encoding="utf-8"))

    def mutate_manifest(self, fn):
        path = self.out / "bundle.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        fn(document)
        path.write_text(json.dumps(document), encoding="utf-8")

    def test_exact_request_and_ordered_blocks_excluding_target_tools_and_analysis(self):
        self.rows = [self.rows[0],
                     message("system", "system instruction"),
                     dict(type="event_msg", payload=dict(type="agent_message", message="not a response")),
                     message("user", "", blocks=[dict(type="input_text", text="a\r\n"),
                                                        dict(type="image", image_url="data:fixture"),
                                                        dict(type="text", text="😀")]),
                     message("assistant", "private analysis", channel="analysis"),
                     dict(type="response_item", payload=dict(type="function_call", arguments="tool instruction")),
                     dict(type="response_item", payload=dict(type="function_call_output", output="tool output")),
                     message("tool", "tool-role output"),
                     message("assistant", "", blocks=[dict(type="analysis", text="hidden"),
                                                             dict(type="output_text", text="verbatim answer\n")]),
                     self.rows[-1], message("assistant", "after target")]
        self.save()
        document = self.prepare(locator=10)
        self.assertEqual((self.out / "request.txt").read_bytes(), self.request.read_bytes())
        self.assertEqual(document["locator"], dict(line=10, ordinal=6))
        context = self.context()
        self.assertEqual([(m["line"], m["ordinal"], m["role"]) for m in context["messages"]],
                         [(4, 2, "user"), (9, 5, "assistant")])
        self.assertEqual(context["messages"][0]["blocks"],
                         [dict(index=1, type="input_text", text="a\r\n"), dict(index=3, type="text", text="😀")])
        self.assertEqual(context["messages"][1]["blocks"],
                         [dict(index=2, type="output_text", text="verbatim answer\n")])
        self.assertEqual(pilot.verify_bundle(self.out), document)
        self.assertEqual(pilot.verify_bundle(self.out / "bundle.json"), document)

    def test_window_counts_unicode_and_stops_at_whole_message_boundary(self):
        self.rows = [self.rows[0], message("user", "old"), message("assistant", "界" * 20001),
                     message("user", "😀" * 19999), self.rows[-1]]
        self.save()
        self.prepare()
        context = self.context()
        self.assertEqual([m["line"] for m in context["messages"]], [3, 4])
        self.assertEqual(context["window"], dict(limit_chars=40000, chars=40000, eligible_messages=3,
                         included_messages=2, omitted_messages=1, cut=True, first_line=3, last_line=4))
        pilot.verify_bundle(self.out)

    def test_oversized_newest_message_does_not_skip_back_to_smaller_older_one(self):
        self.rows = [self.rows[0], message("user", "fits"), message("assistant", "x" * 40001), self.rows[-1]]
        self.save()
        self.prepare()
        self.assertEqual(self.context()["messages"], [])
        self.assertEqual(self.context()["window"]["omitted_messages"], 2)
        self.assertTrue(self.context()["window"]["cut"])

    def test_locator_is_physical_line_not_message_ordinal(self):
        with self.assertRaisesRegex(ValueError, "E6:locator_request_mismatch"):
            self.prepare(locator=2)
        self.assertFalse(self.out.exists())

    def test_mismatched_request_and_missing_target_are_e6(self):
        self.rows[-1] = message("user", "a rewritten request is not acceptable")
        self.save()
        with self.assertRaisesRegex(ValueError, "E6:locator_request_mismatch"):
            self.prepare()
        for locator in (1, 100, 0, True, "4"):
            with self.subTest(locator=locator), self.assertRaisesRegex(ValueError, "E6:"):
                self.prepare(locator=locator)

    def test_conversation_identity_must_match_session_meta(self):
        with self.assertRaisesRegex(ValueError, "E6:conversation_id_mismatch"):
            self.prepare(conversation_id="another-conversation")
        self.rows[0] = dict(type="event_msg", payload={})
        self.save()
        with self.assertRaisesRegex(ValueError, "E6:conversation_id_mismatch"):
            self.prepare()

    def test_missing_or_malformed_jsonl_is_e6(self):
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, "E6:"):
            self.prepare()
        for malformed in (b"{not json}\n", b"\xff\n", b"{}\n", b"\n"):
            self.source.write_bytes(malformed)
            with self.subTest(malformed=malformed), self.assertRaisesRegex(ValueError, "E6:"):
                self.prepare()
        self.save()
        with self.source.open("ab") as file:
            file.write(b"malformed after target\n")
        with self.assertRaisesRegex(ValueError, "E6:"):
            self.prepare()

    def test_missing_unreadable_and_malformed_attachment_descriptor_are_e7(self):
        self.required([self.root / "missing.step"])
        with self.assertRaisesRegex(ValueError, "E7:"):
            self.prepare()
        attachment = self.root / "unreadable.step"
        attachment.write_bytes(b"fixture geometry bytes")
        self.required([attachment])
        original_hash = pilot.ledger.file_sha

        def unreadable(path):
            if Path(path) == attachment:
                raise PermissionError("fixture unreadable")
            return original_hash(path)

        with patch.object(pilot.ledger, "file_sha", side_effect=unreadable), self.assertRaisesRegex(ValueError, "E7:"):
            self.prepare()
        self.attachments.write_text('{"required": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "E7:attachments_schema"):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_recursive_members_are_sorted_and_originals_not_needed_for_verification(self):
        folder = self.root / "original-geometry"
        folder.mkdir()
        (folder / "z.step").write_bytes(b"z\x00\xff")
        (folder / "a.step").write_bytes(b"a")
        (folder / "empty").mkdir()
        single = self.root / "single.bin"
        single.write_bytes(b"single bytes")
        self.required([folder, single])
        document = self.prepare()
        entries = document["attachments"][0]["entries"]
        self.assertEqual([entry["path"] for entry in entries],
                         ["attachments/0001/data", "attachments/0001/data/a.step",
                          "attachments/0001/data/empty", "attachments/0001/data/z.step"])
        self.assertEqual((self.out / "attachments/0001/data/z.step").read_bytes(), b"z\x00\xff")
        single.unlink()
        self.source.unlink()
        self.request.unlink()
        self.attachments.unlink()
        self.assertEqual(pilot.verify_bundle(self.out), document)
        with self.assertRaisesRegex(ValueError, "output_exists_or_linked"):
            # Existing output rejection is independent of source existence.
            pilot.ledger.new_directory(self.out)

    def test_traversal_and_relative_attachments_rejected(self):
        existing = self.root / "exists.step"
        existing.write_bytes(b"fixture")
        for path in ("relative.step", str(self.root / "sub" / ".." / "exists.step")):
            self.required([path])
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "E7:"):
                self.prepare()

    def test_mocked_symlink_and_junction_rejected_without_following(self):
        attachment = self.root / "linked.step"
        attachment.write_bytes(b"never follow")
        self.required([attachment])
        original_lstat = Path.lstat
        for mode, attributes in ((stat.S_IFLNK | 0o777, 0), (stat.S_IFREG | 0o666, 0x400)):
            def linked(path, *, follow_symlinks=False):
                if path == attachment:
                    return SimpleNamespace(st_mode=mode, st_file_attributes=attributes)
                return original_lstat(path)

            with self.subTest(attributes=attributes), patch.object(Path, "lstat", linked), self.assertRaisesRegex(ValueError, "E7:linked_path"):
                self.prepare()

    def test_private_paths_rejected_before_any_filesystem_lookup(self):
        # This is a lexical guard test; no private directory is opened or stat'ed.
        value = "C:/dev/v4-holdout-private/do-not-open"
        with patch.object(Path, "lstat", side_effect=AssertionError("filesystem lookup forbidden")):
            with self.assertRaisesRegex(ValueError, "E7:private_holdout_path_forbidden"):
                pilot._safe_source(value, "E7", absolute=True)
        self.required([value])
        with self.assertRaisesRegex(ValueError, "E7:private_holdout_path_forbidden"):
            self.prepare()

    def test_changed_source_is_e6(self):
        original_hash = pilot.ledger.file_sha
        calls = 0

        def changed(path):
            nonlocal calls
            if Path(path) == self.source:
                calls += 1
                if calls >= 2:
                    return "0" * 64
            return original_hash(path)

        with patch.object(pilot.ledger, "file_sha", side_effect=changed), self.assertRaisesRegex(ValueError, "E6:source_changed"):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_changed_attachment_during_copy_is_e7(self):
        attachment = self.root / "changing.step"
        attachment.write_bytes(b"before")
        self.required([attachment])
        original_copy = pilot.shutil.copyfileobj

        def changing(reader, writer):
            original_copy(reader, writer)
            attachment.write_bytes(b"after")

        with patch.object(pilot.shutil, "copyfileobj", side_effect=changing), self.assertRaisesRegex(ValueError, "E7:attachment_changed"):
            self.prepare()
        self.assertFalse((self.out / "bundle.json").exists())

    def test_tampered_request_context_and_copy_fail_integrity(self):
        attachment = self.root / "source.step"
        attachment.write_bytes(b"original")
        self.required([attachment])
        self.prepare()
        for relative in ("request.txt", "context.json", "attachments/0001/data"):
            target = self.out / relative
            original = target.read_bytes()
            target.write_bytes(b"tampered")
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "E7:bundle_hash_mismatch"):
                pilot.verify_bundle(self.out)
            target.write_bytes(original)

    def test_manifest_traversal_schema_and_unlisted_members_rejected(self):
        attachment = self.root / "source.step"
        attachment.write_bytes(b"original")
        self.required([attachment])
        self.prepare()
        manifest = (self.out / "bundle.json").read_bytes()
        self.mutate_manifest(lambda document: document["attachments"][0]["entries"][0].update(path="../source.step"))
        with self.assertRaisesRegex(ValueError, "E7:bundle_path_traversal"):
            pilot.verify_bundle(self.out)
        (self.out / "bundle.json").write_bytes(manifest)
        self.mutate_manifest(lambda document: document.update(schema="wrong"))
        with self.assertRaisesRegex(ValueError, "E7:bundle_schema"):
            pilot.verify_bundle(self.out)
        (self.out / "bundle.json").write_bytes(manifest)
        (self.out / "extra.txt").write_bytes(b"not declared")
        with self.assertRaisesRegex(ValueError, "E7:unlisted_bundle_member"):
            pilot.verify_bundle(self.out)


if __name__ == "__main__":
    unittest.main()
