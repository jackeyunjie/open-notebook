"""
Unit tests for Notebook, Source, and Note domain models.

Tests cover:
- Model validation and field constraints
- Business logic methods
- Edge cases and error handling
"""

import pytest
from pydantic import ValidationError

from open_notebook.domain.notebook import Notebook, Source, Note, ChatSession
from open_notebook.exceptions import InvalidInputError


class TestNotebook:
    """Tests for Notebook domain model."""

    def test_notebook_creation_basic(self):
        """Test basic notebook creation with required fields."""
        notebook = Notebook(name="Test Notebook", description="A test notebook")
        assert notebook.name == "Test Notebook"
        assert notebook.description == "A test notebook"
        assert notebook.archived is False

    def test_notebook_name_cannot_be_empty(self):
        """Test that notebook name cannot be empty or whitespace only."""
        with pytest.raises(InvalidInputError, match="Notebook name cannot be empty"):
            Notebook(name="", description="Test")

    def test_notebook_name_whitespace_only(self):
        """Test that whitespace-only name is rejected."""
        with pytest.raises(InvalidInputError, match="Notebook name cannot be empty"):
            Notebook(name="   ", description="Test")

    def test_notebook_name_stripped(self):
        """Test that name with leading/trailing whitespace is handled."""
        # This should work as the validator strips and checks
        notebook = Notebook(name="  Test Name  ", description="Test")
        assert notebook.name == "  Test Name  "

    def test_notebook_archived_default(self):
        """Test that archived defaults to False."""
        notebook = Notebook(name="Test", description="Test")
        assert notebook.archived is False

    def test_notebook_archived_explicit(self):
        """Test explicit archived value."""
        notebook = Notebook(name="Test", description="Test", archived=True)
        assert notebook.archived is True

    def test_notebook_optional_description(self):
        """Test that description can be empty."""
        notebook = Notebook(name="Test", description="")
        assert notebook.description == ""


class TestSource:
    """Tests for Source domain model."""

    def test_source_creation_basic(self):
        """Test basic source creation."""
        source = Source(title="Test Source")
        assert source.title == "Test Source"
        assert source.topics == []
        assert source.full_text is None

    def test_source_with_topics(self):
        """Test source creation with topics."""
        source = Source(title="Test", topics=["AI", "ML", "Python"])
        assert source.topics == ["AI", "ML", "Python"]

    def test_source_with_full_text(self):
        """Test source creation with full text content."""
        content = "This is a long text about artificial intelligence."
        source = Source(title="Test", full_text=content)
        assert source.full_text == content

    def test_source_command_field(self):
        """Test source with command field."""
        source = Source(title="Test", command="command:123")
        assert source.command is not None

    def test_source_id_validation_string(self):
        """Test source ID validation with string input."""
        source = Source(id="source:test123", title="Test")
        assert source.id == "source:test123"

    @pytest.mark.skip(reason="Requires database connection for get_insights()")
    def test_source_get_context_short(self):
        """Test get_context method with short context size."""
        # Note: get_context() calls get_insights() which requires database
        pass

    @pytest.mark.skip(reason="Requires database connection for get_insights()")
    def test_source_get_context_long(self):
        """Test get_context method with long context size."""
        # Note: get_context() calls get_insights() which requires database
        pass

    def test_source_empty_title_allowed(self):
        """Test that empty title is allowed (optional field)."""
        source = Source()
        assert source.title is None


