import unittest
import os
import logging
from core.vault_security import VaultSecurity

class TestVaultSecurity(unittest.TestCase):
    def setUp(self):
        # Setup environment variables for testing
        os.environ["HOST_API_KEY"] = "host_secret"
        os.environ["TARGET_API_KEY"] = "target_secret"
        os.environ["HOST_BLEED_KEY"] = "leaked_secret"
        os.environ["TARGET_BLEED_KEY"] = "leaked_secret"
        VaultSecurity.set_context("HOST") # Reset to HOST

    def tearDown(self):
        # Clean up
        keys = ["HOST_API_KEY", "TARGET_API_KEY", "HOST_BLEED_KEY", "TARGET_BLEED_KEY"]
        for k in keys:
            if k in os.environ: del os.environ[k]

    def test_context_enforcement(self):
        """T2: Verify context enforcement (Auditor vs Probe)."""
        # When in HOST context, should be able to get HOST keys
        self.assertEqual(VaultSecurity.get("API_KEY", "HOST"), "host_secret")
        
        # When in TARGET context, should NOT be able to get HOST keys
        VaultSecurity.set_context("TARGET")
        with self.assertRaises(PermissionError):
            VaultSecurity.get("API_KEY", "HOST")
            
        # When in TARGET context, should still be able to get TARGET keys
        self.assertEqual(VaultSecurity.get("API_KEY", "TARGET"), "target_secret")

    def test_bleed_detection(self):
        """T1: Verify credential bleed detection (integrity checks)."""
        # Ensure it logs a warning but still returns the value
        with self.assertLogs(level='WARNING') as cm:
            val = VaultSecurity.get("BLEED_KEY", "TARGET")
            self.assertEqual(val, "leaked_secret")
            self.assertTrue(any("Credential Bleed detected" in output for output in cm.output))

    def test_invalid_namespace(self):
        """T1: Verify strict prefix validation."""
        with self.assertRaises(ValueError):
            VaultSecurity.get("API_KEY", "INVALID")

    def test_context_switch_reset(self):
        """Verify context switching works as expected."""
        VaultSecurity.set_context("TARGET")
        self.assertEqual(VaultSecurity.get_context(), "TARGET")
        VaultSecurity.set_context("HOST")
        self.assertEqual(VaultSecurity.get_context(), "HOST")

if __name__ == "__main__":
    unittest.main()
