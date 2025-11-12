#!/usr/bin/env python3
"""
Evaluation script for vector memory semantic recall.

Compares transformer-based embeddings vs hash-based baseline on:
- Recall@k (1, 5, 10)
- Semantic similarity scores
- Query latency

Usage:
    python scripts/eval_vector_memory.py [--test-size N] [--k-values K1,K2,K3]
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any


# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.memory import vecdb


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def generate_test_events(n: int = 50) -> list[dict[str, Any]]:
    """Generate synthetic test events for evaluation."""
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]
    regimes = ["normal", "high_vol", "crash", "rally", "consolidation"]
    features = [
        "momentum",
        "sentiment",
        "volatility",
        "fundamentals",
        "technical",
        "news_impact",
        "market_correlation",
    ]

    events = []
    for i in range(n):
        ticker_idx = i % len(tickers)
        regime_idx = i % len(regimes)

        # Create correlated groups for testing semantic similarity
        if i < 10:
            # Tech momentum cluster
            ticker = tickers[ticker_idx % 3]  # AAPL, MSFT, GOOGL
            regime = "rally"
            top_features = [["momentum", 0.8], ["sentiment", 0.6]]
            headlines = ["Tech stocks surge on earnings beat"]
        elif i < 20:
            # High volatility cluster
            ticker = "TSLA"
            regime = "high_vol"
            top_features = [["volatility", 0.9], ["news_impact", 0.7]]
            headlines = ["Market volatility spikes on regulatory concerns"]
        elif i < 30:
            # Crash cluster
            ticker = tickers[ticker_idx % len(tickers)]
            regime = "crash"
            top_features = [["market_correlation", 0.85], ["sentiment", -0.8]]
            headlines = ["Market downturn on economic data"]
        else:
            # Random normal events
            ticker = tickers[ticker_idx]
            regime = regimes[regime_idx]
            top_features = [[features[j % len(features)], (i * j % 100) / 100.0] for j in range(3)]
            headlines = [f"Market update for {ticker}"]

        event = {
            "ticker": ticker,
            "regime": regime,
            "explain": {"shap_top": top_features},
            "headlines": headlines,
        }
        events.append(event)

    return events


def build_ground_truth(events: list[dict[str, Any]]) -> dict[int, list[int]]:
    """
    Build ground truth for semantic similarity.

    For each event, identify which other events should be semantically similar.
    """
    ground_truth = {}

    for i, event in enumerate(events):
        similar_indices = []

        # Events are similar if they share regime OR ticker
        for j, other_event in enumerate(events):
            if i == j:
                continue

            # High similarity: same regime and ticker
            if (
                event["ticker"] == other_event["ticker"]
                and event["regime"] == other_event["regime"]
            ) or event["regime"] == other_event["regime"]:
                similar_indices.append(j)

        ground_truth[i] = similar_indices

    return ground_truth


def compute_recall_at_k(retrieved: list[int], relevant: list[int], k: int) -> float:
    """
    Compute Recall@K metric.

    Args:
        retrieved: List of retrieved indices (ordered by similarity)
        relevant: List of ground-truth relevant indices
        k: Number of top results to consider

    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant:
        return 0.0

    retrieved_at_k = set(retrieved[:k])
    relevant_set = set(relevant)

    hits = len(retrieved_at_k & relevant_set)
    return hits / len(relevant_set)


