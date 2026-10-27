"""Verbatim-copied runtime sources — journal + sink."""

import os


def _sink_source():
    """The emitted ikc3_sink.py is taf/sink_ikc3.py verbatim — one source
    for the emitter's own code and the artifact it ships."""
    with open(os.path.join(os.path.dirname(__file__), "..", "..", "sink_ikc3.py"),
              encoding="utf-8") as f:
        return f.read()


def _journal_source():
    """The emitted taf_journal.py is taf/journal_runtime.py verbatim."""
    with open(os.path.join(os.path.dirname(__file__), "..", "..", "journal_runtime.py"),
              encoding="utf-8") as f:
        return f.read()


