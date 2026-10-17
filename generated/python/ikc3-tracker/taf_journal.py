"""taf_journal — the timestamped event stream, one per test.

@concept CONCEPT-taf-v1-004-01-the-artifacts

Every run writes results/<runId>/<testId>/journal.jsonl — one JSON
event per line: {"t": ms, "event": "note|fail|end", ...}. Labels,
soft-check failures, test failures all land here; downstream consumers
(the .srt writer, the rerun manifest, fault reports) read it instead
of re-instrumenting. begin() opens the stream for the test; note()
prints AND records — narration and journal share one line of emission.
"""

import json
import os
import time

_current = None
_start = 0.0
_dir = None
_notes = []


def begin(run_dir, test_id):
    """Open results/<runId>/<testId>/journal.jsonl."""
    global _current, _start, _dir, _notes
    d = os.path.join(run_dir, test_id)
    os.makedirs(d, exist_ok=True)
    _start = time.monotonic()
    _dir = d
    _notes = []
    _current = open(os.path.join(d, "journal.jsonl"), "w",
                    encoding="utf-8")


def test_dir():
    """results/<runId>/<testId>/ of the open journal — where artifacts go."""
    return _dir


def note(label):
    """Narrate a step: print it for the watcher, record it for the file."""
    event("note", label=label)
    _notes.append((int((time.monotonic() - _start) * 1000), label))
    print(label)


def event(kind, **fields):
    """Append one event line; a no-op when no journal is open."""
    if _current is None:
        return
    rec = {"t": int((time.monotonic() - _start) * 1000), "event": kind}
    rec.update(fields)
    _current.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _current.flush()


def mark(outcome):
    """Record the run's verdict; end() writes it into the last line."""
    global _outcome
    _outcome = outcome


def _srt_ts(ms):
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms % 3600000 // 60000,
                                  ms % 60000 // 1000, ms % 1000)


def _write_srt(path, notes):
    """Narrated steps as an .srt track — captions keyed to test time."""
    with open(path, "w", encoding="utf-8") as f:
        for i, (t, label) in enumerate(notes):
            end_t = notes[i + 1][0] if i + 1 < len(notes) else t + 2000
            f.write("%d\n%s --> %s\n%s\n\n" %
                    (i + 1, _srt_ts(t), _srt_ts(end_t), label))


def end(outcome=None):
    """Record the outcome, write the .srt sidecar, close."""
    global _current, _outcome, _dir
    event("end", outcome=outcome or _outcome)
    if _current is not None:
        _current.close()
        _current = None
    if _dir and _notes:
        _write_srt(os.path.join(_dir, "journal.srt"), _notes)
    _outcome = "passed"


_current = None
_outcome = "passed"
