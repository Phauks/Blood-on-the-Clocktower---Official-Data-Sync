"""Unit tests for parser utilities."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "scrapers"))

from parsers import (
    parse_edition_from_icon,
    parse_character_id_from_icon,
    construct_local_image_path,
    detect_setup_flag,
)


class TestParseEditionFromIcon:
    """Tests for parse_edition_from_icon function."""

    def test_parse_tb_edition(self):
        """Should extract 'tb' edition from icon path."""
        icon_src = "src/assets/icons/tb/washerwoman_g.webp"
        assert parse_edition_from_icon(icon_src) == "tb"

    def test_parse_bmr_edition(self):
        """Should extract 'bmr' edition from icon path."""
        icon_src = "src/assets/icons/bmr/moonchild_g.webp"
        assert parse_edition_from_icon(icon_src) == "bmr"

    def test_parse_unknown_edition(self):
        """Should return 'unknown' for invalid path."""
        icon_src = "invalid/path/without/edition"
        assert parse_edition_from_icon(icon_src) == "unknown"


class TestParseCharacterIdFromIcon:
    """Tests for parse_character_id_from_icon function."""

    def test_parse_good_character_id(self):
        """Should extract character ID from good character icon."""
        icon_src = "src/assets/icons/tb/washerwoman_g.webp"
        assert parse_character_id_from_icon(icon_src) == "washerwoman"

    def test_parse_evil_character_id(self):
        """Should extract character ID from evil character icon."""
        icon_src = "src/assets/icons/tb/imp_e.webp"
        assert parse_character_id_from_icon(icon_src) == "imp"

    def test_parse_traveler_character_id(self):
        """Should extract character ID from traveler icon (no suffix)."""
        icon_src = "src/assets/icons/tb/beggar.webp"
        assert parse_character_id_from_icon(icon_src) == "beggar"

    def test_parse_invalid_icon(self):
        """Should return None for invalid icon path."""
        icon_src = "invalid/path"
        assert parse_character_id_from_icon(icon_src) is None


class TestConstructLocalImagePath:
    """Tests for construct_local_image_path function."""

    def test_construct_path_good_character(self):
        """Should construct correct path for good character."""
        result = construct_local_image_path(
            "tb", "washerwoman",
            "src/assets/icons/tb/washerwoman_g.webp"
        )
        assert result == "icons/tb/washerwoman.webp"

    def test_construct_path_evil_character(self):
        """Should construct correct path for evil character."""
        result = construct_local_image_path(
            "tb", "imp",
            "src/assets/icons/tb/imp_e.webp"
        )
        assert result == "icons/tb/imp.webp"

    def test_construct_path_png_extension(self):
        """Should preserve PNG extension if present."""
        result = construct_local_image_path(
            "tb", "washerwoman",
            "src/assets/icons/tb/washerwoman.png"
        )
        assert result == "icons/tb/washerwoman.png"


class TestDetectSetupFlag:
    """Tests for detect_setup_flag function."""

    def test_detect_outsider_setup(self):
        """Should detect [+1 Outsider] setup modifier."""
        ability = "Each night, choose a player: they die. [+1 Outsider]"
        assert detect_setup_flag("godfather", ability) is True

    def test_detect_minion_setup(self):
        """Should detect [-1 Minion] setup modifier."""
        ability = "If you nominate & execute a player, they die that night. [-1 Minion]"
        assert detect_setup_flag("baron", ability) is True

    def test_detect_no_setup(self):
        """Should return False for abilities without setup modifiers."""
        ability = "You start knowing that 1 of 2 players is a particular Townsfolk."
        assert detect_setup_flag("washerwoman", ability) is False

    def test_detect_setup_exception_character(self):
        """Should return True for characters in SETUP_EXCEPTIONS."""
        # Drunk is in SETUP_EXCEPTIONS even without bracket notation
        ability = "You do not know you are the Drunk."
        assert detect_setup_flag("drunk", ability) is True

    def test_non_setup_character_without_brackets(self):
        """Should return False for non-setup characters without bracket text."""
        # Lunatic has no bracket text and is not in SETUP_EXCEPTIONS
        ability = "You think you are a Demon, but you are not."
        assert detect_setup_flag("lunatic", ability) is False
