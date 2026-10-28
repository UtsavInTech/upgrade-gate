"""VoiceOrder: shop checks, sample parsing and the HTTP API (against the local mock, no API calls)."""
from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.request
import wave
from unittest import mock

from tests.mock_server import mock_server
from upgrade_gate.client import ModelClient
from voiceorder import server as vo


def _wav(seconds: float = 0.5) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\0\0" * int(16000 * seconds))
    return buf.getvalue()


class ShopChecks(unittest.TestCase):
    def test_wrong_but_well_formed_pincode_passes_the_shop(self):
        c = vo.checks({"order_number": "93437", "pincode": "380015", "city": "Ahmedabad"}, "")
        self.assertEqual(c["status"], "saved")  # the gap: format checks can't see it's the wrong pincode

    def test_blank_and_cant_hear(self):
        self.assertEqual(vo.checks({"order_number": "", "pincode": "", "city": ""}, "")["status"], "rejected")
        self.assertEqual(vo.checks(None, "I can't hear the audio attachment.")["status"], "ask_customer")
        self.assertEqual(vo.checks({"order_number": "93437", "pincode": "38001", "city": "X"}, "")["status"],
                         "rejected")


class Api(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_recorded_note_uses_the_gated_prompt_and_shipping_model(self):
        answer = '{"order_number": "58213", "pincode": "411001", "city": "Pune"}'
        with mock_server(answer=answer) as api:
            client = ModelClient(base_url=api.base_url, api_key="k", cache_dir=os.path.join(self.tmp, "c"), rpm={"*": 0})
            srv = vo.serve(0, client)
            port = srv.server_address[1]
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                base = "http://127.0.0.1:%d" % port
                cfg = json.load(urllib.request.urlopen(base + "/api/voiceorder/config"))
                self.assertEqual(cfg["shipping"], vo.shipping_model())
                self.assertGreater(len(cfg["samples"]), 10)
                req = urllib.request.Request(base + "/api/voiceorder/parse?model=" + cfg["shipping"], data=_wav(),
                                             method="POST", headers={"Content-Type": "audio/wav"})
                out = json.load(urllib.request.urlopen(req))
                self.assertEqual(out["order"]["pincode"], "411001")
                self.assertEqual(out["checks"]["status"], "saved")
                sent = api.requests[-1]
                self.assertEqual(sent["messages"][0]["content"][0]["text"], vo.PROMPT)
                self.assertEqual(sent["messages"][0]["content"][1]["type"], "input_audio")
                bad = urllib.request.Request(base + "/api/voiceorder/parse?model=spark-1.1@low", data=_wav(),
                                             method="POST")
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(bad)
                self.assertEqual(e.exception.code, 400)  # only the shipping and candidate models
            finally:
                srv.shutdown()


if __name__ == "__main__":
    unittest.main()


class StaticExport(unittest.TestCase):
    """scripts/export_voiceorder.py must never call the API: a cache miss is skipped, not sent."""

    def test_cache_only_client_refuses_to_send(self):
        import importlib.util
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location("export_voiceorder", os.path.join(root, "scripts", "export_voiceorder.py"))
        export_voiceorder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(export_voiceorder)
        with tempfile.TemporaryDirectory() as d:
            c = export_voiceorder.CacheOnly(api_key="x", cache_dir=d)
            with self.assertRaises(LookupError):
                c.chat("muse-spark-1.3", [{"role": "user", "content": "hi"}])
