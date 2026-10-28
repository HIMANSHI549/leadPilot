import json

from src.rag_service import chunk_text
from src.tools import execute_tool


def test_execute_tool_rejects_unknown_name():
    result = json.loads(execute_tool("delete_everything", "{}"))
    assert "error" in result


def test_execute_tool_rejects_invalid_json():
    result = json.loads(execute_tool("find_stale_leads", "{not-json"))
    assert "error" in result


def test_execute_tool_rejects_negative_days():
    result = json.loads(execute_tool("find_stale_leads", '{"days": -3}'))
    assert "error" in result
    assert "days" in result["error"]


def test_execute_tool_rejects_missing_lead_id():
    result = json.loads(execute_tool("get_lead_details", "{}"))
    assert "error" in result


def test_chunk_text_creates_overlapping_chunks():
    text = "word " * 500
    chunks = chunk_text(text, chunk_size=80, overlap=20)
    assert len(chunks) > 1
    assert chunks[0][-10:] in chunks[1]
