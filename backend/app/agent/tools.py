# app/agent/tools.py
from typing import Any

from app.rag.ingest_web import fetch_and_extract, search_web
from app.rag.retriever import retrieve
from app.utils.text import clean_text


# JSON schemas for tool-calling LLMs
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for recent information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and extract main text from a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "http/https URL"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kb_retrieve",
            "description": "Retrieve relevant chunks from the indexed knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
            },
        },
    },
]


# The actual tool implementations the server runs:
def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "web_search":
        q = args.get("query", "")
        k = int(args.get("max_results", 5))
        res = search_web(q, max_results=k)
        return {"results": res}
    if name == "web_fetch":
        url = args["url"]
        text = fetch_and_extract(url) or ""
        return {"url": url, "text": clean_text(text)[:8000]}
    if name == "kb_retrieve":
        q = args["query"]
        k = int(args.get("top_k", 5))
        res = retrieve(q, top_k=k)
        # keep it small
        for r in res:
            r["text"] = r.get("text", "")[:1500]
        return {"results": res}
    return {"error": f"Unknown tool {name}"}
