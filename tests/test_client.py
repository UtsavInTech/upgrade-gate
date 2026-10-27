"""Client, pricing, config tests. Run: pytest tests/test_client.py  or  python -m unittest tests.test_client"""
from __future__ import annotations

import base64
import os
import tempfile
import unittest

from tests.mock_server import mock_server
from upgrade_gate import config, pricing
from upgrade_gate.client import ModelClient, build_messages, cache_key, map_usage
from upgrade_gate.schema import Task

NO_RPM = {"*": 0}


def _client(srv, tmp, **kw):
    kw.setdefault("rpm", NO_RPM)
    kw.setdefault("backoff_base", 0.01)
    return ModelClient(base_url=srv.base_url, api_key="test-key", cache_dir=os.path.join(tmp, "cache"), **kw)


class TestPricing(unittest.TestCase):
    def test_standard_cost(self):
        u = {"input_tokens": 1_000_000, "output_tokens": 1_000_000, "reasoning_tokens": 0, "cached_tokens": 0}
        self.assertAlmostEqual(pricing.cost("muse-spark-1.3", u), 1.25 + 4.25)

    def test_cached_and_reasoning(self):
        # 1M input of which 400k cached; 200k output of which 150k reasoning (already inside output)
        u = {"input_tokens": 1_000_000, "cached_tokens": 400_000, "output_tokens": 200_000, "reasoning_tokens": 150_000}
        exp = (600_000 * 1.25 + 400_000 * 0.15 + 200_000 * 4.25) / 1e6
        self.assertAlmostEqual(pricing.cost("muse-spark-1.2", u), exp)

    def test_reasoning_reported_separately_still_billed(self):
        u = {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 1_000_000}
        self.assertAlmostEqual(pricing.cost("muse-wonder-1.0", u), 20.0)

    def test_contributor(self):
        u = {"input_tokens": 1_000_000, "output_tokens": 1_000_000, "cached_tokens": 0}
        self.assertAlmostEqual(pricing.cost("muse-spark-1.3-contributor", u), 0.30)

    def test_unknown(self):
        d = pricing.cost_detail("gpt-x", {"input_tokens": 10, "output_tokens": 10})
        self.assertEqual(d["cost_usd"], 0.0)
        self.assertFalse(d["known"])
        self.assertTrue(d["warning"])


class TestConfig(unittest.TestCase):
    def test_parse_dotenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, ".env")
            with open(p, "w") as f:
                f.write("# c\nexport A=1\nB = \"two words\"\nC=x # trailing\n\nbad line\n")
            d = config.parse_dotenv(p)
            self.assertEqual(d, {"A": "1", "B": "two words", "C": "x"})

    def test_describe_redacts(self):
        os.environ["MODEL_API_KEY"] = "sk-secret-value"
        try:
            self.assertEqual(config.describe()["MODEL_API_KEY"], "set")
            self.assertNotIn("sk-secret-value", repr(ModelClient(base_url="http://127.0.0.1:1")))
        finally:
            del os.environ["MODEL_API_KEY"]


class TestUsageAndKey(unittest.TestCase):
    def test_map_usage(self):
        u = map_usage({"prompt_tokens": 7, "completion_tokens": 5,
                       "completion_tokens_details": {"reasoning_tokens": 3},
                       "prompt_tokens_details": {"cached_tokens": 2}})
        self.assertEqual(u, {"input_tokens": 7, "output_tokens": 5, "reasoning_tokens": 3, "cached_tokens": 2})
        self.assertEqual(map_usage(None)["input_tokens"], 0)

    def test_cache_key_param_order(self):
        m = [{"role": "user", "content": "x"}]
        self.assertEqual(cache_key("m", m, {"a": 1, "b": 2}), cache_key("m", m, {"b": 2, "a": 1}))
        self.assertNotEqual(cache_key("m", m, {}, "rep0"), cache_key("m", m, {}, "rep1"))


