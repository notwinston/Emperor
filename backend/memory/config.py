"""mem0 Configuration for Emperor Memory System.

Provides two configuration options:
- MEM0_CONFIG: Full configuration with OpenAI embeddings and Neo4j knowledge graph
- MEM0_LOCAL_CONFIG: Local-only configuration using HuggingFace and ChromaDB
"""

import os
from typing import Dict, Any

# Full Configuration (Cloud/Production)
# Requires: OpenAI API key, Neo4j instance, Anthropic API key
MEM0_CONFIG: Dict[str, Any] = {
    "version": "v1.1",  # Enables knowledge graph feature
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "emperor_memories",
            "path": os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "chroma",
            ),
        },
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": os.getenv("NEO4J_URL", "bolt://localhost:7687"),
            "username": os.getenv("NEO4J_USERNAME", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD", "password"),
        },
    },
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-sonnet-4-20250514",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
    },
}

# Local Configuration (Development)
# Uses local embeddings (HuggingFace) but requires Anthropic for memory extraction
MEM0_LOCAL_CONFIG: Dict[str, Any] = {
    "version": "v1.1",
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
        },
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "emperor_memories",
            "path": os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "chroma",
            ),
        },
    },
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-sonnet-4-20250514",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
    },
}


def get_config(use_local: bool = True) -> Dict[str, Any]:
    """Get the appropriate mem0 configuration.

    Args:
        use_local: If True, returns local config (no external APIs).
                   If False, returns full config with OpenAI/Neo4j.

    Returns:
        Configuration dictionary for mem0.Memory.from_config()
    """
    return MEM0_LOCAL_CONFIG if use_local else MEM0_CONFIG


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate that required configuration values are present.

    Args:
        config: mem0 configuration dictionary

    Returns:
        True if valid, raises ValueError if not
    """
    # Check embedder
    if config.get("embedder", {}).get("provider") == "openai":
        api_key = config.get("embedder", {}).get("config", {}).get("api_key")
        if not api_key:
            raise ValueError("OpenAI API key required for openai embedder")

    # Check graph store
    if "graph_store" in config:
        graph_config = config["graph_store"].get("config", {})
        if not graph_config.get("password"):
            raise ValueError("Neo4j password required for graph store")

    # Check LLM
    if "llm" in config:
        llm_config = config["llm"].get("config", {})
        if config["llm"].get("provider") == "anthropic" and not llm_config.get("api_key"):
            raise ValueError("Anthropic API key required for LLM")

    return True
