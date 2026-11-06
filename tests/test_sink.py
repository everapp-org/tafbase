"""T-sink-* — the filed ledger: the same error must not file twice."""
import os

from taf import sink_ikc3


def test_fingerprint_is_stable_across_runs_and_tmpdirs():
    a = sink_ikc3.fingerprint("test_a", "Error at /tmp/taf-run-aaa/x.py 0x1f2a")
    b = sink_ikc3.fingerprint("test_a", "Error at /tmp/taf-run-bbb/x.py 0x9c4d")
    c = sink_ikc3.fingerprint("test_a", "A different error")
    assert a == b and a != c


def test_ledger_remembers_what_filed(tmp_path, monkeypatch):
    monkeypatch.setenv("TAF_RESULTS", str(tmp_path))
    fp = sink_ikc3.fingerprint("test_a", "boom")
    assert sink_ikc3.filed(fp) is None
    sink_ikc3.record(fp, "report-123")
    assert sink_ikc3.filed(fp) == "report-123"
    assert os.path.exists(tmp_path / "filed.json")
