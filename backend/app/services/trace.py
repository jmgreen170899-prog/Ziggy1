"""
ZiggyAI Trace Service - Decision DAG Construction

Builds decision graphs showing the flow from inputs through transforms,
fusion, calibration, risk management, to final position sizing.

Brain-first: All trace data is designed for storage/retrieval from memory.
"""

import logging
import uuid
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


def build_trace(
    inputs: dict[str, Any],
    features: dict[str, Any],
    fusion: dict[str, Any],
    calibration: dict[str, Any],
    risk: dict[str, Any],
    sizing: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a complete decision trace DAG.

    Creates a directed acyclic graph showing the decision pipeline
    from market inputs to final position sizing.

    Args:
        inputs: Market data inputs
        features: Extracted features
        fusion: Signal fusion results
        calibration: Calibration adjustments
        risk: Risk management decisions
        sizing: Position sizing results

    Returns:
        Complete trace with graph structure and raw data
    """

    # Build node list with processing metadata
    nodes = []
    edges = []

    # Input node
    nodes.append(
        {
            "id": "inputs",
            "type": "source",
            "name": "Market Inputs",
            "description": "Raw market data and external signals",
            "data_size": len(str(inputs)),
            "timestamp": inputs.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        }
    )

    # Feature extraction node
    feature_latency = _estimate_processing_time("features", len(features))
    nodes.append(
        {
            "id": "features",
            "type": "transform",
            "name": "Feature Extraction",
            "description": "Technical indicators and derived features",
            "latency_ms": feature_latency,
            "feature_count": len(features),
            "top_feature": _get_top_feature(features),
        }
    )

    # Signal fusion node
    fusion_latency = _estimate_processing_time("fusion", fusion.get("confidence", 0.5))
    nodes.append(
        {
            "id": "fusion",
            "type": "model",
            "name": "Signal Fusion",
            "description": "ML model prediction and confidence",
            "latency_ms": fusion_latency,
            "prediction": fusion.get("p_up_raw", 0.5),
            "confidence": fusion.get("confidence", 0.5),
            "regime": fusion.get("regime", "unknown"),
        }
    )

    # Calibration node
    calib_latency = _estimate_processing_time("calibration", 1.0)
    nodes.append(
        {
            "id": "calibration",
            "type": "transform",
            "name": "Calibration",
            "description": "Probability calibration adjustment",
            "latency_ms": calib_latency,
            "pre_calib": fusion.get("p_up_raw", 0.5),
            "post_calib": calibration.get("p_up_calibrated", 0.5),
            "ece": calibration.get("ece", 0.0),
        }
    )

    # Risk management node
    risk_latency = _estimate_processing_time("risk", risk.get("risk_score", 0.5))
    nodes.append(
        {
            "id": "risk",
            "type": "filter",
            "name": "Risk Management",
            "description": "Position limits and risk controls",
            "latency_ms": risk_latency,
            "max_position": risk.get("max_position_size", 0.05),
            "stop_loss": risk.get("stop_loss", 0.02),
            "risk_score": risk.get("risk_score", 0.5),
        }
    )

    # Position sizing node
    sizing_latency = _estimate_processing_time("sizing", 1.0)
    nodes.append(
        {
            "id": "sizing",
            "type": "output",
            "name": "Position Sizing",
            "description": "Final position size and allocation",
            "latency_ms": sizing_latency,
            "position_size": sizing.get("position_size", 0.0),
            "dollar_amount": sizing.get("dollar_amount", 0.0),
            "shares": sizing.get("shares", 0),
        }
    )

    # Build edge list (pipeline flow)
    pipeline_edges = [
        ("inputs", "features", "market_data"),
        ("features", "fusion", "feature_vector"),
        ("fusion", "calibration", "raw_prediction"),
        ("calibration", "risk", "calibrated_prediction"),
        ("risk", "sizing", "risk_adjusted_signal"),
    ]

    for source, target, label in pipeline_edges:
        # Estimate data flow size
        data_flow_kb = _estimate_data_flow(source, target)

        edges.append(
            {
                "source": source,
                "target": target,
                "label": label,
                "data_flow_kb": data_flow_kb,
                "type": "pipeline",
            }
        )

    # Add feedback edges (for visualization)
    feedback_edges = [
        ("risk", "fusion", "risk_feedback"),
        ("calibration", "features", "calib_feedback"),
    ]

    for source, target, label in feedback_edges:
        edges.append(
            {
                "source": source,
                "target": target,
                "label": label,
                "type": "feedback",
                "strength": 0.3,  # Weaker feedback connections
            }
        )

    # Calculate total processing time
    total_latency = sum(node.get("latency_ms", 0) for node in nodes)

    return {
        "graph": {
            "nodes": nodes,
            "edges": edges,
            "layout": "pipeline",  # Hint for frontend layout
            "total_latency_ms": total_latency,
        },
        "raw": {
            "inputs": inputs,
            "features": features,
            "fusion": fusion,
            "calibration": calibration,
            "risk": risk,
            "sizing": sizing,
        },
        "metadata": {
            "trace_id": str(uuid.uuid4()),
            "pipeline_type": "signal_generation",
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
    }


def _estimate_processing_time(stage: str, complexity: float) -> float:
    """
    Estimate processing time for a pipeline stage.

    Args:
        stage: Pipeline stage name
        complexity: Complexity factor (0-1)

    Returns:
        Estimated latency in milliseconds
    """
    # Base latencies for different stages (in ms)
    base_latencies = {
        "features": 15.0,
        "fusion": 25.0,
        "calibration": 5.0,
        "risk": 8.0,
        "sizing": 3.0,
    }

    base = base_latencies.get(stage, 10.0)

    # Add complexity factor (±50% variation)
    complexity_factor = 0.5 + complexity * 0.5

    # Add some jitter for realism
    import random

    jitter = random.uniform(0.8, 1.2)

    return round(base * complexity_factor * jitter, 1)


def _estimate_data_flow(source: str, target: str) -> float:
    """
    Estimate data flow between pipeline stages.

    Args:
        source: Source stage
        target: Target stage

    Returns:
        Estimated data size in KB
    """
    # Typical data flow sizes
    flow_sizes = {
        ("inputs", "features"): 2.5,
        ("features", "fusion"): 1.2,
        ("fusion", "calibration"): 0.3,
        ("calibration", "risk"): 0.5,
        ("risk", "sizing"): 0.8,
        ("risk", "fusion"): 0.1,  # Feedback
        ("calibration", "features"): 0.2,  # Feedback
    }

    return flow_sizes.get((source, target), 0.5)


def _get_top_feature(features: dict[str, Any]) -> str | None:
    """Get the top contributing feature name."""
    if not features:
        return None

    # Find feature with highest absolute value
    top_feature = None
    max_contrib = 0.0

    for feature_name, contrib in features.items():
        if isinstance(contrib, (int, float)) and abs(contrib) > max_contrib:
            max_contrib = abs(contrib)
            top_feature = feature_name

    return top_feature


def build_trace_summary(trace_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build a summary of trace data for quick display.

    Args:
        trace_data: Complete trace data

    Returns:
        Condensed trace summary
    """
    graph = trace_data.get("graph", {})
    nodes = graph.get("nodes", [])

    # Extract key metrics
    total_latency = graph.get("total_latency_ms", 0.0)

    # Find bottleneck stage
    bottleneck = None
    max_latency = 0.0
    for node in nodes:
        node_latency = node.get("latency_ms", 0.0)
        if node_latency > max_latency:
            max_latency = node_latency
            bottleneck = node.get("name", "unknown")

    # Count pipeline stages
    stage_types = {}
    for node in nodes:
        node_type = node.get("type", "unknown")
        stage_types[node_type] = stage_types.get(node_type, 0) + 1

    # Extract final prediction flow
    prediction_flow = {}
    for node in nodes:
        if node.get("id") == "fusion":
            prediction_flow["raw_prediction"] = node.get("prediction", 0.5)
        elif node.get("id") == "calibration":
            prediction_flow["calibrated"] = node.get("post_calib", 0.5)
        elif node.get("id") == "sizing":
            prediction_flow["final_size"] = node.get("position_size", 0.0)

    return {
        "total_latency_ms": total_latency,
        "bottleneck_stage": bottleneck,
        "bottleneck_latency_ms": max_latency,
        "stage_count": len(nodes),
        "stage_types": stage_types,
        "prediction_flow": prediction_flow,
        "has_feedback": any(edge.get("type") == "feedback" for edge in graph.get("edges", [])),
        "pipeline_efficiency": round(
            (total_latency - max_latency) / total_latency if total_latency > 0 else 0.0, 2
        ),
    }


def validate_trace_integrity(trace_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate trace data integrity and completeness.

    Args:
        trace_data: Complete trace data

    Returns:
        Validation results
    """
    issues = []

    # Check graph structure
    graph = trace_data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if len(nodes) == 0:
        issues.append("no_nodes")

    if len(edges) == 0:
        issues.append("no_edges")

    # Check for required pipeline stages
    required_stages = {"inputs", "features", "fusion", "calibration", "risk", "sizing"}
    found_stages = {node.get("id") for node in nodes}
    missing_stages = required_stages - found_stages

    if missing_stages:
        issues.append(f"missing_stages: {missing_stages}")

    # Check edge connectivity
    node_ids = {node.get("id") for node in nodes}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_ids:
            issues.append(f"invalid_edge_source: {source}")
        if target not in node_ids:
            issues.append(f"invalid_edge_target: {target}")

    # Check raw data completeness
    raw = trace_data.get("raw", {})
    required_raw = {"inputs", "features", "fusion", "calibration", "risk", "sizing"}
    missing_raw = required_raw - set(raw.keys())

    if missing_raw:
        issues.append(f"missing_raw_data: {missing_raw}")

    # Calculate integrity score
    total_checks = 4  # Graph, stages, edges, raw data
    failed_checks = len([issue for issue in issues if not issue.startswith("missing_stages")])
    integrity_score = max(0.0, (total_checks - failed_checks) / total_checks)

    return {
        "is_valid": len(issues) == 0,
        "integrity_score": round(integrity_score, 2),
        "issues": issues,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "validation_timestamp": datetime.utcnow().isoformat() + "Z",
    }
