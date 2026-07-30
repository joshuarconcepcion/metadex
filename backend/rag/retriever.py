"""Similarity search over ingested community content.

Phase 1: will wrap rag/store.py's Chroma collection with a retriever
the LangGraph agent can call as a tool for grounding advice in
community-sourced context (raid strategies, meta discussion, etc).
"""
