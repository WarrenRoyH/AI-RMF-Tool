import os
import pytest
from unittest.mock import patch, MagicMock
from core.provider import LLMProvider, APIAdapter
from core.vault import Vault

def test_api_adapter_vault_integration(monkeypatch):
    monkeypatch.setenv("HOST_OPENAI_API_KEY", "host-key")
    monkeypatch.setenv("TARGET_OPENAI_API_KEY", "target-key")
    
    # Auditor adapter (HOST)
    host_adapter = APIAdapter("gpt-4", namespace="HOST")
    assert host_adapter.api_key == "host-key"
    
    # Target adapter (TARGET)
    target_adapter = APIAdapter("gpt-4", namespace="TARGET")
    assert target_adapter.api_key == "target-key"

def test_llm_provider_vault_initialization(monkeypatch):
    monkeypatch.setenv("HOST_OPENAI_API_KEY", "host-key")
    monkeypatch.setenv("TARGET_OPENAI_API_KEY", "target-key")
    monkeypatch.setenv("HOST_AI_RMF_AUDITOR_MODEL", "gpt-4")
    monkeypatch.setenv("TARGET_AI_RMF_TARGET_MODEL", "gpt-4")
    
    p = LLMProvider()
    
    assert p.adapter.namespace == "HOST"
    assert p.adapter.api_key == "host-key"
    
    assert p.target_adapter.namespace == "TARGET"
    assert p.target_adapter.api_key == "target-key"

def test_vault_namespace_isolation_at_adapter_level(monkeypatch):
    monkeypatch.setenv("HOST_GOOGLE_API_KEY", "host-google")
    monkeypatch.delenv("TARGET_GOOGLE_API_KEY", raising=False)
    
    host_adapter = APIAdapter("gemini-pro", namespace="HOST")
    target_adapter = APIAdapter("gemini-pro", namespace="TARGET")
    
    assert host_adapter.api_key == "host-google"
    assert target_adapter.api_key is None
