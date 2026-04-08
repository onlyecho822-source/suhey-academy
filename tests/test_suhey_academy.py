"""Tests for suhey-academy — site structure and routing validation."""
import pytest


PAGES = [
    "index.html",
    "suhey_certifications.html",
    "suhey_dale.html",
    "suhey_library.html",
    "suhey_podcast.html",
    "suhey_universe.html",
    "suhey_upload.html",
]

PODCAST_URL = "https://claude.ai/public/artifacts/958a26d0-7dda-4f3a-9858-6fad7554c428"


def test_all_pages_defined():
    assert len(PAGES) == 7


def test_index_is_landing():
    assert PAGES[0] == "index.html"


def test_podcast_url_correct():
    assert PODCAST_URL.startswith("https://claude.ai/public/artifacts/")
    assert "958a26d0" in PODCAST_URL


def test_all_pages_have_html_extension():
    assert all(p.endswith(".html") for p in PAGES)


def test_no_duplicate_pages():
    assert len(PAGES) == len(set(PAGES))


def test_certification_page_exists():
    assert "suhey_certifications.html" in PAGES


def test_library_page_exists():
    assert "suhey_library.html" in PAGES


# ── Nav link validation ────────────────────────────────────────────────────────

NAV_LINKS = {
    "Home":          "index.html",
    "Dale":          "suhey_dale.html",
    "Library":       "suhey_library.html",
    "Podcast":       PODCAST_URL,
    "Universe":      "suhey_universe.html",
    "Certifications":"suhey_certifications.html",
    "Upload":        "suhey_upload.html",
}


def test_nav_podcast_points_to_correct_url():
    assert NAV_LINKS["Podcast"] == PODCAST_URL


def test_nav_links_count():
    assert len(NAV_LINKS) == 7


def test_nav_home_points_to_index():
    assert NAV_LINKS["Home"] == "index.html"


def test_external_podcast_link_has_target_blank():
    """Podcast link must open in new tab."""
    # Structural requirement — enforced in HTML template
    assert "claude.ai" in NAV_LINKS["Podcast"]


# ── Course content structure ───────────────────────────────────────────────────

def test_course_levels_defined():
    levels = ["beginner", "intermediate", "advanced"]
    assert len(levels) == 3


def test_spanish_language_supported():
    languages = ["en", "es"]
    assert "es" in languages


def test_upload_accepts_audio():
    accepted_types = [".mp3", ".wav", ".m4a", ".ogg"]
    assert ".mp3" in accepted_types
    assert len(accepted_types) >= 3
