import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.utils import Obfuscator

def test_unicode_homoglyph_smuggling():
    text = "apple"
    obfuscator = Obfuscator()
    # intensity=1.0 ensures all possible characters are replaced
    smuggled = obfuscator.unicode_homoglyph_smuggling(text, intensity=1.0)
    
    assert smuggled != text
    assert len(smuggled) == len(text)
    # Check that 'a' was replaced by something in HOMOGLYPH_MAP
    assert smuggled[0] == Obfuscator.HOMOGLYPH_MAP['a']

def test_nested_hex_encode():
    text = "abc"
    obfuscator = Obfuscator()
    encoded = obfuscator.nested_hex_encode(text, levels=2)
    
    # "abc" -> "616263" (level 1)
    # "616263" -> "363136323633" (level 2)
    assert encoded == "363136323633"

def test_nested_base64_encode():
    text = "abc"
    obfuscator = Obfuscator()
    encoded = obfuscator.nested_base64_encode(text, levels=1)
    
    import base64
    assert encoded == base64.b64encode(b"abc").decode()

def test_obfuscate_all_branches():
    text = "test"
    obfuscator = Obfuscator()
    
    with patch('random.choice', return_value="hex"), \
         patch('random.random', return_value=1.0): # No homoglyphs
        res = obfuscator.obfuscate_all(text)
        assert res == obfuscator.nested_hex_encode(text)

    with patch('random.choice', return_value="base64"), \
         patch('random.random', return_value=1.0):
        res = obfuscator.obfuscate_all(text)
        assert res == obfuscator.nested_base64_encode(text)

    with patch('random.choice', return_value="both"), \
         patch('random.random', return_value=1.0):
        res = obfuscator.obfuscate_all(text)
        # both applies hex then base64
        intermediate = obfuscator.nested_hex_encode(text)
        expected = obfuscator.nested_base64_encode(intermediate)
        assert res == expected

def test_homoglyph_map_integrity():
    # Verify that all values in HOMOGLYPH_MAP are different from keys
    for k, v in Obfuscator.HOMOGLYPH_MAP.items():
        assert k != v
