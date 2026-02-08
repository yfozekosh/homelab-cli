"""Tests for bot utility functions"""

import pytest
from server.bot.main import escape_markdown_v2


class TestEscapeMarkdownV2:
    """Test Markdown V2 escaping function"""

    def test_escape_basic_characters(self):
        """Test escaping basic special characters"""
        text = "Hello_World*Test"
        result = escape_markdown_v2(text)
        assert result == "Hello\\_World\\*Test"

    def test_escape_all_special_chars(self):
        """Test escaping all Telegram MarkdownV2 special characters"""
        text = "_*[]()~`>#+-=|{}.!"
        result = escape_markdown_v2(text)
        # All characters should be escaped
        assert result == "\\_\\*\\[\\]\\(\\)\\~\\`\\>\\#\\+\\-\\=\\|\\{\\}\\.\\!"

    def test_escape_commit_message(self):
        """Test escaping a typical commit message"""
        text = "fix: update config [#123]"
        result = escape_markdown_v2(text)
        assert result == "fix: update config \\[\\#123\\]"

    def test_escape_with_parentheses(self):
        """Test escaping text with parentheses"""
        text = "feat(bot): add new feature"
        result = escape_markdown_v2(text)
        assert result == "feat\\(bot\\): add new feature"

    def test_escape_empty_string(self):
        """Test escaping empty string"""
        result = escape_markdown_v2("")
        assert result == ""

    def test_escape_text_without_special_chars(self):
        """Test text without special characters remains unchanged"""
        text = "Simple text with spaces"
        result = escape_markdown_v2(text)
        assert result == "Simple text with spaces"

    def test_escape_multiple_same_chars(self):
        """Test escaping multiple occurrences of same character"""
        text = "***bold***"
        result = escape_markdown_v2(text)
        assert result == "\\*\\*\\*bold\\*\\*\\*"

    def test_escape_mixed_content(self):
        """Test escaping mixed content"""
        text = "Bug fix: Handle edge-case (issue #42) [CRITICAL]"
        result = escape_markdown_v2(text)
        expected = "Bug fix: Handle edge\\-case \\(issue \\#42\\) \\[CRITICAL\\]"
        assert result == expected
