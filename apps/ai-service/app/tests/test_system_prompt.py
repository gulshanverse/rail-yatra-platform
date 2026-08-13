from app.prompts.system import SYSTEM_PERSONA


def test_system_persona_prioritizes_natural_conversation():
    assert "warm, natural, concise" in SYSTEM_PERSONA
    assert "greetings" in SYSTEM_PERSONA.lower()
    assert "1–4 sentences" in SYSTEM_PERSONA


def test_system_persona_blocks_internal_metadata():
    assert "provider metadata" in SYSTEM_PERSONA
    assert "tool traces" in SYSTEM_PERSONA
    assert "internal reasoning" in SYSTEM_PERSONA


def test_system_persona_uses_markdown_selectively():
    assert "standard Markdown" in SYSTEM_PERSONA
    assert "Use tables only for genuinely tabular comparisons" in SYSTEM_PERSONA
