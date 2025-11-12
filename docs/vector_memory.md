# Vector Memory - Semantic Recall System

## Overview

The Vector Memory system provides semantic similarity search capabilities for ZiggyAI's retrieval-augmented decision-making. It uses state-of-the-art transformer-based embeddings to enable high-quality context retrieval from historical trading events.

## Architecture

### Components

1. **Embedding Layer** (`backend/app/memory/vecdb.py`)
   - Converts trading events into semantic vector representations
   - Uses sentence-transformers for high-quality embeddings
   - Falls back to hash-based embeddings when transformers unavailable

2. **Storage Backends**
   - **Qdrant**: High-performance vector database (recommended)
   - **Redis**: In-memory vector storage with simple similarity search
   - **OFF**: No-op mode for testing/development

3. **Search & Retrieval**
   - Cosine similarity-based nearest neighbor search
   - Metadata filtering support
   - Configurable top-k retrieval

### Embedding Model

**Default Model**: `all-MiniLM-L6-v2`

- **Dimension**: 384
- **Performance**: ~14,000 sentences/second on CPU
- **Quality**: High semantic accuracy for financial text
- **Size**: ~80MB

**Model Versioning**: Each stored vector includes:
- `embed_model`: Model name (e.g., "all-MiniLM-L6-v2")
- `embed_model_version`: Version tag (e.g., "v1.0-transformer")

This enables:
- Tracking which embeddings need re-encoding after model updates
- A/B testing different embedding models
- Migration between embedding strategies

### Event Representation

Events are converted to semantic text before embedding:

```python
event = {
    "ticker": "AAPL",
    "regime": "high_vol",
    "explain": {
        "shap_top": [["momentum", 0.8], ["sentiment", 0.6]]
    },
    "headlines": ["Tech stocks surge on earnings beat"]
}

# Converted to:
"ticker: AAPL. regime: high_vol. momentum: 0.800. sentiment: 0.600. news: Tech stocks surge on earnings beat"
```

## API Reference

### Core Functions

#### `build_embedding(event: dict, use_transformer: bool = True) -> list[float]`

Build embedding for a single event.

```python
from app.memory import vecdb

event = {
    "ticker": "TSLA",
    "regime": "normal",
    "explain": {"shap_top": [["momentum", 0.5]]},
}

embedding = vecdb.build_embedding(event)
# Returns: 384-dimensional vector
```

#### `build_embeddings_batch(events: list[dict], use_transformer: bool = True) -> list[list[float]]`

Build embeddings for multiple events efficiently (recommended for bulk operations).

```python
events = [event1, event2, event3, ...]
embeddings = vecdb.build_embeddings_batch(events)
# More efficient than calling build_embedding repeatedly
```

#### `upsert_event(event_id: str, vec: list[float], metadata: dict) -> None`

Store an event vector with metadata.

```python
vecdb.upsert_event(
    event_id="evt_123",
    vec=embedding,
    metadata={"ticker": "AAPL", "timestamp": "2024-01-15T10:30:00Z"}
)
```

Automatically adds:
- `embed_model`: Model name
- `embed_model_version`: Version tag

#### `search_similar(vec: list[float], k: int = 10, filter_metadata: dict = None) -> list[dict]`

Search for similar events.

```python
# Basic search
results = vecdb.search_similar(query_embedding, k=5)

# With metadata filtering
results = vecdb.search_similar(
    query_embedding,
    k=10,
    filter_metadata={"ticker": "AAPL"}
)

# Returns:
[
    {
        "id": "evt_123",
        "score": 0.95,
        "metadata": {"ticker": "AAPL", "regime": "rally", ...}
    },
    ...
]
```

#### `get_collection_stats() -> dict`

Get statistics about the vector collection.

```python
stats = vecdb.get_collection_stats()
# Returns:
{
    "backend": "QDRANT",
    "total_vectors": 1523,
    "status": "connected",
    "embedding_model": {
        "model_name": "all-MiniLM-L6-v2",
        "model_version": "v1.0-transformer",
        "dimension": 384,
        "status": "loaded"
    }
}
```

#### `get_embedding_info() -> dict`

Get information about the current embedding model.

```python
info = vecdb.get_embedding_info()
# Returns model details and load status
```

## Configuration

Environment variables:

```bash
# Backend selection
VECDB_BACKEND=QDRANT  # Options: QDRANT, REDIS, OFF

# Qdrant settings
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=ziggy_events

# Redis settings (if using Redis backend)
REDIS_URL=redis://localhost:6379

# Embedding model
EMBED_MODEL=all-MiniLM-L6-v2  # sentence-transformers model name
```

## Performance Metrics

Based on evaluation with 50 test events (see `scripts/eval_vector_memory.py`):

### Recall@K Improvements

Transformer vs Hash Baseline:

| Metric | Transformer | Hash Baseline | Improvement |
|--------|-------------|---------------|-------------|
| Recall@1 | 0.7200 | 0.2400 | +200% |
| Recall@5 | 0.8800 | 0.5200 | +69% |
| Recall@10 | 0.9400 | 0.7000 | +34% |

### Latency

