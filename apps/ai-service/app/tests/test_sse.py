import json

from app.api.sse import SSEEvent, format_sse, parse_sse_buffer


def test_parse_sse_preserves_incomplete_network_chunk():
    first = 'data: ' + json.dumps({'type': 'token', 'value': 'hel')
    second = json.dumps({'type': 'token', 'value': 'lo'}) + '\n\n'

    events, remainder = parse_sse_buffer(first)
    assert events == []
    assert remainder == first

    events, remainder = parse_sse_buffer(remainder + second)
    assert events == [SSEEvent(data=json.dumps({'type': 'token', 'value': 'hello'}))]
    assert remainder == ''


def test_parse_multiple_events_in_one_chunk():
    chunk = (
        format_sse({'type': 'token', 'value': 'Hello'})
        + format_sse({'type': 'done', 'reply': 'Hello world'})
    )
    events, remainder = parse_sse_buffer(chunk)

    assert remainder == ''
    assert len(events) == 2
    assert json.loads(events[0].data)['value'] == 'Hello'
    assert json.loads(events[1].data)['reply'] == 'Hello world'


def test_parse_event_metadata_and_multiline_data():
    raw = 'id: 42\nevent: message\ndata: line one\ndata: line two\n\n'
    events, remainder = parse_sse_buffer(raw)

    assert remainder == ''
    assert events == [SSEEvent(data='line one\nline two', event='message', event_id='42')]


def test_format_sse_is_json_safe_and_terminated():
    rendered = format_sse({'type': 'token', 'value': 'नमस्ते'}, event='message', event_id='7')
    assert rendered.endswith('\n\n')
    assert 'event: message\n' in rendered
    assert 'id: 7\n' in rendered
    assert 'data: {"type": "token", "value": "नमस्ते"}\n' in rendered