def evaluate_embeddings(
    events: list[dict[str, Any]],
    ground_truth: dict[int, list[int]],
    use_transformer: bool,
    k_values: list[int],
) -> dict[str, Any]:
    """
    Evaluate embedding quality using recall@k.

    Args:
        events: Test events
        ground_truth: Ground truth similar events
        use_transformer: Whether to use transformer or hash baseline
        k_values: List of k values to evaluate

    Returns:
        Dictionary with evaluation metrics
    """
    model_name = "transformer" if use_transformer else "hash_baseline"
    logger.info(f"Evaluating {model_name}...")

    # Build embeddings
    start_time = time.time()
    if use_transformer:
        embeddings = vecdb.build_embeddings_batch(events, use_transformer=True)
    else:
        embeddings = [vecdb.build_embedding(e, use_transformer=False) for e in events]
    encoding_time = time.time() - start_time

    logger.info(f"Built {len(embeddings)} embeddings in {encoding_time:.2f}s")

    # Compute similarities and recall@k
    recall_scores = {k: [] for k in k_values}
    similarity_scores = []
    query_times = []

    for i, query_embedding in enumerate(embeddings):
        relevant_indices = ground_truth.get(i, [])
        if not relevant_indices:
            continue

        # Compute similarity to all other embeddings
        start_time = time.time()
        similarities = []
        for j, target_embedding in enumerate(embeddings):
            if i == j:
                continue
            sim = vecdb._cosine_similarity(query_embedding, target_embedding)
            similarities.append((j, sim))
        query_time = time.time() - start_time
        query_times.append(query_time)

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        retrieved_indices = [idx for idx, _ in similarities]

        # Compute recall@k for different k values
        for k in k_values:
            recall = compute_recall_at_k(retrieved_indices, relevant_indices, k)
            recall_scores[k].append(recall)

        # Track top similarity score
        if similarities:
            similarity_scores.append(similarities[0][1])

    # Aggregate metrics
    metrics = {
        "model": model_name,
        "num_queries": len(recall_scores[k_values[0]]),
        "encoding_time_total": encoding_time,
        "encoding_time_per_event": encoding_time / len(events),
        "query_time_avg": sum(query_times) / len(query_times) if query_times else 0,
        "query_time_total": sum(query_times),
        "recall_at_k": {},
        "mean_similarity_score": (
            sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        ),
    }

    for k in k_values:
        scores = recall_scores[k]
        metrics["recall_at_k"][f"recall@{k}"] = sum(scores) / len(scores) if scores else 0

    return metrics


def main():
    """Run vector memory evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate vector memory semantic recall")
    parser.add_argument(
        "--test-size", type=int, default=50, help="Number of test events (default: 50)"
    )
    parser.add_argument(
        "--k-values",
        type=str,
        default="1,5,10",
        help="Comma-separated k values for recall@k (default: 1,5,10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval_results.json",
        help="Output file for results (default: eval_results.json)",
    )

    args = parser.parse_args()
    k_values = [int(k) for k in args.k_values.split(",")]

    logger.info("=" * 80)
    logger.info("Vector Memory Evaluation: Transformer vs Hash Baseline")
    logger.info("=" * 80)

    # Generate test data
    logger.info(f"Generating {args.test_size} test events...")
    events = generate_test_events(args.test_size)

    # Build ground truth
    logger.info("Building ground truth...")
    ground_truth = build_ground_truth(events)
    logger.info(
        f"Ground truth: {len(ground_truth)} queries with avg {sum(len(v) for v in ground_truth.values()) / len(ground_truth):.1f} relevant items"
    )

    # Evaluate transformer embeddings
    transformer_metrics = evaluate_embeddings(
        events, ground_truth, use_transformer=True, k_values=k_values
    )

    # Evaluate hash baseline
    baseline_metrics = evaluate_embeddings(
        events, ground_truth, use_transformer=False, k_values=k_values
    )

    # Compare results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)

    logger.info("\n--- Transformer Model ---")
    logger.info(f"Encoding time: {transformer_metrics['encoding_time_total']:.2f}s")
    logger.info(f"Query time (avg): {transformer_metrics['query_time_avg'] * 1000:.2f}ms")
    for k in k_values:
        recall_key = f"recall@{k}"
        logger.info(f"{recall_key}: {transformer_metrics['recall_at_k'][recall_key]:.4f}")
    logger.info(f"Mean similarity: {transformer_metrics['mean_similarity_score']:.4f}")

    logger.info("\n--- Hash Baseline ---")
    logger.info(f"Encoding time: {baseline_metrics['encoding_time_total']:.2f}s")
    logger.info(f"Query time (avg): {baseline_metrics['query_time_avg'] * 1000:.2f}ms")
    for k in k_values:
        recall_key = f"recall@{k}"
        logger.info(f"{recall_key}: {baseline_metrics['recall_at_k'][recall_key]:.4f}")
    logger.info(f"Mean similarity: {baseline_metrics['mean_similarity_score']:.4f}")

    logger.info("\n--- Improvement ---")
    for k in k_values:
        recall_key = f"recall@{k}"
        transformer_recall = transformer_metrics["recall_at_k"][recall_key]
        baseline_recall = baseline_metrics["recall_at_k"][recall_key]
        improvement = (
            ((transformer_recall - baseline_recall) / baseline_recall * 100)
            if baseline_recall > 0
            else 0
        )
        logger.info(f"{recall_key} improvement: {improvement:+.1f}%")

    # Save results
    results = {
        "test_size": args.test_size,
        "k_values": k_values,
        "transformer": transformer_metrics,
        "baseline": baseline_metrics,
    }

    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\nResults saved to: {output_path}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