class TestNote:
    """Tests for Note domain model."""

    def test_note_creation_basic(self):
        """Test basic note creation."""
        note = Note(title="Test Note", content="Test content")
        assert note.title == "Test Note"
        assert note.content == "Test content"

    def test_note_type_human(self):
        """Test note with human type."""
        note = Note(title="Test", content="Content", note_type="human")
        assert note.note_type == "human"

    def test_note_type_ai(self):
        """Test note with AI type."""
        note = Note(title="Test", content="Content", note_type="ai")
        assert note.note_type == "ai"

    def test_note_content_cannot_be_empty(self):
        """Test that note content cannot be empty string."""
        with pytest.raises(InvalidInputError, match="Note content cannot be empty"):
            Note(title="Test", content="")

    def test_note_content_whitespace_only(self):
        """Test that whitespace-only content is rejected."""
        with pytest.raises(InvalidInputError, match="Note content cannot be empty"):
            Note(title="Test", content="   ")

    def test_note_content_none_allowed(self):
        """Test that None content is allowed."""
        note = Note(title="Test", content=None)
        assert note.content is None

    def test_note_get_context_short(self):
        """Test get_context method with short context."""
        note = Note(id="note:test", title="Test", content="A" * 200)
        context = note.get_context(context_size="short")
        assert context["id"] == "note:test"
        assert context["title"] == "Test"
        assert len(context["content"]) <= 100

    def test_note_get_context_long(self):
        """Test get_context method with long context."""
        content = "A" * 1000
        note = Note(id="note:test", title="Test", content=content)
        context = note.get_context(context_size="long")
        assert context["id"] == "note:test"
        assert context["title"] == "Test"
        assert context["content"] == content

    def test_note_get_context_short_truncation(self):
        """Test that short context truncates content to 100 chars."""
        long_content = "A" * 500
        note = Note(id="note:test", title="Test", content=long_content)
        context = note.get_context(context_size="short")
        assert context["content"] == "A" * 100

    def test_note_empty_content_short_context(self):
        """Test short context with empty content."""
        note = Note(id="note:test", title="Test", content=None)
        context = note.get_context(context_size="short")
        assert context["content"] is None


class TestChatSession:
    """Tests for ChatSession domain model."""

    def test_chat_session_creation_basic(self):
        """Test basic chat session creation."""
        session = ChatSession(title="Test Session")
        assert session.title == "Test Session"
        assert session.model_override is None

    def test_chat_session_with_model_override(self):
        """Test chat session with model override."""
        session = ChatSession(title="Test", model_override="gpt-4")
        assert session.model_override == "gpt-4"

    def test_chat_session_nullable_fields(self):
        """Test that title and model_override can be None."""
        session = ChatSession()
        assert session.title is None
        assert session.model_override is None


class TestModelRelationships:
    """Tests for relationships between domain models."""

    def test_notebook_source_relationship_conceptual(self):
        """Conceptual test for notebook-source relationship."""
        notebook = Notebook(name="Research", description="AI Research")
        source = Source(title="AI Paper")
        # In real usage, these would be related via database
        assert notebook.name == "Research"
        assert source.title == "AI Paper"

    def test_notebook_note_relationship_conceptual(self):
        """Conceptual test for notebook-note relationship."""
        notebook = Notebook(name="Notes", description="My notes")
        note = Note(title="Idea", content="An idea")
        # In real usage, these would be related via database
        assert notebook.name == "Notes"
        assert note.title == "Idea"


class TestEdgeCases:
    """Edge case tests for all domain models."""

    def test_notebook_very_long_name(self):
        """Test notebook with very long name."""
        long_name = "A" * 1000
        notebook = Notebook(name=long_name, description="Test")
        assert notebook.name == long_name

    def test_notebook_special_characters_in_name(self):
        """Test notebook name with special characters."""
        name = "Test: Notebook @ 2024 #AI"
        notebook = Notebook(name=name, description="Test")
        assert notebook.name == name

    def test_source_unicode_title(self):
        """Test source with unicode title."""
        title = "测试中文标题 🚀"
        source = Source(title=title)
        assert source.title == title

    def test_note_multiline_content(self):
        """Test note with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        note = Note(title="Test", content=content)
        assert note.content == content

    def test_note_content_with_markdown(self):
        """Test note with markdown content."""
        content = "# Heading\n\n**Bold** and *italic*"
        note = Note(title="Test", content=content)
        assert note.content == content

    def test_source_topics_empty_list(self):
        """Test source with empty topics list."""
        source = Source(title="Test", topics=[])
        assert source.topics == []

    def test_source_topics_duplicate(self):
        """Test source with duplicate topics."""
        source = Source(title="Test", topics=["AI", "AI", "ML"])
        # Note: The model doesn't deduplicate, it stores as-is
        assert source.topics == ["AI", "AI", "ML"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
