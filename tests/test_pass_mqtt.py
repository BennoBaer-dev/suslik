"""Pure-offline tests for pass-level MQTT (core.pass_mqtt / core.passbild / verifyd hooks).

No network, no MQTT, no real data, no pytest. All fixtures are synthetic temp dirs.
Run from the worktree root: python3 -m unittest discover -s tests -v
"""
import ast
import base64
import copy
import datetime
import io
import json
import os
import re
import shutil
import tempfile
import unittest
import uuid
from unittest import mock

from PIL import Image

from core import pass_mqtt as pm
from core import passbild as pb

BASE = int(datetime.datetime(2026, 3, 1, 12, 0, 0).timestamp())

# A deterministic, valid 16x12 JPEG (solid colour). Used as synthetic frame bytes.
JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA0JCgsKCA0LCgsODg0PEyAVExISEyccHhcgLikxMC4pLSwzOko+MzZGNywtQFdBRkxOUlNSMj5aYVpQYEpRUk//2wBDAQ4ODhMREyYVFSZPNS01T09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0//wAARCAAMABADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDmaKKK8o+/P//Z"
)

PASS_KEYS = {"pass_key", "start", "ende", "eids", "categories", "kamera_first_seen",
             "camera_sequence", "inferred_direction", "people", "segments"}
SEG_KEYS = {"index", "window", "eids", "counts", "camera_sequence", "camera_first_seen",
            "inferred_direction", "people", "categories", "frames"}
COUNT_KEYS = {"events", "frames", "known_people", "unknown"}
FRAME_KEYS = {"id", "eid", "camera", "ts", "kind", "url", "score"}
PAYLOAD_KEYS = {"schema", "herkunft", "pass_key", "segment", "segments", "status",
                "revision", "window", "eids", "counts", "camera_sequence",
                "camera_first_seen", "inferred_direction", "people", "categories",
                "frames", "contact_url"}
REV_RE = re.compile(r"^[0-9a-f]{12}$")
EID_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_.-]{0,63}$")
EVENT_URL_RE = re.compile(r"^/events/[0-9A-Za-z._-]+/[0-9A-Za-z._-]+\.jpg$")
REF_URL_RE = re.compile(r"^/lernlauf/satz/[0-9a-f]+\?klein=1$")
VERIFYD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "verifyd.py")

def verifyd_func_src(name):
    """Function source from verifyd.py, parsed as text (never imported). -> str"""
    with open(VERIFYD, encoding="utf-8") as f:
        src = f.read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node) or ""
    return ""


def row(eid, start, *, camera="cam-a", bestaetigt=(), kategorie=None, **extra):
    """A synthetic event row (person names are deliberately generic)."""
    d = {"eid": eid, "start": int(start), "ts": int(start), "camera": camera,
         "bestaetigt": list(bestaetigt), "max_bw": 1.0,
         "ours": {p: {"max": 0.8} for p in bestaetigt}, "kategorie": kategorie}
    d.update(extra)
    return d


def frame(nr, *, eid=None, camera="cam-a", kind="event", ts=None):
    eid = eid or "e%d" % nr
    return {"id": "%s|%s|shot_%02d.jpg" % (eid, kind, nr), "eid": eid,
            "camera": camera, "ts": ts if ts is not None else BASE + nr,
            "kind": kind, "url": "/events/%s/shot_%02d.jpg" % (eid, nr),
            "score": 0.5}


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="passmqtt-offline-")
        self.cfg = {"data_dir": self.tmp, "szene_karenz_s": 7,
                    "mqtt": {"topic_praefix": "offline-test"}}
        self.now = BASE + 7200

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def passe(self, by_h, **kw):
        return pm.paesse(self.cfg, by_h, jetzt=self.now, **kw)

    def frames_dir(self, name="frames"):
        d = os.path.join(self.tmp, name)
        os.makedirs(d, exist_ok=True)
        return d

    def write_show_images(self, directory, n, eid="e1"):
        for i in range(n):
            with open(os.path.join(directory, "clip_show_Person_A_%02d.jpg" % i), "wb") as f:
                f.write(JPEG)

    def write_ref_rows(self, directory, n, *, ext="png", archiv=False, leer=()):
        """kandidaten.jsonl + echte Profildateien; IDs in `leer` bleiben bildlos. -> list"""
        ids = []
        with open(os.path.join(directory, "kandidaten.jsonl"), "w", encoding="utf-8") as f:
            for i in range(n):
                rid = "%012x" % (i + 1)
                z = {"eid": "e1", "ref_id": rid, "person": "Person A",
                     "score": 0.9 - i * 0.01, "datei": "ref_%02d.jpg" % i}
                f.write(json.dumps(z) + "\n")
                ids.append(rid)
        basis = os.path.join(self.tmp, "state", "archiv", "refquelle") if archiv \
            else os.path.join(self.tmp, "refquelle")
        for rid in ids:
            if rid in leer:
                continue
            d = os.path.join(basis, rid)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "profil." + ext), "wb") as f:
                f.write(JPEG)
        return ids


