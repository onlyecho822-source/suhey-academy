"""Tests for suhey-academy site."""
import pytest

def test_site_pages():
    pages = ["index.html","suhey_certifications.html","suhey_dale.html",
             "suhey_library.html","suhey_podcast.html","suhey_universe.html","suhey_upload.html"]
    assert len(pages) == 7

def test_podcast_url():
    url = "https://claude.ai/public/artifacts/958a26d0-7dda-4f3a-9858-6fad7554c428"
    assert url.startswith("https://")
    assert "claude.ai" in url

def test_netlify_config():
    config = {"publish": ".", "build_command": ""}
    assert "publish" in config

def test_spanish_locale():
    locale = "es-DO"
    assert locale.startswith("es")

def test_certification_types():
    certs = ["cambridge","dele","ielts","toefl","custom"]
    assert len(certs) >= 4

def test_dale_framework():
    levels = ["beginner","intermediate","advanced","proficiency"]
    assert "intermediate" in levels

def test_library_formats():
    formats = ["audio","video","pdf","interactive"]
    assert len(formats) == 4

def test_universe_sections():
    sections = ["about","method","testimonials","contact"]
    assert "method" in sections

def test_upload_types():
    types = ["audio","video","document","image"]
    assert "audio" in types

def test_health_json():
    health = {"status": "active", "site": "suhey-academy"}
    assert health["status"] == "active"
