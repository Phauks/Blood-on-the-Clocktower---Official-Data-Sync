"""Pytest configuration and shared fixtures."""

import json
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup after test
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_character():
    """Sample character data for testing."""
    return {
        "id": "washerwoman",
        "name": "Washerwoman",
        "team": "townsfolk",
        "edition": "tb",
        "ability": "You start knowing that 1 of 2 players is a particular Townsfolk.",
        "firstNight": 23,
        "firstNightReminder": "Show the character token of a Townsfolk in play. Point to two players, one of which is that character.",
        "otherNight": 0,
        "otherNightReminder": "",
        "reminders": ["Townsfolk", "Wrong"],
        "setup": False,
        "image": "https://script.bloodontheclocktower.com/src/assets/icons/tb/washerwoman_g.webp"
    }


@pytest.fixture
def sample_characters_list():
    """Sample list of character data for testing."""
    return [
        {
            "id": "washerwoman",
            "name": "Washerwoman",
            "team": "townsfolk",
            "edition": "tb",
            "ability": "You start knowing that 1 of 2 players is a particular Townsfolk.",
            "firstNight": 23,
            "otherNight": 0,
            "setup": False
        },
        {
            "id": "imp",
            "name": "Imp",
            "team": "demon",
            "edition": "tb",
            "ability": "Each night*, choose a player: they die. If you kill yourself this way, a Minion becomes the Imp.",
            "firstNight": 0,
            "otherNight": 28,
            "setup": False
        }
    ]


@pytest.fixture
def sample_character_file(temp_dir, sample_character):
    """Create a temporary character JSON file."""
    char_file = temp_dir / f"{sample_character['id']}.json"
    with open(char_file, "w", encoding="utf-8") as f:
        json.dump(sample_character, f, indent=2)
    return char_file


@pytest.fixture
def mock_wiki_html():
    """Sample wiki HTML for testing parsing."""
    return """
    <html>
    <body>
        <div id="mw-content-text">
            <p class="flavour">"Clean people are happy people."</p>
            <h2>How to Run</h2>
            <p>During the first night, show the TOWNSFOLK character token.</p>
            <p>Place the WRONG reminder on a player who is not that character.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_icon_url():
    """Sample icon URL for testing."""
    return "https://script.bloodontheclocktower.com/src/assets/icons/tb/washerwoman_g.webp"