class TestConstantsAndGrouping(OfflineCase):
    def test_constants(self):
        self.assertEqual(pm.SCHEMA, "pass-v1")
        self.assertEqual((pm.MAX_SEGMENT_S, pm.MAX_SEGMENT_EVENTS), (600, 20))
        self.assertEqual((pm.ZIEL_BILDER, pm.MAX_BILDER, pm.MIN_BILDER), (10, 12, 8))

    def test_empty_by_h(self):
        self.assertEqual(self.passe({}), [])

    def test_single_pass_single_segment(self):
        by_h = {e: row(e, BASE + 5 * i) for i, e in enumerate(("e1", "e2", "e3"))}
        passe = self.passe(by_h)
        self.assertEqual(len(passe), 1)
        snap = passe[0]
        self.assertTrue(PASS_KEYS <= set(snap))
        self.assertEqual(sorted(snap["eids"]), ["e1", "e2", "e3"])
        self.assertEqual(len(snap["segments"]), 1)
        seg = snap["segments"][0]
        self.assertTrue(SEG_KEYS <= set(seg))
        self.assertTrue(COUNT_KEYS <= set(seg["counts"]))
        self.assertEqual(seg["counts"]["events"], 3)

    def test_segment_600s_boundary(self):
        by_h = {"e%02d" % i: row("e%02d" % i, BASE + 60 * i) for i in range(12)}
        passe = self.passe(by_h)
        self.assertEqual(len(passe), 1)          # 60 s gaps stay inside one pass
        segs = passe[0]["segments"]
        self.assertGreaterEqual(len(segs), 2)
        self.assertEqual(sorted(e for s in segs for e in s["eids"]), sorted(by_h))
        self.assertEqual([s["index"] for s in segs], list(range(len(segs))))

    def test_segment_20_event_boundary(self):
        by_h = {"e%02d" % i: row("e%02d" % i, BASE + i) for i in range(21)}
        segs = self.passe(by_h)[0]["segments"]
        self.assertEqual(len(segs), 2)
        self.assertTrue(all(len(s["eids"]) <= pm.MAX_SEGMENT_EVENTS for s in segs))
        self.assertEqual(sum(len(s["eids"]) for s in segs), 21)

    def test_midnight_day_boundary(self):
        d1 = int(datetime.datetime(2026, 3, 1, 23, 58).timestamp())
        d2 = int(datetime.datetime(2026, 3, 2, 0, 1).timestamp())
        by_h = {"e1": row("e1", d1), "e2": row("e2", d2)}
        passe = self.passe(by_h)
        self.assertEqual(len(passe), 2)
        self.assertEqual([p["eids"] for p in passe], [["e1"], ["e2"]])
        self.assertNotEqual(passe[0]["pass_key"], passe[1]["pass_key"])

    def test_overlong_single_event_alone(self):
        by_h = {"solo": row("solo", BASE, ende=BASE + 3600)}
        passe = self.passe(by_h)
        self.assertEqual(len(passe), 1)
        self.assertEqual(passe[0]["eids"], ["solo"])
        self.assertEqual(len(passe[0]["segments"]), 1)
        self.assertEqual(passe[0]["segments"][0]["eids"], ["solo"])


    def test_late_event_recuts_and_rekeys(self):
        e1, e2, e3, e4 = "g1", "g2", "g3", "g4"
        basis = {e1: row(e1, BASE), e2: row(e2, BASE + 120)}
        first = self.passe(basis)[0]
        late = dict(basis)
        late[e3] = row(e3, BASE + 240)          # inside the 300 s gap
        second = self.passe(late)[0]
        self.assertEqual(second["pass_key"], first["pass_key"])
        self.assertEqual(sorted(second["eids"]), [e1, e2, e3])
        self.assertGreater(second["ende"], first["ende"])
        self.assertNotEqual(pm.revision(second["pass_key"], 0, second),
                            pm.revision(first["pass_key"], 0, first))
        self.assertEqual(second["segments"][0]["window"], [BASE, BASE + 240])

        far = dict(basis)
        far[e4] = row(e4, BASE + 600)           # beyond the gap -> new pass
        passe = self.passe(far)
        self.assertEqual(len(passe), 2)
        self.assertNotEqual(passe[0]["pass_key"], passe[1]["pass_key"])
        self.assertEqual([p["eids"] for p in passe], [[e1, e2], [e4]])
        for p in passe:
            seg_eids = [e for s in p["segments"] for e in s["eids"]]
            self.assertEqual(sorted(seg_eids), p["eids"])
        self.assertFalse(set(passe[0]["segments"][0]["eids"]) &
                         set(passe[1]["segments"][0]["eids"]))

