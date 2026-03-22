#!/usr/bin/env python3
"""Tests for validate.py — structural validation helpers."""

import os
import sys

import pytest

# Import from tests directory
sys.path.insert(0, os.path.dirname(__file__))

from validate import (
    find_entry_block,
    find_commented_entry,
    get_field,
    has_bibtidy_comment,
    has_source_url,
)


SAMPLE_ENTRY = (
    "@article{Smith2020,\n"
    "  title={A {Nested} Title},\n"
    "  author={Smith, John},\n"
    "  year={2020}\n"
    "}"
)

SAMPLE_CHANGED = (
    "% @article{Smith2020,\n"
    "%   title={Old Title},\n"
    "% }\n"
    "% bibtidy: source https://doi.org/10.1234/test\n"
    "% bibtidy: fixed title\n"
    "@article{Smith2020,\n"
    "  title={New Title},\n"
    "  year={2020}\n"
    "}"
)


class TestFindEntryBlock:
    def test_finds_entry(self):
        result = find_entry_block(SAMPLE_ENTRY, "Smith2020")
        assert result is not None
        assert "Smith2020" in result
        assert "title={A {Nested} Title}" in result

    def test_handles_nested_braces(self):
        text = "@article{X,\n  title={A {B {C}} D},\n  year={2020}\n}"
        result = find_entry_block(text, "X")
        assert result is not None
        assert "A {B {C}} D" in result

    def test_returns_none_for_missing_key(self):
        assert find_entry_block(SAMPLE_ENTRY, "Missing") is None

    def test_ignores_commented_entry(self):
        text = "% @article{Ghost,\n%   title={Hidden}\n% }\n"
        assert find_entry_block(text, "Ghost") is None

    def test_key_with_special_chars(self):
        text = "@article{doi:10.1234/foo,\n  title={Test}\n}"
        result = find_entry_block(text, "doi:10.1234/foo")
        assert result is not None


class TestFindCommentedEntry:
    def test_found(self):
        assert find_commented_entry(SAMPLE_CHANGED, "Smith2020") is True

    def test_not_found(self):
        assert find_commented_entry(SAMPLE_ENTRY, "Smith2020") is False

    def test_key_with_special_chars(self):
        text = "% @article{doi:10.1234/foo,\n%   title={Old}\n% }\n"
        assert find_commented_entry(text, "doi:10.1234/foo") is True


class TestGetField:
    def test_simple_field(self):
        assert get_field(SAMPLE_ENTRY, "year") == "2020"

    def test_nested_braces(self):
        assert get_field(SAMPLE_ENTRY, "title") == "A {Nested} Title"

    def test_missing_field(self):
        assert get_field(SAMPLE_ENTRY, "doi") is None

    def test_case_insensitive(self):
        text = "@article{X,\n  Title={Hello}\n}"
        assert get_field(text, "title") == "Hello"


class TestHasBibtidyComment:
    def test_found(self):
        assert has_bibtidy_comment(SAMPLE_CHANGED, "Smith2020", r"% bibtidy: fixed") is True

    def test_not_found(self):
        assert has_bibtidy_comment(SAMPLE_ENTRY, "Smith2020", r"% bibtidy:") is False

    def test_source_url(self):
        assert has_source_url(SAMPLE_CHANGED, "Smith2020") is True

    def test_no_source_url(self):
        assert has_source_url(SAMPLE_ENTRY, "Smith2020") is False

    def test_duplicate_flag(self):
        text = (
            "% bibtidy: DUPLICATE of Other — consider removing\n"
            "@article{Dup,\n"
            "  title={Test}\n"
            "}"
        )
        assert has_bibtidy_comment(text, "Dup", r"DUPLICATE") is True
