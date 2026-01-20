"""Unit tests for src/utils/data_loader.py."""

import json
import pytest
from pathlib import Path

from src.utils.data_loader import (
    load_previous_character_data,
    load_character_file,
    save_character_file,
    get_character_files_by_edition,
)


class TestLoadPreviousCharacterData:
    """Tests for load_previous_character_data function."""

    @pytest.mark.unit
    def test_returns_empty_dict_when_dir_not_exists(self, temp_dir):
        """Should return empty dict when characters directory doesn't exist."""
        non_existent = temp_dir / "non_existent"
        result = load_previous_character_data(non_existent)
        assert result == {}

    @pytest.mark.unit
    def test_loads_character_files(self, temp_dir, sample_character):
        """Should load character files from subdirectories."""
        # Create edition directory and character file
        edition_dir = temp_dir / "tb"
        edition_dir.mkdir(parents=True)
        char_file = edition_dir / "washerwoman.json"
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(sample_character, f)

        result = load_previous_character_data(temp_dir)
        assert "washerwoman" in result
        assert result["washerwoman"]["name"] == "Washerwoman"

    @pytest.mark.unit
    def test_skips_all_characters_json(self, temp_dir, sample_character):
        """Should skip all_characters.json file."""
        all_chars_file = temp_dir / "all_characters.json"
        with open(all_chars_file, "w", encoding="utf-8") as f:
            json.dump([sample_character], f)

        result = load_previous_character_data(temp_dir)
        assert result == {}

    @pytest.mark.unit
    def test_handles_malformed_json(self, temp_dir):
        """Should skip files with invalid JSON."""
        edition_dir = temp_dir / "tb"
        edition_dir.mkdir(parents=True)
        bad_file = edition_dir / "bad.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("not valid json {")

        # Should not raise, just skip the file
        result = load_previous_character_data(temp_dir)
        assert result == {}


class TestLoadCharacterFile:
    """Tests for load_character_file function."""

    @pytest.mark.unit
    def test_loads_valid_file(self, temp_dir, sample_character):
        """Should load a valid character JSON file."""
        char_file = temp_dir / "test.json"
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(sample_character, f)

        result = load_character_file(char_file)
        assert result is not None
        assert result["id"] == "washerwoman"

    @pytest.mark.unit
    def test_returns_none_for_missing_file(self, temp_dir):
        """Should return None for non-existent file."""
        result = load_character_file(temp_dir / "missing.json")
        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_invalid_json(self, temp_dir):
        """Should return None for invalid JSON."""
        bad_file = temp_dir / "bad.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        result = load_character_file(bad_file)
        assert result is None


class TestSaveCharacterFile:
    """Tests for save_character_file function."""

    @pytest.mark.unit
    def test_saves_character(self, temp_dir, sample_character):
        """Should save character to JSON file."""
        char_file = temp_dir / "test.json"
        result = save_character_file(char_file, sample_character)

        assert result is True
        assert char_file.exists()

        # Verify content
        with open(char_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["id"] == "washerwoman"

    @pytest.mark.unit
    def test_creates_parent_directories(self, temp_dir, sample_character):
        """Should create parent directories if they don't exist."""
        nested_file = temp_dir / "deep" / "nested" / "test.json"
        result = save_character_file(nested_file, sample_character)

        assert result is True
        assert nested_file.exists()

    @pytest.mark.unit
    def test_adds_trailing_newline(self, temp_dir, sample_character):
        """Should add trailing newline to file."""
        char_file = temp_dir / "test.json"
        save_character_file(char_file, sample_character)

        with open(char_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert content.endswith("\n")


class TestGetCharacterFilesByEdition:
    """Tests for get_character_files_by_edition function."""

    @pytest.mark.unit
    def test_returns_empty_for_missing_edition(self, temp_dir):
        """Should return empty list for non-existent edition."""
        result = get_character_files_by_edition("nonexistent", temp_dir)
        assert result == []

    @pytest.mark.unit
    def test_returns_sorted_files(self, temp_dir):
        """Should return files sorted by name."""
        edition_dir = temp_dir / "tb"
        edition_dir.mkdir(parents=True)

        # Create files in non-alphabetical order
        (edition_dir / "z_char.json").write_text("{}")
        (edition_dir / "a_char.json").write_text("{}")
        (edition_dir / "m_char.json").write_text("{}")

        result = get_character_files_by_edition("tb", temp_dir)

        assert len(result) == 3
        assert result[0].name == "a_char.json"
        assert result[1].name == "m_char.json"
        assert result[2].name == "z_char.json"
