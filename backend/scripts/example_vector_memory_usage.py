#!/usr/bin/env python3
"""
Example usage of the enhanced vector memory system with sentence-transformers.

This script demonstrates:
1. Basic embedding generation
2. Batch processing for efficiency
3. Storage and retrieval
4. Semantic similarity search
5. Model versioning

Prerequisites:
    - sentence-transformers installed
    - Vector backend configured (QDRANT, REDIS, or OFF)
"""

import sys
from pathlib import Path


# Add backend to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.memory import vecdb


def example_basic_usage():
    """Example 1: Basic embedding and similarity."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Embedding Generation")
    print("=" * 80)

    # Create a trading event
    event = {
        "ticker": "AAPL",
        "regime": "rally",
        "explain": {
            "shap_top": [["momentum", 0.85], ["sentiment", 0.72], ["volume", 0.65]]
        },
        "headlines": ["Apple stock surges on strong iPhone sales and AI announcements"],
    }

    # Generate embedding
    print(f"\nEvent: {event['ticker']} in {event['regime']} regime")
    embedding = vecdb.build_embedding(event)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {[f'{x:.4f}' for x in embedding[:5]]}")

    # Check model info
    model_info = vecdb.get_embedding_info()
    print(f"\nModel: {model_info['model_name']}")
    print(f"Version: {model_info['model_version']}")
    print(f"Status: {model_info['status']}")


def example_batch_processing():
    """Example 2: Batch processing for efficiency."""
    print("\n" + "=" * 80)
    print("Example 2: Batch Processing")
    print("=" * 80)

    # Multiple events to process
    events = [
        {
            "ticker": "AAPL",
            "regime": "rally",
            "explain": {"shap_top": [["momentum", 0.8]]},
            "headlines": ["Tech stocks rise"],
        },
        {
            "ticker": "MSFT",
            "regime": "rally",
            "explain": {"shap_top": [["sentiment", 0.7]]},
            "headlines": ["Microsoft beats earnings"],
        },
        {
            "ticker": "GOOGL",
            "regime": "normal",
            "explain": {"shap_top": [["fundamentals", 0.6]]},
            "headlines": ["Google announces new AI features"],
        },
        {
            "ticker": "TSLA",
            "regime": "high_vol",
            "explain": {"shap_top": [["volatility", 0.9]]},
            "headlines": ["Tesla stock volatile on production concerns"],
        },
        {
            "ticker": "NVDA",
            "regime": "rally",
            "explain": {"shap_top": [["momentum", 0.85]]},
            "headlines": ["NVIDIA soars on AI chip demand"],
        },
    ]

    print(f"\nProcessing {len(events)} events...")

    # Batch encode (much faster than individual encoding)
    embeddings = vecdb.build_embeddings_batch(events)

    print(f"Generated {len(embeddings)} embeddings")
    print(f"All embeddings are {len(embeddings[0])}-dimensional")

    # Show similarity between related events
    print("\n--- Similarity Analysis ---")

    # AAPL vs MSFT (both rally regime)
    sim_rally = vecdb._cosine_similarity(embeddings[0], embeddings[1])
    print(f"AAPL (rally) vs MSFT (rally): {sim_rally:.4f}")

    # AAPL vs NVDA (both tech rally with momentum)
    sim_tech = vecdb._cosine_similarity(embeddings[0], embeddings[4])
    print(f"AAPL (rally) vs NVDA (rally): {sim_tech:.4f}")

    # AAPL vs TSLA (different regimes)
    sim_diff = vecdb._cosine_similarity(embeddings[0], embeddings[3])
    print(f"AAPL (rally) vs TSLA (high_vol): {sim_diff:.4f}")


def example_storage_and_search():
    """Example 3: Storage and similarity search."""
    print("\n" + "=" * 80)
    print("Example 3: Storage and Search")
    print("=" * 80)

    # Check backend configuration
    stats = vecdb.get_collection_stats()
    print(f"\nBackend: {stats['backend']}")
    print(f"Status: {stats['status']}")

    if stats["backend"] == "OFF":
        print(
            "\n⚠️  Backend is OFF mode. To test storage, set VECDB_BACKEND=QDRANT or REDIS"
        )
        return

    # Store some events
    events_to_store = [
        {
            "ticker": "AAPL",
            "regime": "rally",
            "explain": {"shap_top": [["momentum", 0.8]]},
            "date": "2024-01-15",
        },
        {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["sentiment", 0.5]]},
            "date": "2024-01-16",
        },
        {
            "ticker": "TSLA",
            "regime": "high_vol",
            "explain": {"shap_top": [["volatility", 0.9]]},
            "date": "2024-01-15",
        },
    ]

    print(f"\nStoring {len(events_to_store)} events...")

    embeddings = vecdb.build_embeddings_batch(events_to_store)
    for i, (event, embedding) in enumerate(zip(events_to_store, embeddings)):
        event_id = f"evt_{event['ticker']}_{event['date']}_{i}"
        vecdb.upsert_event(
            event_id=event_id,
            vec=embedding,
            metadata={
                "ticker": event["ticker"],
                "regime": event["regime"],
                "date": event["date"],
            },
        )
        print(f"  Stored: {event_id}")

    # Search for similar events
    print("\nSearching for events similar to AAPL rally...")
    query_event = events_to_store[0]  # AAPL rally
    query_embedding = embeddings[0]

    results = vecdb.search_similar(query_embedding, k=3)

    print(f"Found {len(results)} similar events:")
    for result in results:
        print(f"  Score: {result['score']:.4f}")
        print(f"  Metadata: {result['metadata']}")
        print()


def example_model_versioning():
    """Example 4: Model versioning for migrations."""
    print("\n" + "=" * 80)
    print("Example 4: Model Versioning")
    print("=" * 80)

    # Get current model version
    model_info = vecdb.get_embedding_info()
    print(f"\nCurrent embedding model: {model_info['model_name']}")
    print(f"Current version: {model_info['model_version']}")

    # When storing, version is automatically included
    event = {
        "ticker": "NVDA",
        "regime": "rally",
        "explain": {"shap_top": [["momentum", 0.9]]},
    }

    embedding = vecdb.build_embedding(event)
    metadata = {"ticker": "NVDA", "regime": "rally"}

    # The upsert will add embed_model and embed_model_version automatically
    print("\nWhen upserting, metadata will include:")
    print(f"  - embed_model: {model_info['model_name']}")
    print(f"  - embed_model_version: {model_info['model_version']}")
    print(f"  - Original metadata: {metadata}")

    # This allows filtering by version during searches
    print(
        "\nYou can filter searches to only use embeddings from specific model versions"
    )
    print("Example: filter_metadata={'embed_model_version': 'v1.0-transformer'}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("Vector Memory System - Usage Examples")
    print("=" * 80)

    # Run examples
    example_basic_usage()
    example_batch_processing()
    example_storage_and_search()
    example_model_versioning()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print("\nFor more details, see: docs/vector_memory.md")
    print("To evaluate performance, run: python scripts/eval_vector_memory.py")
    print()


if __name__ == "__main__":
    main()
