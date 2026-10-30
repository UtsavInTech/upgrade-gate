"""serve.py, the production server: routes, no paid calls for saved samples, writes go to DATA_DIR."""
import importlib
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "web", "dist")


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    if not os.path.exists(os.path.join(DIST, "index.html")):
        pytest.skip("web/dist not built (npm --prefix web run build)")
    data = tmp_path_factory.mktemp("data")
    os.environ["DATA_DIR"] = str(data)
    os.environ["LIVE_INFERENCE"] = "0"
    sys.path.insert(0, ROOT)
    serve = importlib.import_module("serve")
    importlib.reload(serve)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), serve.App)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % httpd.server_address[1], data
    httpd.shutdown()


def req(url, data=None, method=None):
    r = urllib.request.Request(url, data=data, method=method or ("POST" if data is not None else "GET"))
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, resp.headers.get("Content-Type"), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type"), e.read()


def test_health_and_static(base):
    b, _ = base
    code, _, body = req(b + "/healthz")
    assert code == 200 and json.loads(body)["live"] is False
    code, ctype, _ = req(b + "/")
    assert code == 200 and ctype.startswith("text/html")
    assert req(b + "/..%2f..%2fserve.py")[0] == 404


def test_saved_sample_is_free_and_deterministic(base):
    b, _ = base
    cfg = json.loads(req(b + "/api/voiceorder/config")[2])
    assert cfg["live"] is False and cfg["samples"]
    sid = cfg["samples"][0]["id"]
    code, _, body = req(b + "/api/voiceorder/parse?model=%s&sample=%s" % (urllib.request.quote(cfg["candidate"]), sid), b"")
    assert code == 200 and json.loads(body)["checks"]["status"]
    code, ctype, body = req(b + "/api/voiceorder/parse?model=x&sample=missing", b"")
    assert code == 404 and ctype.startswith("application/json")


def test_live_is_off(base):
    b, _ = base
    code, _, body = req(b + "/api/voiceorder/parse?model=spark-1.2%40low", b"RIFF" + b"\0" * 100)
    assert code == 403 and "off" in json.loads(body)["error"]


def test_recording_and_audit_write_to_data_dir(base):
    b, data = base
    wav = b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 64
    assert req(b + "/api/record?speaker=test-a&clip=audio-extract-00-en", wav)[0] == 200
    assert json.loads(req(b + "/api/recorded?speaker=test-a")[2]) == ["audio-extract-00-en"]
    assert (data / "audio-real" / "test-a" / "audio-extract-00-en.wav").exists()
    assert req(b + "/api/record?speaker=BAD%20NAME&clip=x", wav)[0] == 400
    assert req(b + "/api/audit?labeler=t", json.dumps({"id": "a01", "label": "wrong"}).encode())[0] == 200
    assert json.loads(req(b + "/api/audit?labeler=t")[2]) == {"a01": "wrong"}


def test_unknown_api_is_json_404(base):
    b, _ = base
    code, ctype, _ = req(b + "/api/nope")
    assert code == 404 and ctype.startswith("application/json")
