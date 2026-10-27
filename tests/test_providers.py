"""Meta Model API vs OpenRouter: config selection and request translation. Stdlib only."""
from __future__ import annotations

import os
import tempfile
import unittest

from upgrade_gate import config, pricing
from upgrade_gate.client import ModelClient, wire_request

OR = "https://openrouter.ai/api/v1"
META = "https://api.meta.ai/v1"


class Translate(unittest.TestCase):
    def test_meta_untouched(self):
        b = wire_request(META, "muse-spark-1.3", {"max_completion_tokens": 100, "reasoning_effort": "low"})
        self.assertEqual(b, {"model": "muse-spark-1.3", "max_completion_tokens": 100, "reasoning_effort": "low"})

    def test_openrouter_spark(self):
        b = wire_request(OR, "muse-spark-1.3", {"max_completion_tokens": 100, "reasoning_effort": "low"})
        self.assertEqual(b["model"], "meta/muse-spark-1.3")
        self.assertEqual(b["max_tokens"], 100)
        self.assertNotIn("max_completion_tokens", b)
        self.assertEqual(b["provider"], {"order": ["meta"], "allow_fallbacks": False})
        self.assertEqual(b["usage"], {"include": True})
        self.assertEqual(b["reasoning_effort"], "low")

    def test_openrouter_contributor_allows_training(self):
        b = wire_request(OR, "muse-spark-1.2-contributor", {})
        self.assertEqual(b["model"], "meta/muse-spark-1.2-contributor")
        self.assertEqual(b["provider"]["data_collection"], "allow")

    def test_openrouter_wonder_and_open_weights(self):
        self.assertEqual(wire_request(OR, "muse-wonder-1.0", {})["model"], "meta/muse-wonder")
        g = wire_request(OR, "muse-glimmer-30b", {})
        self.assertEqual(g["model"], "meta/muse-glimmer-30b")
        self.assertNotIn("provider", g)  # several hosts serve it; don't pin

    def test_prices_resolve_prefixed_ids(self):
        self.assertTrue(pricing.is_known("meta/muse-spark-1.3"))
        self.assertTrue(pricing.is_known("muse-glimmer-30b"))
        self.assertTrue(pricing.is_known("meta/muse-wonder"))


class ProviderConfig(unittest.TestCase):
    KEYS = ("MODEL_PROVIDER", "MODEL_API_KEY", "MODEL_API_BASE", "OPENROUTER_API_KEY")

    def setUp(self):
        self.saved = {k: os.environ.pop(k, None) for k in self.KEYS}
        self.tmp = tempfile.TemporaryDirectory()
        self.saved_root = config.REPO_ROOT
        config.REPO_ROOT = self.tmp.name  # empty .env
        config.reload()

    def tearDown(self):
        for k, v in self.saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
        config.REPO_ROOT = self.saved_root
        config.reload()
        self.tmp.cleanup()

    def test_default_is_meta(self):
        self.assertEqual(config.provider(), "meta")
        self.assertEqual(config.model_api_base(), META)

    def test_openrouter_key_alone_selects_openrouter(self):
        os.environ["OPENROUTER_API_KEY"] = "sk-or-test"
        self.assertEqual(config.provider(), "openrouter")
        self.assertEqual(config.model_api_base(), OR)
        self.assertEqual(config.model_api_key(), "sk-or-test")
        self.assertEqual(ModelClient().base_url, OR)

    def test_explicit_provider_wins(self):
        os.environ["OPENROUTER_API_KEY"] = "sk-or-test"
        os.environ["MODEL_API_KEY"] = "LLM_test"
        self.assertEqual(config.provider(), "meta")
        os.environ["MODEL_PROVIDER"] = "openrouter"
        self.assertEqual(config.provider(), "openrouter")
        self.assertEqual(config.model_api_key(), "sk-or-test")

    def test_describe_never_shows_keys(self):
        os.environ["OPENROUTER_API_KEY"] = "sk-or-secret"
        self.assertNotIn("sk-or-secret", repr(config.describe()))


if __name__ == "__main__":
    unittest.main()
