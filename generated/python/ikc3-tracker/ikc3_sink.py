"""The IKC3 result sink — files a fault report into a running bus.

@concept CONCEPT-taf-v1-010-01-the-result-sink

Speaks the bus's own wire protocol: one EDN `{:t :dispatch …}` envelope
over a WebSocket text frame on /bus-ws, reply `{:t :reply … :result
[{:type :support/report-filed :report-id …}]}`. A report lands as a real
:fault-report frame with its page, so a red generated test can name its
model element inside the tracker itself — the closed quality loop.

Lane TAF/PLAN-taf-v1-001-01/C-3. No token support yet: works against a
probe or deployment where authz is off (no IKC_*_TOKEN configured).
"""
import json
import uuid


def _edn_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _edn(v):
    if isinstance(v, dict):
        return "{" + " ".join(f":{k} {_edn(x)}" for k, x in v.items() if x is not None) + "}"
    if isinstance(v, str) and v.startswith(":"):
        return v  # a value written ":ns/name" is a keyword, not a string
    return _edn_str(str(v))


def file_report(ws_url, what, url="", dom="", island="", timeout=30):
    """Dispatch :support/file-report; return the report-id string.

    Raises RuntimeError on a refused/error reply so callers can decide —
    a sink that cannot file is a warning for the suite, never a failure.
    """
    import websocket

    rid = str(uuid.uuid4())
    cmd = {"type": ":support/file-report", "what": what, "url": url,
           "dom": dom, "island": island}
    envelope = "{:t :dispatch :id %s :command %s}" % (_edn_str(rid), _edn(cmd))
    ws = websocket.create_connection(ws_url, subprotocols=["ikc3-bus"], timeout=timeout)
    try:
        ws.send(envelope)
        while True:
            msg = ws.recv()
            if f':id "{rid}"' not in msg or ":reply" not in msg:
                continue
            if ":support/report-filed" not in msg:
                raise RuntimeError(f"the bus refused the report: {msg[:300]}")
            marker = ':report-id #uuid "'
            i = msg.index(marker) + len(marker)
            return msg[i:msg.index('"', i)]
    finally:
        ws.close()


def report_url(http_base, report_id):
    """Where a person reads the filed report — the report's page."""
    return f"{http_base}/index.html?island=report&report={report_id}"