class TestFrameSelection(OfflineCase):
    def _by_h(self, n=1):
        return {"e%d" % i: row("e%d" % i, BASE + i * 10) for i in range(1, n + 1)}

    def test_deterministic_across_runs(self):
        d = self.frames_dir()
        self.write_show_images(d, 6)
        self.write_ref_rows(d, 3)
        by_h = self._by_h()
        a = self.passe(by_h, event_dir=d)[0]["segments"][0]["frames"]
        b = self.passe(by_h, event_dir=d)[0]["segments"][0]["frames"]
        self.assertEqual(a, b)
        self.assertTrue(a)

    def test_count_bounds_and_per_event_cap(self):
        for i in range(1, 9):
            eid = "e%d" % i
            d = os.path.join(self.tmp, "events", eid)
            os.makedirs(d, exist_ok=True)
            self.write_show_images(d, 3, eid)
        by_h = self._by_h(8)
        frames = pm.frames_fuer_segment(self.cfg, sorted(by_h), by_h=by_h)
        self.assertEqual(len(frames), pm.MAX_BILDER)
        self.assertGreaterEqual(len({f["eid"] for f in frames}), pm.MIN_BILDER // 2)

    def test_ref_rows_preferred_over_show_files(self):
        d = os.path.join(self.tmp, "events", "e1")
        os.makedirs(d, exist_ok=True)
        self.write_show_images(d, 8, "e1")
        self.write_ref_rows(d, 6)
        frames = pm.frames_fuer_segment(self.cfg, ["e1"], by_h=self._by_h())
        self.assertTrue(frames)
        self.assertGreaterEqual(sum(1 for f in frames if f["kind"] == "ref"), 2)
        show_only = os.path.join(self.tmp, "events", "e2")
        os.makedirs(show_only, exist_ok=True)
        self.write_show_images(show_only, 8, "e2")
        other = pm.frames_fuer_segment(
            self.cfg, ["e2"], by_h={"e2": row("e2", BASE)})
        self.assertTrue(other)
        self.assertTrue(all(f["kind"] != "ref" for f in other))
        self.assertTrue(any(f["kind"] == "event" for f in other))
        self.assertNotEqual([f["id"] for f in frames], [f["id"] for f in other])

    def test_missing_frames_handled(self):
        empty = self.frames_dir("empty")
        by_h = self._by_h()
        self.assertEqual(pm.frames_fuer_segment(
            self.cfg, ["e1"], by_h=by_h, event_dir=empty), [])
        missing = frame(1)
        self.assertIsNone(pm.bild_bytes(self.cfg, missing))
        self.assertIsNone(pm.bild_bytes(self.cfg, None))

    def test_bild_bytes_reads_guarded_local_file(self):
        d = os.path.join(self.tmp, "events", "e1")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "shot.jpg"), "wb") as f:
            f.write(JPEG)
        self.assertEqual(pm.bild_bytes(self.cfg, frame(1) |
                         {"url": "/events/e1/shot.jpg"}), JPEG)
        evil = frame(1) | {"url": "/events/../secret/shot.jpg"}
        self.assertIsNone(pm.bild_bytes(self.cfg, evil))

    def test_ref_bytes_accepts_non12_hex(self):
        d = os.path.join(self.tmp, "refquelle", "abc12345")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "profil.png"), "wb") as f:
            f.write(JPEG)
        self.assertEqual(
            pm.bild_bytes(self.cfg, {"url": "/lernlauf/satz/abc12345?klein=1"}), JPEG)
        self.assertIsNone(pm.bild_bytes(
            self.cfg, {"url": "/lernlauf/satz/../etc/passwd"}))

    def test_ref_bytes_live_profile_webp(self):
        rid = "abc12345"
        d = os.path.join(self.tmp, "refquelle", rid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "profil.webp"), "wb") as f:
            f.write(JPEG)
        self.assertEqual(pm.bild_bytes(
            self.cfg, {"url": "/lernlauf/satz/%s?klein=1" % rid}), JPEG)

    def test_ref_bytes_archiv_profile_jpg(self):
        rid = "def67890"
        d = os.path.join(self.tmp, "state", "archiv", "refquelle", rid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "profil.jpg"), "wb") as f:
            f.write(JPEG)
        self.assertEqual(pm.bild_bytes(
            self.cfg, {"url": "/lernlauf/satz/%s?klein=1" % rid}), JPEG)

    def test_ref_bytes_missing_and_traversal_are_none(self):
        self.assertIsNone(pm.bild_bytes(
            self.cfg, {"url": "/lernlauf/satz/99999999?klein=1"}))
        for url in ("/lernlauf/satz/../etc/passwd",
                    "/lernlauf/satz/../etc/passwd?klein=1"):
            self.assertIsNone(pm.bild_bytes(self.cfg, {"url": url}))

    def test_missing_ref_set_does_not_break_selection(self):
        eid = "e1"
        d = os.path.join(self.tmp, "events", eid)
        os.makedirs(d, exist_ok=True)
        self.write_show_images(d, 4, eid)
        ids = self.write_ref_rows(d, 2, leer=("%012x" % 1, "%012x" % 2))
        self.assertEqual(len(ids), 2)
        by_h = {eid: row(eid, BASE)}
        a = pm.frames_fuer_segment(self.cfg, [eid], by_h=by_h)
        b = pm.frames_fuer_segment(self.cfg, [eid], by_h=by_h)
        self.assertTrue(a)
        self.assertEqual(a, b)
        self.assertTrue(all(f["kind"] != "ref" for f in a))

    def test_unreadable_refs_fill_from_show_candidates(self):
        eid = "e1"
        d = os.path.join(self.tmp, "events", eid)
        os.makedirs(d, exist_ok=True)
        self.write_show_images(d, 6, eid)
        self.write_ref_rows(d, 4, leer=tuple("%012x" % (i + 1) for i in range(4)))
        snap = self.passe({eid: row(eid, BASE)})[0]
        seg = snap["segments"][0]
        frames = seg["frames"]
        self.assertTrue(frames)
        self.assertEqual(seg["counts"]["frames"], len(frames))
        self.assertTrue(all("placeholder" not in f["id"].lower() for f in frames))
        self.assertTrue(all(f["id"].count("|") == 2 for f in frames))
        self.assertTrue(all(f["kind"] != "ref" for f in frames))

    def test_only_two_usable_candidates_stay_two(self):
        eid = "e1"
        d = os.path.join(self.tmp, "events", eid)
        os.makedirs(d, exist_ok=True)
        self.write_show_images(d, 2, eid)
        frames = pm.frames_fuer_segment(self.cfg, [eid], by_h={eid: row(eid, BASE)})
        self.assertEqual(len(frames), 2)

    def test_fill_to_min_when_all_candidates_one_eid(self):
        d = self.frames_dir("one-eid")
        self.write_show_images(d, 12, "e1")
        self.write_ref_rows(d, 12)
        by_h = {"e1": row("e1", BASE)}
        a = pm.frames_fuer_segment(self.cfg, ["e1"], by_h=by_h, event_dir=d)
        b = pm.frames_fuer_segment(self.cfg, ["e1"], by_h=by_h, event_dir=d)
        self.assertTrue(pm.MIN_BILDER <= len(a) <= pm.MAX_BILDER)
        self.assertEqual(a, b)
        for f in a:
            self.assertTrue(EVENT_URL_RE.match(f["url"]) or REF_URL_RE.match(f["url"]),
                            f["url"])

    def test_urls_match_guarded_routes_without_paths(self):
        d = self.frames_dir()
        self.write_show_images(d, 6)
        self.write_ref_rows(d, 4)
        by_h = self._by_h()
        frames = pm.frames_fuer_segment(self.cfg, ["e1"], by_h=by_h, event_dir=d)
        self.assertTrue(frames)
        for f in frames:
            self.assertTrue(FRAME_KEYS <= set(f))
            self.assertEqual(f["id"], "%s|%s|%s" % (f["eid"], f["kind"],
                             f["id"].split("|", 2)[2]))
            self.assertTrue(f["url"].startswith("/"))
            self.assertNotIn("..", f["url"])
            self.assertNotIn("\\", f["url"])
            self.assertFalse(os.path.isabs(f["url"].lstrip("/")) or ":" in f["url"])
            self.assertTrue(EVENT_URL_RE.match(f["url"]) or REF_URL_RE.match(f["url"]), f["url"])


