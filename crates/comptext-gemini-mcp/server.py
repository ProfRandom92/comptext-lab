#!/usr/bin/env python3
"""
comptext-gemini-mcp
───────────────────
Google Gemini MCP server for Antigravity CLI (agy-ct).
Default: gemini-2.5-flash @ HIGH thinking budget (24 576 tokens).

Env vars:
  GOOGLE_API_KEY     required
  GEMINI_MODEL       default: gemini-2.5-flash
  THINKING_BUDGET    default: 24576  (HIGH)
                     options: 24576=high · 8192=medium · 1024=low · 0=off
"""

import json
import os
from pathlib import Path

from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY       = os.environ.get("GOOGLE_API_KEY", "")
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
BUDGET_HIGH   = 24576   # gemini-2.5-flash max
BUDGET_MED    = 8192
BUDGET_LOW    = 1024
BUDGET_OFF    = 0
DEFAULT_BUDGET = int(os.environ.get("THINKING_BUDGET", str(BUDGET_HIGH)))

QUALITY_MAP = {
    "high":   BUDGET_HIGH,
    "medium": BUDGET_MED,
    "low":    BUDGET_LOW,
    "off":    BUDGET_OFF,
}

# ── Client ────────────────────────────────────────────────────────────────────
_client: genai.Client | None = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        key = os.environ.get("GOOGLE_API_KEY", API_KEY)
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        _client = genai.Client(api_key=key)
    return _client

def make_cfg(
    quality: str = "high",
    system: str = "",
    json_mode: bool = False,
    schema: dict | None = None,
) -> types.GenerateContentConfig:
    budget = QUALITY_MAP.get(quality, DEFAULT_BUDGET)
    kwargs: dict = dict(
        thinkingConfig=types.ThinkingConfig(
            thinkingBudget=budget,
            includeThoughts=False,
        ),
        temperature=1.0,
    )
    if system:
        kwargs["systemInstruction"] = system
    if json_mode:
        kwargs["responseMimeType"] = "application/json"
    if schema:
        kwargs["responseSchema"] = schema
    return types.GenerateContentConfig(**kwargs)

# ── MCP server ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="comptext-gemini-mcp",
    instructions=(
        "Google Gemini MCP for Antigravity CLI. "
        "Default model: gemini-2.5-flash at HIGH thinking budget (24 576 tokens). "
        "Use gemini_generate for text, gemini_generate_json for structured output, "
        "gemini_analyze_dpl for CompText DPL corpus analysis."
    ),
)

# ── Tool 1: generate ──────────────────────────────────────────────────────────
@mcp.tool()
def gemini_generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    quality: str = "high",
    system: str = "",
    max_tokens: int = 8192,
) -> str:
    """
    Generate text with Google Gemini at configurable thinking quality.

    Args:
        prompt:     User prompt text.
        model:      Gemini model string (default: gemini-2.5-flash).
        quality:    Thinking budget — "high" | "medium" | "low" | "off".
                    "high" = 24 576 tokens (default, recommended).
        system:     Optional system instruction.
        max_tokens: Maximum output tokens (default: 8 192).

    Returns:
        Generated text.
    """
    cfg = make_cfg(quality=quality, system=system)
    cfg.maxOutputTokens = max_tokens
    resp = get_client().models.generate_content(
        model=model,
        contents=prompt,
        config=cfg,
    )
    return resp.text or ""


# ── Tool 2: generate_json ─────────────────────────────────────────────────────
@mcp.tool()
def gemini_generate_json(
    prompt: str,
    json_schema: str = "",
    model: str = DEFAULT_MODEL,
    quality: str = "high",
    system: str = "",
) -> str:
    """
    Generate structured JSON output from Gemini.

    Args:
        prompt:      User prompt.
        json_schema: Optional JSON Schema string to constrain output shape.
                     Example: '{"type":"object","properties":{"name":{"type":"string"}}}'
                     Leave empty for free-form JSON.
        model:       Gemini model string.
        quality:     Thinking budget — "high" | "medium" | "low" | "off".
        system:      Optional system instruction.

    Returns:
        Raw JSON string.
    """
    schema = json.loads(json_schema) if json_schema.strip() else None
    cfg = make_cfg(quality=quality, system=system, json_mode=True, schema=schema)
    resp = get_client().models.generate_content(
        model=model,
        contents=prompt,
        config=cfg,
    )
    return resp.text or "{}"


