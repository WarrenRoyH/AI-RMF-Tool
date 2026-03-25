import os

class Vault:
    """
    Zero-Trust Vault interface for managing HOST and TARGET credentials.
    Enforces namespace isolation to prevent credential bleed.
    """
    
    VALID_NAMESPACES = ["HOST", "TARGET"]

    @staticmethod
    def get(key_name: str, namespace: str) -> str:
        """
        Retrieves a secret from the environment based on the specified namespace.
        The key name will be prefixed with '{namespace}_'.
        """
        if namespace not in Vault.VALID_NAMESPACES:
            raise ValueError(f"Invalid namespace: {namespace}. Must be HOST or TARGET.")
            
        prefixed_key = f"{namespace}_{key_name}"
        
        # Security Boundary: Never fallback across namespaces
        value = os.getenv(prefixed_key)
        
        # Isolation Check: If looking for TARGET and it's missing, ensure we don't return HOST
        # (Though os.getenv(f"TARGET_{key_name}") will only return that specific env var anyway)
        
        # AC3: Key Bleed detection logic would be in cli/verify.py, but we can have a basic check here if needed.
        # For now, stay simple.
        
        return value

    @staticmethod
    def get_host_key(key_name: str) -> str:
        return Vault.get(key_name, "HOST")

    @staticmethod
    def get_target_key(key_name: str) -> str:
        return Vault.get(key_name, "TARGET")
