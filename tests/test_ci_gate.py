"""CI entry point: replay and live mode (live against the local mock, so no API calls)."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


class CiGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"RUNNER_TEMP": self.tmp, "UPGRADE_GATE_CACHE_DIR": os.path.join(self.tmp, "c"),
                                                "UPGRADE_GATE_LEDGER": os.path.join(self.tmp, "ledger.jsonl")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _main(self, *argv):
        import ci_gate
        with mock.patch.object(sys, "argv", ["ci_gate.py", *argv]):
            return ci_gate.main()

    def test_replay_blocks_voice_notes_and_passes_text(self):
        self.assertEqual(self._main("voice-notes", "--baseline", "spark-1.2@low", "--candidate", "spark-1.3@low"), 2)
        self.assertEqual(self._main("text-and-documents", "--baseline", "spark-1.2@low",
                                    "--candidate", "spark-1.3@low"), 0)

    def test_live_mode_runs_end_to_end_on_mock(self):
        from tests.mock_server import mock_server
        with mock_server(answer="ok") as srv, mock.patch.dict(os.environ, {"MODEL_API_KEY": "test",
                                                                          "MODEL_API_BASE": srv.base_url}):
            code = self._main("custom", "--baseline", "spark-1.2@low", "--candidate", "spark-1.3@low", "--live",
                              "--packs", os.path.join(ROOT, "examples", "my_tasks.jsonl"), "--n", "5",
                              "--budget", "0.5")
            calls = srv.calls
        self.assertEqual(calls, 5 * 2 * 3)  # 5 tasks x 2 models x 3 tries, all sent to the mock
        self.assertIn(code, (0, 2))  # identical answers: GO, or inconclusive treated as neutral (0)
        with open(os.path.join(self.tmp, "upgrade-gate-live", "live-custom", "gate.json")) as f:
            self.assertIn(json.load(f)["decision"], ("go", "inconclusive"))


if __name__ == "__main__":
    unittest.main()