class TestRevision(OfflineCase):
    def _snap(self):
        d = self.frames_dir()
        self.write_show_images(d, 8)
        self.write_ref_rows(d, 4)
        by_h = {"e1": row("e1", BASE, bestaetigt=["Person A"], kategorie="person"),
                "e2": row("e2", BASE + 5)}
        snap = self.passe(by_h, event_dir=d)[0]
        self.assertTrue(snap["segments"][0]["frames"])
        return snap

    def _rev(self, snap):
        return pm.revision(snap["pass_key"], 0, snap)

    def test_stable_and_valid_hex(self):
        snap = self._snap()
        rev = self._rev(snap)
        self.assertTrue(REV_RE.match(rev))
        self.assertEqual(self._rev(snap), rev)

    def test_changes_with_eids(self):
        snap = self._snap()
        base = self._rev(snap)
        other = copy.deepcopy(snap)
        other["segments"][0]["eids"].append("e-extra")
        self.assertNotEqual(self._rev(other), base)

    def test_changes_with_person_label(self):
        snap = self._snap()
        base = self._rev(snap)
        other = copy.deepcopy(snap)
        other["segments"][0]["people"] = [{"name": "Person B"}]
        self.assertNotEqual(self._rev(other), base)

    def test_changes_with_categories(self):
        snap = self._snap()
        base = self._rev(snap)
        other = copy.deepcopy(snap)
        other["segments"][0]["categories"] = ["other"]
        self.assertNotEqual(self._rev(other), base)

    def test_changes_with_frame_set(self):
        snap = self._snap()
        base = self._rev(snap)
        other = copy.deepcopy(snap)
        other["segments"][0]["frames"] = snap["segments"][0]["frames"][:1]
        self.assertNotEqual(self._rev(other), base)