# ── Tool 3: analyze_dpl ───────────────────────────────────────────────────────
@mcp.tool()
def gemini_analyze_dpl(
    dpl_path: str,
    question: str,
    model: str = DEFAULT_MODEL,
    quality: str = "high",
) -> str:
    """
    Analyze a CompText DPL file with Gemini at HIGH thinking quality.

    Reads the .dpl corpus, sends it to Gemini with the given question,
    and returns a precise, technically grounded answer.

    Args:
        dpl_path: Absolute or relative path to a .dpl file.
        question: What to analyze, extract, or summarize from the corpus.
        model:    Gemini model string.
        quality:  Thinking budget — "high" | "medium" | "low" | "off".

    Returns:
        Analysis result as text.
    """
    path = Path(dpl_path).expanduser().resolve()
    if not path.exists():
        return f"ERROR: file not found: {path}"
    if path.suffix.lower() != ".dpl":
        return f"ERROR: expected .dpl file, got '{path.suffix}'"

    corpus = path.read_text(encoding="utf-8")
    lines  = corpus.count("\n") + 1
    chars  = len(corpus)

    system = (
        "You are a CompText DPL analyst. "
        "DPL (Deep Perception Language) is a compact, token-efficient knowledge representation format. "
        "§DOM: blocks are knowledge domains. §EDGES define cross-domain relationships. "
        "§SYNTHESIS is the global conclusion. "
        "Answer precisely and technically, grounded in the corpus content."
    )

    prompt = (
        f"<dpl_corpus name=\"{path.name}\" lines=\"{lines}\" chars=\"{chars}\">\n"
        f"{corpus}\n"
        f"</dpl_corpus>\n\n"
        f"Question: {question}"
    )

    cfg = make_cfg(quality=quality, system=system)
    resp = get_client().models.generate_content(model=model, contents=prompt, config=cfg)
    return resp.text or ""


# ── Tool 4: embed ─────────────────────────────────────────────────────────────
@mcp.tool()
def gemini_embed(
    texts: list[str],
    model: str = "text-embedding-004",
    task_type: str = "SEMANTIC_SIMILARITY",
) -> str:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts:     List of strings to embed (max 100 per call).
        model:     Embedding model (default: text-embedding-004).
        task_type: SEMANTIC_SIMILARITY | RETRIEVAL_DOCUMENT |
                   RETRIEVAL_QUERY | CLASSIFICATION | CLUSTERING.

    Returns:
        JSON array of embedding vectors (list[list[float]]).
    """
    c = get_client()
    result = []
    for text in texts[:100]:
        resp = c.models.embed_content(
            model=model,
            contents=text,
            config=types.EmbedContentConfig(taskType=task_type),
        )
        result.append(resp.embeddings[0].values)
    return json.dumps(result)


# ── Tool 5: count_tokens ──────────────────────────────────────────────────────
@mcp.tool()
def gemini_count_tokens(
    text: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Count tokens for a text string before submitting to Gemini.

    Args:
        text:  Input string.
        model: Gemini model to count tokens for.

    Returns:
        JSON: {"total_tokens": int, "model": str}
    """
    resp = get_client().models.count_tokens(model=model, contents=text)
    return json.dumps({"total_tokens": resp.totalTokens, "model": model})


# ── Tool 6: list_models ───────────────────────────────────────────────────────
@mcp.tool()
def gemini_list_models(filter_prefix: str = "gemini") -> str:
    """
    List available Google Generative AI models.

    Args:
        filter_prefix: Only return models whose name contains this string.
                       Default: "gemini". Use "" for all models.

    Returns:
        JSON array of model name strings, sorted alphabetically.
    """
    models = get_client().models.list()
    names = sorted(
        m.name for m in models
        if not filter_prefix or filter_prefix.lower() in m.name.lower()
    )
    return json.dumps(names)


# ── Tool 7: set_quality ───────────────────────────────────────────────────────
@mcp.tool()
def gemini_quality_info() -> str:
    """
    Return the current default model and thinking budget configuration.

    Returns:
        JSON with current config values and available quality levels.
    """
    return json.dumps({
        "default_model":   DEFAULT_MODEL,
        "default_budget":  DEFAULT_BUDGET,
        "active_quality":  next(
            (k for k, v in QUALITY_MAP.items() if v == DEFAULT_BUDGET), "custom"
        ),
        "quality_levels": {
            "high":   BUDGET_HIGH,
            "medium": BUDGET_MED,
            "low":    BUDGET_LOW,
            "off":    BUDGET_OFF,
        },
        "env_vars": {
            "GOOGLE_API_KEY":  "set" if API_KEY else "NOT SET",
            "GEMINI_MODEL":    DEFAULT_MODEL,
            "THINKING_BUDGET": DEFAULT_BUDGET,
        },
    })


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
