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


def begin(run_dir, test_id):
    """Open results/<runId>/<testId>/journal.jsonl."""
    global _current, _start
    d = os.path.join(run_dir, test_id)
    os.makedirs(d, exist_ok=True)
    _start = time.monotonic()
    _current = open(os.path.join(d, "journal.jsonl"), "w",
                    encoding="utf-8")


def note(label):
    """Narrate a step: print it for the watcher, record it for the file."""
    event("note", label=label)
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


def end(outcome=None):
    """Record the outcome and close."""
    global _current, _outcome
    event("end", outcome=outcome or _outcome)
    if _current is not None:
        _current.close()
        _current = None
    _outcome = "passed"


_current = None
_outcome = "passed"
