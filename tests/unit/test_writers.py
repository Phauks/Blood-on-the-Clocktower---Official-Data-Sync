"""Unit tests for src/scrapers/writers.py."""

import json
import pytest
from pathlib import Path

from src.scrapers.writers import (
    order_character_fields,
    strip_internal_fields,
    save_characters_by_edition,
    create_manifest,
    FIELD_ORDER,
)


class TestOrderCharacterFields:
    """Tests for order_character_fields function."""

    @pytest.mark.unit
    def test_orders_fields_correctly(self):
        """Should order fields according to FIELD_ORDER."""
        char = {
            "ability": "Test ability",
            "id": "test",
            "name": "Test",
            "team": "townsfolk",
            "edition": "tb",
        }

        result = order_character_fields(char)
        keys = list(result.keys())

        # id, name, edition, team should come before ability
        assert keys.index("id") < keys.index("ability")
        assert keys.index("name") < keys.index("ability")
        assert keys.index("edition") < keys.index("ability")
        assert keys.index("team") < keys.index("ability")

    @pytest.mark.unit
    def test_preserves_unknown_fields(self):
        """Should preserve fields not in FIELD_ORDER at the end."""
        char = {
            "id": "test",
            "custom_field": "value",
        }

        result = order_character_fields(char)
        assert "custom_field" in result
        assert result["custom_field"] == "value"


class TestStripInternalFields:
    """Tests for strip_internal_fields function."""

    @pytest.mark.unit
    def test_strips_internal_fields(self):
        """Should remove fields starting with underscore."""
        char = {
            "id": "test",
            "name": "Test",
            "_imageUrl": "http://example.com/img.png",
            "_internal": "data",
        }

        result = strip_internal_fields(char)
        assert "id" in result
        assert "name" in result
        assert "_imageUrl" not in result
        assert "_internal" not in result

    @pytest.mark.unit
    def test_preserves_reminder_flag_when_requested(self):
        """Should preserve _remindersFetched when preserve_reminder_flag=True."""
        char = {
            "id": "test",
            "_remindersFetched": True,
            "_imageUrl": "http://example.com/img.png",
        }

        result = strip_internal_fields(char, preserve_reminder_flag=True)
        assert "_remindersFetched" in result
        assert result["_remindersFetched"] is True
        assert "_imageUrl" not in result

    @pytest.mark.unit
    def test_strips_all_internal_when_not_preserving(self):
        """Should strip all internal fields when preserve_reminder_flag=False."""
        char = {
            "id": "test",
            "_remindersFetched": True,
            "_imageUrl": "http://example.com/img.png",
        }

        result = strip_internal_fields(char, preserve_reminder_flag=False)
        assert "_remindersFetched" not in result
        assert "_imageUrl" not in result


class TestSaveCharactersByEdition:
    """Tests for save_characters_by_edition function."""

    @pytest.mark.unit
    def test_creates_edition_directories(self, temp_dir, sample_character):
        """Should create edition directories."""
        characters = {sample_character["id"]: sample_character}
        save_characters_by_edition(characters, temp_dir)

        edition_dir = temp_dir / sample_character["edition"]
        assert edition_dir.exists()

    @pytest.mark.unit
    def test_saves_individual_character_files(self, temp_dir, sample_character):
        """Should save individual character JSON files."""
        characters = {sample_character["id"]: sample_character}
        save_characters_by_edition(characters, temp_dir)

        char_file = temp_dir / sample_character["edition"] / f"{sample_character['id']}.json"
        assert char_file.exists()

        with open(char_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["id"] == sample_character["id"]

    @pytest.mark.unit
    def test_creates_all_characters_file(self, temp_dir, sample_character):
        """Should create all_characters.json file."""
        characters = {sample_character["id"]: sample_character}
        save_characters_by_edition(characters, temp_dir)

        all_file = temp_dir / "all_characters.json"
        assert all_file.exists()

        with open(all_file, "r", encoding="utf-8") as f:
            all_chars = json.load(f)
        assert len(all_chars) == 1
        assert all_chars[0]["id"] == sample_character["id"]

    @pytest.mark.unit
    def test_strips_internal_fields_from_all_characters(self, temp_dir, sample_character):
        """Should strip internal fields from all_characters.json."""
        char_with_internal = {**sample_character, "_imageUrl": "http://example.com/img.png"}
        characters = {char_with_internal["id"]: char_with_internal}
        save_characters_by_edition(characters, temp_dir)

        all_file = temp_dir / "all_characters.json"
        with open(all_file, "r", encoding="utf-8") as f:
            all_chars = json.load(f)

        assert "_imageUrl" not in all_chars[0]


class TestCreateManifest:
    """Tests for create_manifest function."""

    @pytest.mark.unit
    def test_creates_manifest_file(self, temp_dir, sample_character):
        """Should create manifest.json file."""
        characters = {sample_character["id"]: sample_character}
        create_manifest(characters, temp_dir)

        manifest_file = temp_dir / "manifest.json"
        assert manifest_file.exists()

    @pytest.mark.unit
    def test_manifest_has_required_fields(self, temp_dir, sample_character):
        """Should include all required manifest fields."""
        characters = {sample_character["id"]: sample_character}
        manifest = create_manifest(characters, temp_dir)

        assert "schemaVersion" in manifest
        assert "version" in manifest
        assert "generated" in manifest
        assert "contentHash" in manifest
        assert "total_characters" in manifest
        assert "editions" in manifest
        assert "edition_counts" in manifest

    @pytest.mark.unit
    def test_counts_characters_correctly(self, temp_dir):
        """Should count characters correctly."""
        characters = {
            "char1": {"id": "char1", "edition": "tb", "reminders": ["A", "B"]},
            "char2": {"id": "char2", "edition": "tb", "reminders": []},
            "char3": {"id": "char3", "edition": "bmr", "reminders": ["C"]},
        }
        manifest = create_manifest(characters, temp_dir)

        assert manifest["total_characters"] == 3
        assert manifest["edition_counts"]["tb"] == 2
        assert manifest["edition_counts"]["bmr"] == 1
        assert manifest["total_reminders"] == 3

    @pytest.mark.unit
    def test_counts_jinxes_correctly(self, temp_dir):
        """Should count jinxes correctly (accounting for bidirectional storage)."""
        characters = {
            "char1": {"id": "char1", "edition": "tb", "jinxes": [{"id": "char2", "reason": "test"}]},
            "char2": {"id": "char2", "edition": "tb", "jinxes": [{"id": "char1", "reason": "test"}]},
        }
        manifest = create_manifest(characters, temp_dir)

        # Jinxes are stored bidirectionally, so divide by 2
        assert manifest["total_jinxes"] == 1
