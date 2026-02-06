import unittest
from unittest import mock

import app


class AppStateTests(unittest.TestCase):
    def test_grpc_falls_back_to_sim_when_disabled(self):
        with mock.patch.object(app, "_DISABLE_GRPC", True), mock.patch.object(
            app, "_ENABLE_LLMD", True
        ):
            self.assertEqual(app._normalize_backend("GRPC"), "SIM")

    def test_llmd_requires_local_flag(self):
        with mock.patch.object(app, "_DISABLE_GRPC", False), mock.patch.object(
            app, "_ENABLE_LLMD", False
        ):
            self.assertEqual(app._normalize_backend("LLMD"), "SIM")

    def test_sglang_alias_requires_llmd_local_flag(self):
        with mock.patch.object(app, "_DISABLE_GRPC", False), mock.patch.object(
            app, "_ENABLE_LLMD", False
        ):
            self.assertEqual(app._normalize_backend("SGLANG"), "SIM")

    def test_sglang_alias_maps_to_llmd(self):
        with mock.patch.object(app, "_DISABLE_GRPC", False), mock.patch.object(
            app, "_ENABLE_LLMD", True
        ):
            self.assertEqual(app._normalize_backend("SGLANG"), "LLMD")
            self.assertEqual(app._normalize_backend("sglang (local)"), "LLMD")

    def test_mode_label_for_llmd(self):
        self.assertEqual(app._mode_label("LLMD"), "llm-d (local)")

    def test_resolve_selected_worker_from_numeric_id(self):
        result = {"worker_id": 3, "reason": {}}
        self.assertEqual(app._resolve_selected_worker(result, "GRPC", 5), "D")

    def test_resolve_selected_worker_from_identity_hash(self):
        result = {"worker_id": "llm-d", "reason": {"worker_identity": "pod-abc-1"}}
        selected = app._resolve_selected_worker(result, "LLMD", 5)
        self.assertIn(selected, {"A", "B", "C", "D", "E"})

    def test_resolve_selected_worker_none_when_identity_unknown(self):
        result = {"worker_id": "sglang", "reason": {}}
        self.assertIsNone(app._resolve_selected_worker(result, "LLMD", 5))


if __name__ == "__main__":
    unittest.main()
