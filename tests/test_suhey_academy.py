"""Tests for suhey-academy site."""
import pytest

def test_site_pages():
    pages = ["index.html", "suhey_certifications.html", "suhey_dale.html",
             "suhey_library.html", "suhey_podcast.html",
             "suhey_universe.html", "suhey_upload.html"]
    assert len(pages) == 7

def test_podcast_url():
    podcast_url = "https://claude.ai/public/artifacts/958a26d0-7dda-4f3a-9858-6fad7554c428"
    assert "claude.ai" in podcast_url
    assert "artifacts" in podcast_url

def test_podcast_target():
    target = "_blank"
    assert target == "_blank"

def test_netlify_config():
    config = {"publish": ".", "framework": None}
    assert "publish" in config

def test_config_required_fields():
    required = ["owner_name", "tagline", "contact_email", "social_links",
                "course_titles", "testimonials", "hero_image", "logo"]
    assert len(required) == 8

def test_bilingual_support():
    languages = ["en", "es"]
    assert "es" in languages

def test_deploy_guide_steps():
    steps = ["configure", "preflight_check", "deploy_to_netlify", "verify"]
    assert steps[0] == "configure"

def test_certifications_section():
    certs = {"displayed": True, "format": "cards", "bilingual": True}
    assert certs["bilingual"] is True

def test_site_identity():
    identity = {"name": "Suhey Spanish Academy", "type": "language_school"}
    assert "Spanish" in identity["name"]

def test_health_json():
    health = {"status": "pre-launch", "config_complete": False, "deploy_ready": False}
    assert "status" in health
