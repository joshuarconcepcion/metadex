"""ChromaDB vector store setup.

Phase 1: will initialize a persistent Chroma collection at
settings.chroma_db_path and expose add/upsert helpers for the documents
produced by rag/ingestion.py.
"""