class TestPayload(OfflineCase):
    def _snap(self):
        d = self.frames_dir()
        self.write_show_images(d, 6)
        by_h = {"e1": row("e1", BASE, bestaetigt=["Person A"], kategorie="person")}
        snap = self.passe(by_h, event_dir=d)[0]
        return snap, pm.revision(snap["pass_key"], 0, snap)

    def test_empty_segment_has_no_contact_url(self):
        snap, rev = self._snap()
        empty = copy.deepcopy(snap)
        empty["segments"][0]["frames"] = []
        empty["segments"][0]["counts"]["frames"] = 0
        d = pm.payload(empty, 0, "active", rev)
        self.assertEqual(set(d), PAYLOAD_KEYS)
        self.assertTrue(COUNT_KEYS <= set(d["counts"]))
        self.assertEqual(d["counts"]["frames"], 0)
        self.assertEqual(d["frames"], [])
        self.assertEqual(d["contact_url"], "")
        full = pm.payload(snap, 0, "active", rev)
        self.assertEqual(full["contact_url"],
                         "/pass/%s/%s/0/contact.jpg" % (snap["pass_key"], rev))

    def test_exact_key_set_and_statuses(self):
        snap, rev = self._snap()
        for status in ("active", "revision", "final"):
            d = pm.payload(snap, 0, status, rev)
            self.assertEqual(set(d), PAYLOAD_KEYS)
            self.assertEqual(d["schema"], "pass-v1")
            self.assertEqual(d["herkunft"], "pass")
            self.assertEqual(d["status"], status)
            self.assertEqual(d["revision"], rev)
            self.assertEqual(d["segment"], 0)
            self.assertNotIn("zones", d)
            self.assertNotIn("topic", d)

    def test_contact_url_and_frame_shape(self):
        snap, rev = self._snap()
        d = pm.payload(snap, 0, "active", rev)
        self.assertEqual(d["contact_url"],
                         "/pass/%s/%s/0/contact.jpg" % (snap["pass_key"], rev))
        self.assertTrue(d["frames"])
        for f in d["frames"]:
            self.assertEqual(set(f), FRAME_KEYS)
            self.assertTrue(f["url"].startswith("/"))
            self.assertNotIn("..", f["url"])


