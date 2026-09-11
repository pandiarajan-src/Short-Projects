import assembler
from youtube_client import Chapter


class TestSanitizeFilename:
    def test_removes_forbidden_characters(self):
        assert assembler.sanitize_filename('My: Video? <Title>*') == "My Video Title"

    def test_collapses_whitespace(self):
        assert assembler.sanitize_filename("My    Video") == "My Video"

    def test_empty_title_falls_back(self):
        assert assembler.sanitize_filename('???') == "Untitled Video"


class TestBuildDocument:
    def test_includes_title_link_and_toc(self):
        chapters = [
            Chapter(title="Intro", start_seconds=0, end_seconds=60),
            Chapter(title="Deep Dive", start_seconds=60, end_seconds=300),
        ]
        sections = [
            (chapters[0], "## Intro\n\nContent A"),
            (chapters[1], "## Deep Dive\n\nContent B"),
        ]

        document = assembler.build_document("My Video", "https://youtube.com/watch?v=abc", sections)

        assert document.startswith("# My Video")
        assert "**Video:** https://youtube.com/watch?v=abc" in document
        assert "- [Intro](#intro)" in document
        assert "- [Deep Dive](#deep-dive)" in document
        assert "Content A" in document
        assert "Content B" in document
        # Chapters appear in order
        assert document.index("Content A") < document.index("Content B")

    def test_toc_uses_actual_generated_heading_not_original_chapter_title(self):
        # Claude often paraphrases the chapter title we gave it. The TOC must
        # link to whatever heading actually ended up in the body, or the
        # anchor link is broken.
        chapter = Chapter(title="OpenClaw Setup AI Models (Clade, etc)", start_seconds=0, end_seconds=60)
        sections = [(chapter, "## Connecting AI Models to OpenClaw (Claude, etc.)\n\nBody text")]

        document = assembler.build_document("Video", "https://youtube.com/watch?v=abc", sections)

        assert "- [Connecting AI Models to OpenClaw (Claude, etc.)](#connecting-ai-models-to-openclaw-claude-etc)" in document
        assert "Clade" not in document

    def test_toc_falls_back_to_chapter_title_when_no_heading_found(self):
        chapter = Chapter(title="Fallback Title", start_seconds=0, end_seconds=60)
        sections = [(chapter, "Body text with no markdown heading")]

        document = assembler.build_document("Video", "https://youtube.com/watch?v=abc", sections)

        assert "- [Fallback Title](#fallback-title)" in document


class TestExtractHeading:
    def test_finds_first_level_two_heading(self):
        body = "Some preamble\n\n## The Real Title\n\nMore text"
        assert assembler._extract_heading(body, "fallback") == "The Real Title"

    def test_ignores_non_level_two_headings(self):
        body = "### Not this one\n## The Real Title"
        assert assembler._extract_heading(body, "fallback") == "The Real Title"

    def test_falls_back_when_no_heading_present(self):
        assert assembler._extract_heading("no headings here", "fallback") == "fallback"
