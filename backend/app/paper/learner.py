# ruff: noqa: N803
"""
Online learning module for ZiggyAI paper trading lab.

This module provides incremental learning capabilities with support for
sklearn-style partial_fit and PyTorch mini-batch training.
"""

from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportAttributeAccessFromUnknown=false, reportGeneralTypeIssues=false
import importlib.util as importlib_util
import io
import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.core.logging import get_logger


logger = get_logger("ziggy.learner")

try:
    from sklearn.linear_model import SGDClassifier, SGDRegressor
    from sklearn.metrics import accuracy_score, mean_squared_error
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Define stubs to satisfy static analysis; they won't be used at runtime when unavailable
    SGDClassifier = None  # type: ignore[assignment]
    SGDRegressor = None  # type: ignore[assignment]
    accuracy_score = None  # type: ignore[assignment]
    mean_squared_error = None  # type: ignore[assignment]
    StandardScaler = None  # type: ignore[assignment]
    logger.warning("scikit-learn not available, using simple fallback learner")

TORCH_AVAILABLE = bool(importlib_util.find_spec("torch"))
if not TORCH_AVAILABLE:
    logger.info("PyTorch not available, using sklearn/fallback only")


@dataclass
class TrainingBatch:
    """Training batch for online learning."""

    features: np.ndarray
    labels: np.ndarray
    sample_weights: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """Result of model prediction."""

    predictions: np.ndarray
    probabilities: np.ndarray | None = None
    confidence: np.ndarray | None = None
    explanations: dict[str, Any] | None = None


