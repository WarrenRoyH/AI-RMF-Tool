import unittest
import os
from core.vault import Vault

class TestVault(unittest.TestCase):
    def setUp(self):
        # Setup environment variables for testing
        os.environ["HOST_TEST_KEY"] = "host_secret"
        os.environ["TARGET_TEST_KEY"] = "target_secret"
        os.environ["UNPREFIXED_KEY"] = "unprefixed_secret"

    def tearDown(self):
        # Clean up
        if "HOST_TEST_KEY" in os.environ: del os.environ["HOST_TEST_KEY"]
        if "TARGET_TEST_KEY" in os.environ: del os.environ["TARGET_TEST_KEY"]
        if "UNPREFIXED_KEY" in os.environ: del os.environ["UNPREFIXED_KEY"]

    def test_host_namespace_isolation(self):
        """AC1: Verify HOST_ prefix is enforced."""
        val = Vault.get("TEST_KEY", "HOST")
        self.assertEqual(val, "host_secret")
        
        # Ensure it doesn't accidentally pick up unprefixed or target
        val_unprefixed = Vault.get("UNPREFIXED_KEY", "HOST")
        self.assertIsNone(val_unprefixed)

    def test_target_namespace_isolation(self):
        """AC1: Verify TARGET_ prefix is enforced."""
        val = Vault.get("TEST_KEY", "TARGET")
        self.assertEqual(val, "target_secret")

    def test_invalid_namespace(self):
        """Verify that invalid namespaces raise ValueError."""
        with self.assertRaises(ValueError):
            Vault.get("TEST_KEY", "INVALID")

    def test_get_host_key_helper(self):
        self.assertEqual(Vault.get_host_key("TEST_KEY"), "host_secret")

    def test_get_target_key_helper(self):
        self.assertEqual(Vault.get_target_key("TEST_KEY"), "target_secret")

    def test_isolation_integrity(self):
        """Ensure that calling TARGET doesn't return HOST even if TARGET is missing."""
        if "TARGET_MISSING_KEY" in os.environ: del os.environ["TARGET_MISSING_KEY"]
        os.environ["HOST_MISSING_KEY"] = "should_not_see_this"
        
        val = Vault.get("MISSING_KEY", "TARGET")
        self.assertIsNone(val)
        if "HOST_MISSING_KEY" in os.environ: del os.environ["HOST_MISSING_KEY"]

if __name__ == "__main__":
    unittest.main()
