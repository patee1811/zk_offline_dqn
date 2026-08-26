import importlib
import unittest


class ActiveImportSurfaceTests(unittest.TestCase):
    def test_active_future_namespaces_import_normally(self):
        module_names = [
            "zk_offline_dqn.merkle",
            "zk_offline_dqn.zk_specs",
            "zk_offline_dqn.commitments",
            "zk_offline_dqn.relations",
            "zk_offline_dqn.verifiers",
            "zk_offline_dqn.artifacts",
            "zk_offline_dqn.exporters",
            "zk_offline_dqn.backends.sp1",
            "zk_offline_dqn.experiments",
            "zk_offline_dqn.cli",
        ]

        for module_name in module_names:
            with self.subTest(module_name=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))


if __name__ == "__main__":
    unittest.main()
