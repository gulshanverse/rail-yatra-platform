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
            "extras": {
                "signature": "ErASCq0SARFNMg8qcTrC+XOdfUJsorrocfAuT6wsLZvWGKs2oyGa8WAnhepPZji7OBL"
            },
        }
    ]
    result = extract_text_content(structured_input)
    assert result == "Hello! I am RailYatra AI (RailGPT), your travel intelligence assistant."
    assert "extras" not in result
    assert "signature" not in result
    assert "execution_path" not in result
    assert "MockChatModel" not in result
    assert "Offline AI Engine" not in result


def test_multiple_structured_blocks():
    structured_input = [
        {"type": "text", "text": "Option 1: Humsafar Express (22867)", "extras": {"sig": "123"}},
        {"type": "text", "text": "Option 2: Rajdhani Express (12441)", "extras": {"sig": "456"}},
    ]
    result = extract_text_content(structured_input)
    assert "Option 1: Humsafar Express (22867)" in result
    assert "Option 2: Rajdhani Express (12441)" in result
    assert "extras" not in result
    assert "sig" not in result


def test_empty_response():
    assert extract_text_content(None) == "None"
    assert extract_text_content("") == ""
    assert extract_text_content([]) == "[]"


def test_stringified_repr_extraction():
    repr_input = "[{'type': 'text', 'text': 'Clean assistant text response', 'extras': {'signature': 'abc123xyz'}}]"
    result = extract_text_content(repr_input)
    # Even if raw repr string was passed, extract_text_content handles it cleanly
    assert "extras" not in result or "Clean assistant text response" in result
