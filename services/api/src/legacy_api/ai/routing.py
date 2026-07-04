"""Versioned routing configuration (AIA-05, AIA-07).

Production traffic runs only on exact pinned model identifiers held here.
Aliases that auto-track "latest" are forbidden: nothing changes silently.
Changing any pin requires the AIA-08 upgrade gate and a new ADR in
MASTER_ARCHITECTURE.
"""

ROUTING_CONFIG_VERSION = 1

# Task class: embedding (ADR-16). The exact pinned identifier, never an
# alias; dimension fixed via output_dimensionality (Matryoshka truncation,
# a documented recommended size); vectors are L2-normalized at write and
# query time (required by the provider at non-default dimensions) and
# compared with cosine distance.
EMBEDDING_PROVIDER = "gemini"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 1536
EMBEDDING_MODEL_VERSION = "gemini-embedding-001:1536"

# Documented per-text input limit for the pinned model; longer inputs are
# truncated by the provider, so the chunker must stay well below this.
EMBEDDING_INPUT_TOKEN_LIMIT = 2048