class SimpleFallbackLearner:
    """Simple fallback learner when sklearn/torch not available."""

    def __init__(self, task_type: str = "classification"):
        self.task_type = task_type
        self.feature_means: np.ndarray | None = None
        self.feature_stds: np.ndarray | None = None
        self.weights: np.ndarray | None = None
        self.bias: float = 0.0
        self.learning_rate = 0.01
        self.n_samples = 0

    def partial_fit(
        self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None
    ) -> None:
        """Partial fit with simple gradient descent."""
        if X.size == 0 or y.size == 0:
            return

        # Initialize on first fit
        if self.weights is None:
            self.weights = np.random.normal(0, 0.01, X.shape[1])
            self.feature_means = np.zeros(X.shape[1])
            self.feature_stds = np.ones(X.shape[1])

        # Update feature statistics
        batch_size = X.shape[0]

        # Update running mean and std
        if self.n_samples > 0:
            assert self.feature_means is not None and self.feature_stds is not None
            # Welford's online algorithm
            for i in range(X.shape[1]):
                for j in range(batch_size):
                    self.n_samples += 1
                    delta = X[j, i] - self.feature_means[i]
                    self.feature_means[i] += delta / self.n_samples
                    delta2 = X[j, i] - self.feature_means[i]
                    self.feature_stds[i] += delta * delta2
        else:
            self.feature_means = np.mean(X, axis=0)
            self.feature_stds = np.std(X, axis=0) + 1e-8
            self.n_samples = batch_size

        # Ensure feature stats exist for normalization (type safety)
        if self.feature_means is None or self.feature_stds is None:
            self.feature_means = np.mean(X, axis=0)
            self.feature_stds = np.std(X, axis=0) + 1e-8
        fm = self.feature_means
        fs = self.feature_stds
        # Normalize features
        X_norm = (X - fm) / (fs + 1e-8)

        # Simple gradient descent update
        for i in range(batch_size):
            x_i = X_norm[i]
            y_i = y[i]
            weight = sample_weight[i] if sample_weight is not None else 1.0

            # Forward pass
            prediction = np.dot(x_i, self.weights) + self.bias

            # Loss and gradient
            if self.task_type == "classification":
                # Logistic regression
                sigmoid_pred = 1 / (1 + np.exp(-prediction))
                error = sigmoid_pred - y_i
            else:
                # Linear regression
                error = prediction - y_i

            # Update weights
            self.weights -= self.learning_rate * weight * error * x_i
            self.bias -= self.learning_rate * weight * error

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if self.weights is None:
            return np.zeros(X.shape[0])

        # Normalize features with safe defaults if stats missing
        if self.feature_means is None or self.feature_stds is None:
            fm_arr = np.zeros(X.shape[1])
            fs_arr = np.ones(X.shape[1])
        else:
            fm_arr = np.asarray(self.feature_means)
            fs_arr = np.asarray(self.feature_stds)
        X_norm = (X - fm_arr) / (fs_arr + 1e-8)

        predictions = np.dot(X_norm, self.weights) + self.bias

        if self.task_type == "classification":
            return (predictions > 0).astype(int)
        else:
            return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities (classification only)."""
        if self.task_type != "classification" or self.weights is None:
            return np.zeros((X.shape[0], 2))

        # Normalize features with safe defaults if stats missing
        if self.feature_means is None or self.feature_stds is None:
            fm_arr = np.zeros(X.shape[1])
            fs_arr = np.ones(X.shape[1])
        else:
            fm_arr = np.asarray(self.feature_means)
            fs_arr = np.asarray(self.feature_stds)
        X_norm = (X - fm_arr) / (fs_arr + 1e-8)

        logits = np.dot(X_norm, self.weights) + self.bias
        probabilities = 1 / (1 + np.exp(-logits))

        # Return as [prob_class_0, prob_class_1]
        prob_array = np.column_stack([1 - probabilities, probabilities])
        return prob_array


class OnlineLearner:
    """
    Online learner with multiple backend support.

    Supports:
    - sklearn SGD models with partial_fit
    - PyTorch neural networks with mini-batch training
    - Simple fallback implementation
    """

    def __init__(
        self,
        task_type: str = "classification",  # "classification" or "regression"
        backend: str = "auto",  # "sklearn", "torch", "simple", or "auto"
        model_params: dict[str, Any] | None = None,
        feature_dim: int | None = None,
        buffer_size: int = 1000,
        torch_hidden_dims: list[int] | None = None,
    ):
        self.task_type = task_type
        self.backend = self._select_backend(backend)
        self.model_params = model_params or {}
        self.feature_dim = feature_dim
        self.buffer_size = buffer_size
        self.torch_hidden_dims = torch_hidden_dims or [64, 32]

        # Initialize model
        self.model = self._create_model()
        self.scaler = (
            StandardScaler() if (self.backend == "sklearn" and SKLEARN_AVAILABLE) else None
        )
        self.is_fitted = False

        # Training buffer for experience replay
        self.training_buffer: list[TrainingBatch] = []

        # Metrics tracking
        self.training_metrics: dict[str, list[float]] = {"loss": []}
        if task_type == "classification":
            self.training_metrics["accuracy"] = []
        else:
            self.training_metrics["mse"] = []

        logger.info(
            "OnlineLearner initialized",
            extra={"task_type": task_type, "backend": self.backend, "feature_dim": feature_dim},
        )

    def _select_backend(self, backend: str) -> str:
        """Select appropriate backend."""
        if backend == "auto":
            if SKLEARN_AVAILABLE:
                return "sklearn"
            elif TORCH_AVAILABLE:
                return "torch"
            else:
                return "simple"
        elif backend == "sklearn" and not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available, falling back to simple")
            return "simple"
        elif backend == "torch" and not TORCH_AVAILABLE:
            logger.warning("torch not available, falling back to sklearn or simple")
            return "sklearn" if SKLEARN_AVAILABLE else "simple"
        else:
            return backend

    def _create_model(self):
        """Create model based on backend."""
        if self.backend == "sklearn":
            if not SKLEARN_AVAILABLE:
                raise ImportError("scikit-learn not available")
            if self.task_type == "classification":
                return SGDClassifier(
                    loss="log",  # Logistic regression
                    learning_rate="adaptive",
                    eta0=0.01,
                    random_state=42,
                    **self.model_params,
                )
            else:
                return SGDRegressor(
                    loss="squared_loss",
                    learning_rate="adaptive",
                    eta0=0.01,
                    random_state=42,
                    **self.model_params,
                )

        elif self.backend == "torch":
            return self._create_torch_model()

        else:  # simple
            return SimpleFallbackLearner(self.task_type)

    def _create_torch_model(self):
        """Create PyTorch model."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")

        if self.feature_dim is None:
            raise ValueError("feature_dim required for PyTorch backend")

        layers = []
        input_dim = self.feature_dim

        # Hidden layers
        for hidden_dim in self.torch_hidden_dims:
            try:
                import torch.nn as _nn  # type: ignore
            except Exception as e:
                raise ImportError("PyTorch not available") from e
            layers.extend([_nn.Linear(input_dim, hidden_dim), _nn.ReLU(), _nn.Dropout(0.2)])
            input_dim = hidden_dim

        # Output layer
        if self.task_type == "classification":
            output_dim = 1  # Binary classification
            try:
                import torch.nn as _nn  # type: ignore
            except Exception as e:
                raise ImportError("PyTorch not available") from e
            layers.append(_nn.Linear(input_dim, output_dim))
            layers.append(_nn.Sigmoid())
        else:
            output_dim = 1  # Regression
            try:
                import torch.nn as _nn  # type: ignore
            except Exception as e:
                raise ImportError("PyTorch not available") from e
            layers.append(_nn.Linear(input_dim, output_dim))
        try:
            import torch.nn as _nn  # type: ignore
        except Exception as e:
            raise ImportError("PyTorch not available") from e
        model = _nn.Sequential(*layers)
        return model

    def partial_fit(
        self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None
    ) -> dict[str, float]:
        """
        Partial fit on new data.

        Args:
            X: Feature matrix
            y: Target values
            sample_weight: Sample weights

        Returns:
            Training metrics
        """
        if X.size == 0 or y.size == 0:
            return {}

        # Add to training buffer
        batch = TrainingBatch(
            features=X.copy(),
            labels=y.copy(),
            sample_weights=sample_weight.copy() if sample_weight is not None else None,
        )
        self.training_buffer.append(batch)

        # Keep buffer size manageable
        if len(self.training_buffer) > self.buffer_size:
            self.training_buffer.pop(0)

        # Train model
        if self.backend == "sklearn":
            return self._sklearn_partial_fit(X, y, sample_weight)
        elif self.backend == "torch":
            return self._torch_partial_fit(X, y, sample_weight)
        else:  # simple
            return self._simple_partial_fit(X, y, sample_weight)

    def _sklearn_partial_fit(
        self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None
    ) -> dict[str, float]:
        """Sklearn partial fit."""
        # Scale features
        if not self.is_fitted:
            assert self.scaler is not None
            X_scaled = self.scaler.fit_transform(X)
            self.is_fitted = True
        else:
            assert self.scaler is not None
            X_scaled = self.scaler.transform(X)

        # Partial fit
        if self.task_type == "classification":
            classes = np.array([0, 1])  # Binary classification
            model_any: Any = self.model
            model_any.partial_fit(X_scaled, y, classes=classes, sample_weight=sample_weight)
        else:
            model_any: Any = self.model
            model_any.partial_fit(X_scaled, y, sample_weight=sample_weight)

        # Calculate metrics
        model_any: Any = self.model
        predictions = model_any.predict(X_scaled)

        if self.task_type == "classification":
            assert accuracy_score is not None
            accuracy = float(accuracy_score(y, predictions, sample_weight=sample_weight))
            self.training_metrics["accuracy"].append(accuracy)
            return {"accuracy": accuracy}
        else:
            assert mean_squared_error is not None
            mse = float(mean_squared_error(y, predictions, sample_weight=sample_weight))
            self.training_metrics["mse"].append(mse)
            return {"mse": mse}

    def _torch_partial_fit(
        self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None
    ) -> dict[str, float]:
        """PyTorch partial fit."""
        if not TORCH_AVAILABLE:
            return {}
        try:
            import torch as _torch  # type: ignore
            import torch.nn as _nn  # type: ignore
            import torch.optim as _optim  # type: ignore
        except Exception:
            return {}

        # Convert to tensors
        X_tensor = _torch.FloatTensor(X)
        y_tensor = _torch.FloatTensor(y.reshape(-1, 1))

        if sample_weight is not None:
            weight_tensor = _torch.FloatTensor(sample_weight)
        else:
            weight_tensor = _torch.ones(X.shape[0])

        # Setup optimizer
        if not hasattr(self, "optimizer"):
            tmodel: Any = self.model
            self.optimizer = _optim.Adam(tmodel.parameters(), lr=0.001)

        # Training step
        tmodel = self.model  # type: ignore[assignment]
        tmodel.train()  # type: ignore[attr-defined]
        self.optimizer.zero_grad()

        predictions = tmodel(X_tensor)  # type: ignore[operator]

        if self.task_type == "classification":
            loss_fn = _nn.BCELoss(reduction="none")
            loss = loss_fn(predictions, y_tensor)
            weighted_loss = (loss * weight_tensor.unsqueeze(1)).mean()
        else:
            loss_fn = _nn.MSELoss(reduction="none")
            loss = loss_fn(predictions, y_tensor)
            weighted_loss = (loss * weight_tensor.unsqueeze(1)).mean()

        weighted_loss.backward()
        self.optimizer.step()

        # Calculate metrics
        tmodel.eval()  # type: ignore[attr-defined]
        with _torch.no_grad():
            if self.task_type == "classification":
                pred_classes = (predictions > 0.5).float()
                accuracy = float((pred_classes == y_tensor).float().mean().item())
                self.training_metrics["accuracy"].append(accuracy)
                return {"accuracy": accuracy, "loss": float(weighted_loss.item())}
            else:
                mse = float(loss.mean().item())
                self.training_metrics["mse"].append(mse)
                return {"mse": mse, "loss": float(weighted_loss.item())}

    def _simple_partial_fit(
        self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None
    ) -> dict[str, float]:
        """Simple fallback partial fit."""
        self.model.partial_fit(X, y, sample_weight)
        self.is_fitted = True

        # Calculate basic metrics
        predictions = self.model.predict(X)

        if self.task_type == "classification":
            accuracy = np.mean(predictions == y)
            return {"accuracy": accuracy}
        else:
            mse = np.mean((predictions - y) ** 2)
            return {"mse": mse}

    def predict(self, X: np.ndarray) -> PredictionResult:
        """
        Make predictions.

        Args:
            X: Feature matrix

        Returns:
            PredictionResult with predictions and optional probabilities
        """
        if not self.is_fitted:
            # Return default predictions
            default_pred = np.zeros(X.shape[0])
            return PredictionResult(predictions=default_pred)

        if self.backend == "sklearn":
            return self._sklearn_predict(X)
        elif self.backend == "torch":
            return self._torch_predict(X)
        else:  # simple
            return self._simple_predict(X)

    def _sklearn_predict(self, X: np.ndarray) -> PredictionResult:
        """Sklearn prediction."""
        assert self.scaler is not None
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)

        probabilities = None
        confidence = None

        if self.task_type == "classification" and hasattr(self.model, "predict_proba"):
            model_any = self.model
            probabilities = model_any.predict_proba(X_scaled)
            confidence = np.max(probabilities, axis=1)

        return PredictionResult(
            predictions=predictions, probabilities=probabilities, confidence=confidence
        )

    def _torch_predict(self, X: np.ndarray) -> PredictionResult:
        """PyTorch prediction."""
        if not TORCH_AVAILABLE:
            return PredictionResult(predictions=np.zeros(X.shape[0]))
        try:
            import torch as _torch  # type: ignore
        except Exception:
            return PredictionResult(predictions=np.zeros(X.shape[0]))

        X_tensor = _torch.FloatTensor(X)

        tmodel: Any = self.model
        tmodel.eval()  # type: ignore[attr-defined]
        with _torch.no_grad():
            outputs = self.model(X_tensor)

            if self.task_type == "classification":
                probabilities = outputs.numpy()
                predictions = (probabilities > 0.5).astype(int).flatten()
                confidence = np.maximum(probabilities, 1 - probabilities).flatten()
                # Convert to two-class format
                prob_array = np.column_stack([1 - probabilities.flatten(), probabilities.flatten()])
            else:
                predictions = outputs.numpy().flatten()
                probabilities = None
                confidence = None
                prob_array = None

        return PredictionResult(
            predictions=predictions, probabilities=prob_array, confidence=confidence
        )

    def _simple_predict(self, X: np.ndarray) -> PredictionResult:
        """Simple fallback prediction."""
        predictions = self.model.predict(X)

        probabilities = None
        confidence = None

        if self.task_type == "classification":
            probabilities = self.model.predict_proba(X)
            confidence = np.max(probabilities, axis=1)

        return PredictionResult(
            predictions=predictions, probabilities=probabilities, confidence=confidence
        )

    def explain(self, x: np.ndarray) -> dict[str, Any]:
        """
        Generate explanations for a single prediction.

        Args:
            x: Single feature vector

        Returns:
            Dictionary with explanation information
        """
        if not self.is_fitted:
            return {"error": "Model not fitted"}

        explanation = {"method": "feature_importance"}

        if self.backend == "sklearn":
            # Use model coefficients as feature importance
            if hasattr(self.model, "coef_"):
                feature_importance = self.model.coef_.flatten()
                explanation["feature_importance"] = feature_importance.tolist()
                explanation["input_values"] = x.tolist()

                # Calculate contribution of each feature
                if self.scaler is not None:
                    x_scaled = self.scaler.transform(x.reshape(1, -1)).flatten()
                    feature_contributions = feature_importance * x_scaled
                    explanation["feature_contributions"] = feature_contributions.tolist()

        elif self.backend == "simple":
            # Use model weights
            if self.model.weights is not None:
                explanation["feature_importance"] = self.model.weights.tolist()
                explanation["input_values"] = x.tolist()

        else:
            explanation["error"] = "Explanations not implemented for torch backend"

        return explanation

    def save_model(self, filepath: str | Path) -> None:
        """Save model to disk."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "task_type": self.task_type,
            "backend": self.backend,
            "model_params": self.model_params,
            "feature_dim": self.feature_dim,
            "is_fitted": self.is_fitted,
            "training_metrics": self.training_metrics,
        }

        if self.backend == "sklearn":
            model_data["model"] = pickle.dumps(self.model)
            model_data["scaler"] = pickle.dumps(self.scaler)
        elif self.backend == "torch" and TORCH_AVAILABLE:
            try:
                import torch as _torch  # type: ignore

                _torch.save(self.model.state_dict(), filepath.with_suffix(".pt"))
            except Exception:
                pass
            model_data["torch_model_path"] = str(filepath.with_suffix(".pt"))
        else:  # simple
            model_data["simple_model"] = {
                "weights": self.model.weights.tolist() if self.model.weights is not None else None,
                "bias": self.model.bias,
                "feature_means": (
                    self.model.feature_means.tolist()
                    if self.model.feature_means is not None
                    else None
                ),
                "feature_stds": (
                    self.model.feature_stds.tolist()
                    if self.model.feature_stds is not None
                    else None
                ),
                "n_samples": self.model.n_samples,
            }

        with open(filepath.with_suffix(".json"), "w") as f:
            json.dump(model_data, f, indent=2)

        logger.info("Model saved", extra={"filepath": str(filepath)})

    def load_model(self, filepath: str | Path) -> None:
        """Load model from disk."""
        filepath = Path(filepath)

        with open(filepath.with_suffix(".json")) as f:
            model_data = json.load(f)

        self.task_type = model_data["task_type"]
        self.backend = model_data["backend"]
        self.model_params = model_data["model_params"]
        self.feature_dim = model_data["feature_dim"]
        self.is_fitted = model_data["is_fitted"]
        self.training_metrics = model_data["training_metrics"]

        if self.backend == "sklearn":
            self.model = pickle.loads(model_data["model"])
            self.scaler = pickle.loads(model_data["scaler"])
        elif self.backend == "torch" and TORCH_AVAILABLE:
            self.model = self._create_torch_model()
            try:
                import torch as _torch  # type: ignore

                self.model.load_state_dict(_torch.load(model_data["torch_model_path"]))
            except Exception:
                pass
        else:  # simple
            self.model = SimpleFallbackLearner(self.task_type)
            simple_data = model_data["simple_model"]
            self.model.weights = (
                np.array(simple_data["weights"]) if simple_data["weights"] else None
            )
            self.model.bias = simple_data["bias"]
            self.model.feature_means = (
                np.array(simple_data["feature_means"]) if simple_data["feature_means"] else None
            )
            self.model.feature_stds = (
                np.array(simple_data["feature_stds"]) if simple_data["feature_stds"] else None
            )
            self.model.n_samples = simple_data["n_samples"]

        logger.info("Model loaded", extra={"filepath": str(filepath)})

    # --- Durability API ---
    def get_state(self) -> dict[str, Any]:
        """Return model bytes and meta suitable for checkpointing."""
        meta: dict[str, Any] = {
            "task_type": self.task_type,
            "backend": self.backend,
            "model_params": self.model_params,
            "feature_dim": self.feature_dim,
            "is_fitted": self.is_fitted,
        }
        try:
            if self.backend == "sklearn":
                import pickle

                model_bytes = pickle.dumps(
                    {
                        "model": self.model,
                        "scaler": self.scaler,
                        "meta": meta,
                    }
                )
                return {"algo": "sklearn", "bytes": model_bytes, "meta": meta}
            elif self.backend == "torch" and TORCH_AVAILABLE:
                try:
                    import torch as _torch  # type: ignore
                except Exception:
                    return {"algo": "torch", "bytes": b"", "meta": meta}

                buf = io.BytesIO()
                tmodel: Any = self.model
                _torch.save(tmodel.state_dict(), buf)
                return {"algo": "torch", "bytes": buf.getvalue(), "meta": meta}
            else:
                import pickle

                model_bytes = pickle.dumps(
                    {
                        "simple": {
                            "weights": getattr(self.model, "weights", None),
                            "bias": getattr(self.model, "bias", 0.0),
                            "feature_means": getattr(self.model, "feature_means", None),
                            "feature_stds": getattr(self.model, "feature_stds", None),
                            "n_samples": getattr(self.model, "n_samples", 0),
                        },
                        "meta": meta,
                    }
                )
                return {"algo": "simple", "bytes": model_bytes, "meta": meta}
        except Exception as e:
            logger.warning("Learner get_state failed", extra={"error": str(e)})
            return {"algo": self.backend, "bytes": b"", "meta": meta}

    def set_state(self, model_bytes: bytes, meta: dict[str, Any] | None = None) -> None:
        """Restore learner from bytes and meta."""
        meta = meta or {}
        try:
            if not model_bytes:
                return
            if meta.get("backend") == "sklearn" or self.backend == "sklearn":
                import pickle

                data = pickle.loads(model_bytes)
                self.model = data.get("model", self.model)
                self.scaler = data.get("scaler", self.scaler)
                self.is_fitted = bool(meta.get("is_fitted", True))
            elif meta.get("backend") == "torch" or self.backend == "torch":
                if not TORCH_AVAILABLE:
                    return
                import torch

                buf = io.BytesIO(model_bytes)
                state_dict = torch.load(buf)
                self.model = self._create_torch_model()
                self.model.load_state_dict(state_dict)
                self.is_fitted = bool(meta.get("is_fitted", True))
            else:
                import pickle

                data = pickle.loads(model_bytes)
                simple = data.get("simple", {})
                self.model = SimpleFallbackLearner(self.task_type)
                w = simple.get("weights")
                if w is not None:
                    import numpy as np

                    self.model.weights = np.array(w)
                self.model.bias = simple.get("bias", 0.0)
                fm = simple.get("feature_means")
                fs = simple.get("feature_stds")
                if fm is not None:
                    import numpy as np

                    self.model.feature_means = np.array(fm)
                if fs is not None:
                    import numpy as np

                    self.model.feature_stds = np.array(fs)
                self.model.n_samples = simple.get("n_samples", 0)
                self.is_fitted = bool(meta.get("is_fitted", True))
        except Exception as e:
            logger.warning("Learner set_state failed", extra={"error": str(e)})
