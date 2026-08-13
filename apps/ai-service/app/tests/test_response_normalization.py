from app.agents.base import extract_text_content


def test_plain_text_assistant_response():
    input_text = "Here are the best train options for your journey from Bilaspur to Delhi."
    result = extract_text_content(input_text)
    assert result == input_text
    assert "extras" not in result
    assert "signature" not in result


def test_structured_text_response_with_extras_and_signature():
    structured_input = [
        {
            "type": "text",
            "text": "Hello! I am RailYatra AI (RailGPT), your travel intelligence assistant.",
            "extras": {"signature": "secret-provider-signature"},
        }
    ]
    result = extract_text_content(structured_input)
    assert result == "Hello! I am RailYatra AI (RailGPT), your travel intelligence assistant."
    assert "extras" not in result
    assert "signature" not in result
    assert "execution_path" not in result


def test_multiple_structured_blocks():
    structured_input = [
        {"type": "text", "text": "Option 1: Humsafar Express (22867)", "extras": {"sig": "123"}},
        {"type": "text", "text": "Option 2: Rajdhani Express (12441)", "extras": {"sig": "456"}},
    ]
    result = extract_text_content(structured_input)
    assert result == "Option 1: Humsafar Express (22867)\n\nOption 2: Rajdhani Express (12441)"
    assert "extras" not in result
    assert "sig" not in result


def test_dict_response_extracts_text_without_metadata():
    result = extract_text_content(
        {"type": "text", "text": "Clean assistant text", "extras": {"signature": "abc"}}
    )
    assert result == "Clean assistant text"
    assert "signature" not in result


def test_empty_and_none_responses_are_safe():
    assert extract_text_content(None) == ""
    assert extract_text_content("") == ""
    assert extract_text_content([]) == ""
    assert extract_text_content({}) == ""


def test_string_content_is_trimmed():
    assert extract_text_content("  Good morning, Gulshan!  ") == "Good morning, Gulshan!"
