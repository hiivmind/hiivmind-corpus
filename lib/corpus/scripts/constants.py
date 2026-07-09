"""Shared constants for the embedding pipeline.

Single source of truth for the model identity and Lance table layout.
detect.py, embed.py, and search.py import from here — do not redefine
these values in individual scripts.
"""

MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384
TABLE_NAME = "embeddings"
CHUNKS_TABLE_NAME = "chunks"
META_TABLE = "_meta"
PASSAGE_PREFIX = "passage: "  # bge-small asymmetric retrieval prefix for documents
QUERY_PREFIX = "query: "  # bge-small asymmetric retrieval prefix for queries
VECTOR_INDEX_THRESHOLD = 500  # Create IVF_PQ index above this entry count
