import os
import pytest
from unittest.mock import patch, MagicMock
from cli.verify import check_key_bleed

def test_check_key_bleed_success():
    # Mock environment to be clean of sensitive keys
    with patch.dict(os.environ, {
        "HOST_OPENAI_API_KEY": "host",
        "TARGET_OPENAI_API_KEY": "target"
    }, clear=True):
        assert check_key_bleed() is True

def test_check_key_bleed_failure():
    # Mock environment with a bleed
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "bleed"
    }, clear=True):
        assert check_key_bleed() is False

def test_check_key_bleed_identical_warning():
    # Identical keys should not cause failure but should print a warning
    with patch.dict(os.environ, {
        "HOST_OPENAI_API_KEY": "same",
        "TARGET_OPENAI_API_KEY": "same"
    }, clear=True):
        assert check_key_bleed() is True
