"""The AI layer seam (AI_ARCHITECTURE): Model Router and provider adapters.

Every LLM and embedding call passes through the ModelRouter (ADR-06); no
other module calls a provider directly.
"""