class FakeTimer:
    def __init__(self, delay, fn, args=()):
        self.delay, self.fn, self.args = delay, fn, args
        self.started = self.cancelled = False

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True

    def fire(self):
        self.fn(*self.args)


class FakeFactory:
    def __init__(self):
        self.timers = []

    def __call__(self, delay, fn, args=()):
        t = FakeTimer(delay, fn, args)
        self.timers.append(t)
        return t


class TestPassTimer(OfflineCase):
    def _timer(self, factory=None):
        fired = []
        factory = factory or FakeFactory()
        timer = pm.PassTimer(self.cfg, lambda pk, t: fired.append(pk),
                             timer_factory=factory)
        return timer, factory, fired

    def test_final_timer_fires_once_through_pass_timer_callback(self):
        fired = []
        factory = FakeFactory()

        def fire(pass_key, mein_timer):
            fired.append(pass_key)
            pt.feuer(pass_key, mein_timer)   # mirrors the old guard in _pass_faellig

        pt = pm.PassTimer(self.cfg, fire, timer_factory=factory)
        self.assertTrue(pt.antossen("pk-final"))
        current = factory.timers[-1]
        current.fn(*current.args)            # timer callback -> exactly one fire
        self.assertEqual(fired, ["pk-final"])
        current.fn(*current.args)            # re-entry is stale -> no second fire
        self.assertEqual(fired, ["pk-final"])

        pt.antossen("pk-final")              # reset: old token stale, new token current
        stale, fresh = factory.timers[-2], factory.timers[-1]
        stale.fn(*stale.args)
        self.assertEqual(fired, ["pk-final"])
        fresh.fn(*fresh.args)
        self.assertEqual(fired, ["pk-final", "pk-final"])

        self.assertNotIn("_pass_timer.feuer", verifyd_func_src("_pass_faellig"))
        self.assertIn("_pass_timer.antossen", verifyd_func_src("_pass_anstossen"))

    def test_armed_once_with_configured_grace(self):
        timer, factory, fired = self._timer()
        self.assertTrue(timer.antossen("pk1"))
        self.assertEqual(len(factory.timers), 1)
        self.assertEqual(factory.timers[0].delay, 7)
        self.assertTrue(factory.timers[0].started)
        self.assertTrue(timer.feuer("pk1", factory.timers[0]))
        self.assertEqual(fired, ["pk1"])
        self.assertFalse(timer.feuer("pk1", factory.timers[0]))

    def test_reset_cancels_prior_and_stale_token_cannot_fire(self):
        timer, factory, fired = self._timer()
        timer.antossen("pk1")
        timer.antossen("pk1")
        self.assertEqual(len(factory.timers), 2)
        self.assertTrue(factory.timers[0].cancelled)
        self.assertFalse(timer.feuer("pk1", factory.timers[0]))
        self.assertEqual(fired, [])
        self.assertTrue(timer.feuer("pk1", factory.timers[1]))
        self.assertEqual(fired, ["pk1"])

    def test_cancel_all_and_single(self):
        timer, factory, fired = self._timer()
        timer.antossen("pk1")
        timer.antossen("pk2")
        timer.cancel("pk1")
        self.assertTrue(factory.timers[0].cancelled)
        self.assertFalse(factory.timers[1].cancelled)
        timer.cancel()
        self.assertTrue(all(t.cancelled for t in factory.timers))
        self.assertFalse(timer.feuer("pk2", factory.timers[1]))
        self.assertEqual(fired, [])

    def test_no_startup_arming_and_in_memory_only(self):
        timer, factory, fired = self._timer()
        self.assertEqual(factory.timers, [])
        self.assertEqual(timer._laufend, {})
        self.assertEqual(os.listdir(self.tmp), [])  # nothing persisted to disk


