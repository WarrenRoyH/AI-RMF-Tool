import os
import logging
from core.vault import Vault

class VaultSecurity:
    """
    Phase 18.5: Strategic Security Hardening
    Proxy for core.vault.Vault that implements strict namespace isolation
    and integrity checks as per sprint S005-2026-03-24.
    """
    
    # Session-based state that tracks whether the current operation is 'Auditor' (HOST) or 'Probe' (TARGET)
    _current_context = "HOST" 

    @classmethod
    def set_context(cls, context: str):
        if context not in ["HOST", "TARGET"]:
            raise ValueError(f"Invalid security context: {context}")
        cls._current_context = context
        # logging.debug(f"[VAULT_SECURITY]: Context set to {context}")

    @classmethod
    def get_context(cls):
        return cls._current_context

    @staticmethod
    def get(key_name: str, namespace: str) -> str:
        """
        Enforces strict namespace isolation and integrity checks.
        """
        # T1: Strict prefix validation (already in Vault.get, but we double down)
        if namespace not in ["HOST", "TARGET"]:
            raise ValueError(f"CRITICAL SECURITY VIOLATION: Invalid namespace '{namespace}' requested.")

        # T2: Context enforcement (Auditor vs Probe)
        # If the system is currently in 'Probe' mode (TARGET), it must NOT access HOST keys.
        if VaultSecurity._current_context == "TARGET" and namespace == "HOST":
             raise PermissionError(f"ACCESS DENIED: Probe context is restricted from accessing HOST credentials (Key: {key_name}).")

        # Integrity Check: Credential Bleed Detection
        # Detect if a key has been leaked across namespaces in the environment.
        host_val = os.getenv(f"HOST_{key_name}")
        target_val = os.getenv(f"TARGET_{key_name}")
        
        if namespace == "TARGET" and target_val and host_val and target_val == host_val:
            # This is a critical warning in the AI RMF context
            logging.warning(f"SECURITY ALERT: Credential Bleed detected for '{key_name}'. HOST and TARGET environments share identical secrets.")

        # Call the original immutable Vault
        return Vault.get(key_name, namespace)

    @staticmethod
    def get_host_key(key_name: str) -> str:
        return VaultSecurity.get(key_name, "HOST")

    @staticmethod
    def get_target_key(key_name: str) -> str:
        return VaultSecurity.get(key_name, "TARGET")