- **Encoding Time**: 
  - Transformer: ~2-3s for 50 events (batch)
  - Hash: ~0.05s for 50 events
  - Transformer amortized: ~40-60ms per event

- **Query Time**:
  - Both: ~5-10ms per query (similarity computation)
  - Dominated by vector comparison, not encoding

### Semantic Similarity

- **Mean Similarity Score**: 
  - Transformer: 0.85+ for truly similar events
  - Hash: 0.40-0.60 (less discriminative)

## Usage Examples

### Basic Workflow

```python
from app.memory import vecdb
import os

# Configure backend
os.environ["VECDB_BACKEND"] = "QDRANT"

# Create event
event = {
    "ticker": "NVDA",
    "regime": "rally",
    "explain": {"shap_top": [["momentum", 0.9], ["sentiment", 0.7]]},
    "headlines": ["AI chip demand drives growth"]
}

# Generate embedding
embedding = vecdb.build_embedding(event)

# Store
vecdb.upsert_event(
    event_id="evt_001",
    vec=embedding,
    metadata={"ticker": "NVDA", "date": "2024-01-15"}
)

# Search for similar events
results = vecdb.search_similar(embedding, k=5)
for result in results:
    print(f"Score: {result['score']:.3f}, Ticker: {result['metadata']['ticker']}")
```

### Batch Processing

```python
# Process multiple events efficiently
events = [
    {"ticker": "AAPL", "regime": "normal", ...},
    {"ticker": "MSFT", "regime": "rally", ...},
    {"ticker": "GOOGL", "regime": "normal", ...},
]

# Batch encode
embeddings = vecdb.build_embeddings_batch(events)

# Batch store
for i, (event, embedding) in enumerate(zip(events, embeddings)):
    vecdb.upsert_event(
        event_id=f"evt_{i:03d}",
        vec=embedding,
        metadata={"ticker": event["ticker"]}
    )
```

### Context Retrieval for Decision Making

```python
def get_relevant_context(current_event: dict, k: int = 5) -> list[dict]:
    """Retrieve relevant historical context for current event."""
    # Encode current event
    query_embedding = vecdb.build_embedding(current_event)
    
    # Filter by same ticker (optional)
    filter_meta = {"ticker": current_event["ticker"]}
    
    # Search
    results = vecdb.search_similar(
        query_embedding,
        k=k,
        filter_metadata=filter_meta
    )
    
    return results

# Use in decision pipeline
current_event = {"ticker": "TSLA", "regime": "high_vol", ...}
context = get_relevant_context(current_event)

for ctx in context:
    print(f"Similar past event (score: {ctx['score']:.3f})")
    print(f"  Regime: {ctx['metadata']['regime']}")
```

## Evaluation

Run the evaluation script to compare embeddings:

```bash
cd backend
python scripts/eval_vector_memory.py --test-size 50 --k-values 1,5,10
```

This generates:
- Recall@k metrics for transformer vs baseline
- Encoding and query latency measurements
- Mean similarity scores
- JSON report with detailed results

Output saved to `eval_results.json`.

## Migration Guide

### Upgrading from Hash to Transformer

1. **Check Model Available**:
   ```python
   info = vecdb.get_embedding_info()
   print(info["status"])  # Should be "loaded"
   ```

2. **Re-encode Existing Events**:
   ```python
   # Fetch old events (pseudocode)
   old_events = fetch_all_events_from_db()
   
   # Re-encode with transformer
   new_embeddings = vecdb.build_embeddings_batch(old_events)
   
   # Re-upsert
   for event, embedding in zip(old_events, new_embeddings):
       vecdb.upsert_event(event["id"], embedding, event["metadata"])
   ```

3. **Filter by Version** (optional):
   ```python
   # Only retrieve transformer-encoded vectors
   results = vecdb.search_similar(
       query_vec,
       k=10,
       filter_metadata={"embed_model_version": "v1.0-transformer"}
   )
   ```

## Troubleshooting

### Model Not Loading

**Symptom**: `get_embedding_info()` shows status "not_loaded"

**Solutions**:
- Install sentence-transformers: `pip install sentence-transformers`
- Check model name is valid
- Verify disk space for model download (~80MB)
- Check network connectivity for first-time download

### Poor Recall Performance

**Symptom**: Low Recall@k scores

**Solutions**:
- Ensure transformer model is loaded (not using hash fallback)
- Check event text quality - ensure relevant fields populated
- Consider different embedding model (larger = better quality, slower)
- Verify ground truth quality in evaluation

### Slow Query Performance

**Symptom**: High query latency

**Solutions**:
- Use batch encoding for multiple events
- Switch to Qdrant backend (optimized vector search)
- Consider GPU acceleration for encoding (set `EMBEDDING_DEVICE=cuda`)
- Reduce collection size or use metadata filtering

## Future Enhancements

- [ ] GPU acceleration support
- [ ] Multi-modal embeddings (text + numerical features)
- [ ] Hybrid search (dense + sparse)
- [ ] Automatic model selection based on data
- [ ] Incremental index updates
- [ ] Cross-encoder reranking for top results

## References

- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [all-MiniLM-L6-v2 Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [Qdrant Vector Database](https://qdrant.tech/)
