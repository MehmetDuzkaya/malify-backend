import pytest
from app.services.scraper.parser import GazetteParser


def test_extract_text_removes_script_tags():
    html = "<html><body><script>alert(1)</script><p>Test metin</p></body></html>"
    result = GazetteParser.extract_text(html)
    assert "alert" not in result
    assert "Test metin" in result


def test_extract_text_empty_html():
    result = GazetteParser.extract_text("<html></html>")
    assert result == ""