class TestContactSheet(OfflineCase):
    def _sheet(self, frames, *, pk=None, rev=None, seg=0, image=JPEG):
        pk = pk or "p" + uuid.uuid4().hex[:10]
        rev = rev or uuid.uuid4().hex[:12]
        with mock.patch.object(pm, "bild_bytes", side_effect=lambda cfg, f: image):
            return pb.contact_sheet(self.cfg, pk, rev, seg, frames=frames)

    def _size(self, data):
        self.assertTrue(data)
        self.assertEqual(data[:2], b"\xff\xd8")
        with Image.open(io.BytesIO(data)) as img:
            return img.size

    def test_grid_rows_and_12_tile_cap(self):
        for n, rows in ((1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (12, 6), (13, 6)):
            with self.subTest(n=n):
                size = self._size(self._sheet([frame(i) for i in range(1, n + 1)]))
                self.assertEqual(size, (1024, rows * 384))

    def test_tile_dimensions(self):
        w, h = self._size(self._sheet([frame(1)]))
        self.assertEqual(w // 2, 512)
        self.assertEqual(h - 24, 360)

    def test_order_and_labels_affect_bytes(self):
        f1, f2 = frame(1, camera="cam-a", kind="event"), frame(2, camera="cam-b", kind="ref")
        key = dict(pk="pOrder", rev="000000000001")
        a = self._sheet([f1, f2], **key)
        b = self._sheet([f2, f1], **dict(pk="pOrder", rev="000000000002"))
        self.assertNotEqual(a, b)
        c = self._sheet([f1, f2 | {"camera": "cam-c"}],
                        pk="pOrder", rev="000000000003")
        d = self._sheet([f1, f2 | {"ts": BASE + 99}],
                        pk="pOrder", rev="000000000004")
        e = self._sheet([f1, f2 | {"kind": "person"}],
                        pk="pOrder", rev="000000000005")
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, d)
        self.assertNotEqual(a, e)

    def test_missing_frames_placeholder_is_deterministic(self):
        frames = [frame(1) | {"url": "/events/e1/does-not-exist.jpg"}]
        a = self._sheet(frames, image=None)
        b = self._sheet(frames, image=None)
        self.assertIsNotNone(a)
        self.assertEqual(a, b)
        self.assertEqual(self._size(a), (1024, 384))

    def test_invalid_keys_and_traversal_return_none(self):
        seg = [frame(1)]
        rev = "00000000000a"
        for pk in ("../etc/passwd", "a/b", "/absolute", "..", "", "bad key", 123):
            self.assertIsNone(pb.contact_sheet(self.cfg, pk, rev, 0, frames=seg))
        for bad_rev in ("xyz", "../00000000000a", "00000000000A", None, 12):
            self.assertIsNone(pb.contact_sheet(self.cfg, "pk1", bad_rev, 0, frames=seg))
        for bad_seg in (-1, 64, "abc", None, 10 ** 30):
            self.assertIsNone(pb.contact_sheet(self.cfg, "pk1", rev, bad_seg, frames=seg))

    def test_implicit_frames_path_resolves_revision(self):
        d = os.path.join(self.tmp, "events", "e1")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "clip_show_Person_A_00.jpg"), "wb") as f:
            f.write(JPEG)
        by_h = {"e1": row("e1", BASE + 31)}
        snap = pm.paesse(self.cfg, by_h)[0]
        rev = pm.revision(snap["pass_key"], 0, snap)
        data = pb.contact_sheet(self.cfg, snap["pass_key"], rev, 0, by_h=by_h)
        self.assertEqual(self._size(data), (1024, 384))

    def test_repeated_call_is_byte_identical_and_uses_cache(self):
        frames = [frame(1), frame(2)]
        key = dict(pk="pCache", rev="00000000000c", seg=0)
        with mock.patch.object(pm, "bild_bytes", side_effect=lambda cfg, f: JPEG) as lader:
            first = pb.contact_sheet(self.cfg, key["pk"], key["rev"], key["seg"], frames=frames)
            calls = lader.call_count
            second = pb.contact_sheet(self.cfg, key["pk"], key["rev"], key["seg"], frames=frames)
        self.assertEqual(first, second)
        self.assertEqual(lader.call_count, calls)
        self.assertEqual(calls, len(frames))
        self.assertEqual(pb.cache_lesen(("pCache", "00000000000c", 0)), first)
        self.assertEqual(pb.etag("00000000000c"), '"00000000000c"')


class TestSourceWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(VERIFYD, encoding="utf-8") as f:
            cls.src = f.read()
        cls.tree = ast.parse(cls.src)

    def _func(self, name):
        return next(n for n in ast.walk(self.tree)
                    if isinstance(n, ast.FunctionDef) and n.name == name)

    def _src(self, node):
        return ast.get_source_segment(self.src, node) or ""

    def test_route_constant_and_do_get_branch(self):
        node = next(n for n in self.tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "PASS_CONTACT_RE"
                            for t in n.targets))
        text = self._src(node)
        self.assertIn("re.compile", text)
        pattern = ast.literal_eval(node.value.args[0])
        rx = re.compile(pattern)
        good = "/pass/1234567890/0123456789ab/0/contact.jpg"
        self.assertTrue(rx.match(good))
        self.assertIsNone(rx.match("/pass/../etc/0123456789ab/0/contact.jpg"))
        self.assertIsNone(rx.match("/pass/1234567890/0123456789ab/x/contact.jpg"))
        branch = self._src(self._func("do_GET"))
        self.assertIn("PASS_CONTACT_RE", branch)
        self.assertIn("contact_sheet", branch)

    def test_legacy_pass_branch_excludes_contact_route(self):
        branch = self._src(self._func("do_GET"))
        legacy = re.search(
            r'if\s+path\.startswith\("/pass/"\)\s+and\s+not\s+PASS_CONTACT_RE\.match\(path\)',
            branch)
        self.assertIsNotNone(legacy)
        node = next(n for n in self.tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "PASS_CONTACT_RE"
                            for t in n.targets))
        rx = re.compile(ast.literal_eval(node.value.args[0]))
        self.assertTrue(rx.match("/pass/1764231000/0123456789ab/0/contact.jpg"))
        self.assertIsNone(rx.match("/pass/1764231000"))
        contact = branch.index("_pm_treffer = PASS_CONTACT_RE.match(path)", legacy.end())
        self.assertLess(legacy.start(), contact)

    def test_topic_and_anstossen_hook(self):
        self.assertIn('_melden.topic(self.cfg, "pass")', self.src)
        self.assertIn("def _pass_anstossen(", self.src)
        self.assertIn("self._pass_anstossen(", self.src)

    def test_vision_off_and_no_refquelle_in_new_code(self):
        self.assertNotIn("_vision_anstossen", self._src(self._func("_pass_anstossen")))
        base = os.path.dirname(VERIFYD)
        def imports_refquelle(source):
            for n in ast.walk(ast.parse(source)):
                if isinstance(n, ast.Import):
                    if any("refquelle" in a.name for a in n.names):
                        return True
                elif isinstance(n, ast.ImportFrom) and n.module and "refquelle" in n.module:
                    return True
            return False
        for name in ("core/pass_mqtt.py", "core/passbild.py"):
            with self.subTest(file=name):
                with open(os.path.join(base, name), encoding="utf-8") as f:
                    self.assertFalse(imports_refquelle(f.read()))
        for name in ("_pass_anstossen", "_pass_publizieren", "_pass_faellig"):
            with self.subTest(func=name):
                self.assertFalse(imports_refquelle(self._src(self._func(name))))


if __name__ == "__main__":
    unittest.main()
