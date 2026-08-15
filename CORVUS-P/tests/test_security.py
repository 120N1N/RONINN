import pytest
from backend.utils.security import SecurityValidator

def test_validate_target_valid_domain():
    assert SecurityValidator.validate_target("google.com") == "http://google.com"
    assert SecurityValidator.validate_target("https://example.com") == "https://example.com"

def test_validate_target_invalid_ssrf():
    with pytest.raises(ValueError, match="SSRF Blocked"):
        SecurityValidator.validate_target("127.0.0.1")
    
    with pytest.raises(ValueError, match="SSRF Blocked"):
        SecurityValidator.validate_target("localhost")

def test_validate_target_admin_bypass():
    res = SecurityValidator.validate_target("localhost", is_admin=True)
    assert res == "http://localhost"