class TestChat(unittest.TestCase):
    def test_basic_call_and_params(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server(answer="hello") as srv:
            c = _client(srv, tmp)
            r = c.chat("muse-spark-1.3", [{"role": "user", "content": "hi"}],
                       params={"reasoning_effort": "low", "max_completion_tokens": 64})
            self.assertIsNone(r.error)
            self.assertEqual(r.text, "hello")
            self.assertFalse(r.cached)
            self.assertEqual(r.returned_model, "muse-spark-1.3")
            self.assertEqual(r.usage, {"input_tokens": 100, "output_tokens": 50,
                                       "reasoning_tokens": 20, "cached_tokens": 10})
            self.assertAlmostEqual(r.cost_usd, (90 * 1.25 + 10 * 0.15 + 50 * 4.25) / 1e6)
            req = srv.requests[0]
            self.assertEqual(req["reasoning_effort"], "low")
            self.assertEqual(req["max_completion_tokens"], 64)
            self.assertEqual(srv.headers[0]["Authorization"], "Bearer test-key")

    def test_retries_on_429(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server(answer="ok", fail_first=3) as srv:
            r = _client(srv, tmp).chat("muse-spark-1.2", [{"role": "user", "content": "x"}])
            self.assertIsNone(r.error)
            self.assertEqual(r.text, "ok")
            self.assertEqual(srv.calls, 4)

    def test_retries_on_503(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server(fail_first=1, fail_status=503) as srv:
            r = _client(srv, tmp).chat("muse-spark-1.2", [{"role": "user", "content": "x"}])
            self.assertIsNone(r.error)
            self.assertEqual(srv.calls, 2)

    def test_gives_up_after_max_attempts(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server(fail_first=100) as srv:
            r = _client(srv, tmp).chat("muse-spark-1.2", [{"role": "user", "content": "x"}])
            self.assertIsNone(r.text)
            self.assertIn("429", r.error)
            self.assertEqual(srv.calls, 5)

    def test_no_retry_on_400(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock_server(status_for_model={"muse-spark-1.3": 400}) as srv:
            c = _client(srv, tmp)
            r = c.chat("muse-spark-1.3", [{"role": "user", "content": "x"}], params={"reasoning_effort": "none"})
            self.assertEqual(srv.calls, 1)
            self.assertIn("HTTP 400", r.error)
            self.assertIn("forced 400", r.error)
            # errors are not cached
            r2 = c.chat("muse-spark-1.3", [{"role": "user", "content": "x"}], params={"reasoning_effort": "none"})
            self.assertEqual(srv.calls, 2)
            self.assertFalse(r2.cached)

    def test_connection_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = ModelClient(base_url="http://127.0.0.1:9/v1", api_key="k", cache_dir=tmp, rpm=NO_RPM,
                            backoff_base=0.001, max_attempts=2, timeout=2)
            r = c.chat("muse-spark-1.2", [{"role": "user", "content": "x"}])
            self.assertIsNone(r.text)
            self.assertIn("gave up after 2", r.error)

    def test_cache_hit(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server(answer="cached?") as srv:
            c = _client(srv, tmp)
            m = [{"role": "user", "content": "x"}]
            r1 = c.chat("muse-spark-1.2", m)
            r2 = c.chat("muse-spark-1.2", m)
            self.assertEqual(srv.calls, 1)
            self.assertTrue(r2.cached)
            self.assertEqual(r2.text, "cached?")
            self.assertAlmostEqual(r2.cost_usd, r1.cost_usd)
            self.assertEqual(r2.usage, r1.usage)
            # new client instance on same dir also hits
            self.assertTrue(_client(srv, tmp).chat("muse-spark-1.2", m).cached)
            # cache files in ab/abcdef.json layout
            files = []
            for root, _, fs in os.walk(os.path.join(tmp, "cache")):
                files += [os.path.join(root, f) for f in fs]
            self.assertEqual(len(files), 1)
            self.assertEqual(os.path.basename(os.path.dirname(files[0])), os.path.basename(files[0])[:2])

    def test_salt_and_use_cache_false(self):
        with tempfile.TemporaryDirectory() as tmp, mock_server() as srv:
            c = _client(srv, tmp)
            m = [{"role": "user", "content": "x"}]
            c.chat("muse-spark-1.2", m, cache_salt="rep0")
            self.assertFalse(c.chat("muse-spark-1.2", m, cache_salt="rep1").cached)
            self.assertFalse(c.chat("muse-spark-1.2", m, cache_salt="rep0", use_cache=False).cached)
            self.assertEqual(srv.calls, 3)

    def test_rate_limiter_spacing(self):
        import time
        with tempfile.TemporaryDirectory() as tmp, mock_server() as srv:
            c = _client(srv, tmp, rpm={"muse-spark-1.2-contributor": 600})  # 0.1 s apart
            t0 = time.monotonic()
            for i in range(4):
                c.chat("muse-spark-1.2-contributor", [{"role": "user", "content": str(i)}])
            self.assertGreaterEqual(time.monotonic() - t0, 0.28)

    def test_default_rpm(self):
        c = ModelClient(base_url="http://127.0.0.1:1")
        self.assertEqual(c._rpm_for("muse-spark-1.3-contributor"), 140)
        self.assertEqual(c._rpm_for("muse-spark-1.3"), 2500)


class TestBuildMessages(unittest.TestCase):
    def _task(self, attachments, prompt="Q?"):
        return Task(id="t1", pack="p", category="c", lang="en", modality="image", prompt=prompt,
                    reference="a", scorer={"type": "exact"}, attachments=attachments)

    def test_text(self):
        self.assertEqual(build_messages(self._task([])), [{"role": "user", "content": "Q?"}])
        msgs = build_messages({"prompt": "hi"}, system="be brief")
        self.assertEqual(msgs[0], {"role": "system", "content": "be brief"})
        self.assertEqual(msgs[1], {"role": "user", "content": "hi"})

    def test_image_and_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            png, jpg, webp, pdf = [os.path.join(tmp, n) for n in ("a.png", "b.JPG", "c.webp", "d.pdf")]
            for p in (png, jpg, webp, pdf):
                with open(p, "wb") as f:
                    f.write(b"\x00bytes-" + p.encode())
            msgs = build_messages(self._task([png, jpg, webp, pdf]))
            parts = msgs[0]["content"]
            self.assertEqual(parts[0], {"type": "text", "text": "Q?"})
            self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/png;base64,"))
            self.assertTrue(parts[2]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
            self.assertTrue(parts[3]["image_url"]["url"].startswith("data:image/webp;base64,"))
            self.assertEqual(parts[4]["type"], "file")
            self.assertEqual(parts[4]["file"]["filename"], "d.pdf")
            fd = parts[4]["file"]["file_data"]
            self.assertTrue(fd.startswith("data:application/pdf;base64,"))
            self.assertEqual(base64.b64decode(fd.split(",", 1)[1]), b"\x00bytes-" + pdf.encode())

    def test_unsupported(self):
        with self.assertRaises(ValueError):
            build_messages(self._task(["x.docx"]))


if __name__ == "__main__":
    unittest.main()
