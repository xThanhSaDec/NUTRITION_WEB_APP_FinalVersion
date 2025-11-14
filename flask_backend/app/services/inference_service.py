from __future__ import annotations
import io
import json
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, Tuple, List

import numpy as np
from PIL import Image
import tensorflow as tf
try:
    import keras  # Prefer standalone Keras 3 for .keras models
    _HAS_KERAS = True
except Exception:
    keras = None  # type: ignore
    _HAS_KERAS = False

# Default locations for model and mapping
THIS_DIR = os.path.dirname(__file__)
# Try Flask backend ml_models first, then project root ml_models
CANDIDATE_MODEL_DIRS = [
    os.path.abspath(os.path.join(THIS_DIR, "..", "ml_models")),
    os.path.abspath(os.path.join(THIS_DIR, "..", "..", "..", "ml_models")),
]

MODEL_FILENAME = "best_model_phase2.keras"
CLASS_MAP_FILENAME = "final_class_mapping.json"


def _first_existing(*paths: str) -> Optional[str]:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


@dataclass
class _InferenceState:
    model: Optional[tf.keras.Model] = None
    class_map: Optional[Dict[int, str]] = None
    input_size: int = 224
    model_path: Optional[str] = None
    preprocess_source: Optional[str] = None

_state = _InferenceState()


def _load_class_map(path: str) -> Dict[int, str]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # keys may be strings of ints
    return {int(k): v for k, v in raw.items()}


def _ensure_loaded() -> None:
    if _state.model is not None and _state.class_map is not None:
        return
    # Resolve paths
    model_path = None
    class_map_path = None
    for base in CANDIDATE_MODEL_DIRS:
        model_path = _first_existing(os.path.join(base, MODEL_FILENAME)) or model_path
        class_map_path = _first_existing(os.path.join(base, CLASS_MAP_FILENAME)) or class_map_path
    if not model_path:
        raise FileNotFoundError("Model file not found: best_model_phase2.keras in ml_models")
    if not class_map_path:
        raise FileNotFoundError("Class mapping not found: final_class_mapping.json in ml_models")

    # Lazy-load model and mapping
    # Prefer Keras 3 loader for native .keras format if available
    last_err: Optional[Exception] = None

    # Build custom_objects to satisfy Lambda('preprocess_input') deserialization
    def _identity(x):
        return x
    def _get_preprocess_func() -> Callable:
        # Try common preprocess_input locations; fall back to identity
        mods = [
            "keras.applications.efficientnet_v2",
            "keras.applications.efficientnet",
            "keras.applications.mobilenet_v2",
            "keras.applications.resnet",
            "keras.applications.resnet50",
            "keras.applications.inception_v3",
            "keras.applications.xception",
            "keras.applications.densenet",
            "keras.applications.nasnet",
            "keras.applications.vgg16",
            "keras.applications.vgg19",
            # tf.keras fallbacks
            "tensorflow.keras.applications.efficientnet_v2",
            "tensorflow.keras.applications.efficientnet",
            "tensorflow.keras.applications.mobilenet_v2",
            "tensorflow.keras.applications.resnet",
            "tensorflow.keras.applications.resnet50",
            "tensorflow.keras.applications.inception_v3",
            "tensorflow.keras.applications.xception",
            "tensorflow.keras.applications.densenet",
            "tensorflow.keras.applications.nasnet",
            "tensorflow.keras.applications.vgg16",
            "tensorflow.keras.applications.vgg19",
        ]
        for m in mods:
            try:
                mod = __import__(m, fromlist=["preprocess_input"])  # type: ignore
                fn = getattr(mod, "preprocess_input", None)
                if callable(fn):
                    _state.preprocess_source = m
                    return fn  # type: ignore[return-value]
            except Exception:
                continue
        return _identity  # type: ignore[return-value]

    custom_objects = {"preprocess_input": _get_preprocess_func()}
    if _HAS_KERAS:
        # Try safest: do not compile; allow deserialization of built-ins
        for kwargs in (
            {"compile": False, "safe_mode": False, "custom_objects": custom_objects},
            {"compile": False, "custom_objects": custom_objects},
            {"custom_objects": custom_objects},
        ):
            try:
                _state.model = keras.saving.load_model(model_path, **kwargs)  # type: ignore[attr-defined]
                last_err = None
                break
            except Exception as e:
                last_err = e
        if _state.model is None:
            # Fallback legacy API
            try:
                _state.model = keras.models.load_model(model_path, compile=False, custom_objects=custom_objects)  # type: ignore
                last_err = None
            except Exception as e:
                last_err = e
    if _state.model is None:
        # Fallback to tf.keras if standalone Keras isn't installed or failed
        try:
            _state.model = tf.keras.models.load_model(model_path, compile=False, custom_objects=custom_objects)
            last_err = None
        except Exception as e:
            last_err = e
    if _state.model is None and last_err is not None:
        # Surface a clear error up the stack
        raise last_err
    _state.model_path = model_path
    _state.class_map = _load_class_map(class_map_path)


def _preprocess(img_bytes: bytes, size: int, normalize01: bool = False) -> np.ndarray:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((size, size))
    arr = np.asarray(img, dtype=np.float32)
    if normalize01:
        arr = arr / 255.0
    arr = np.expand_dims(arr, axis=0)
    return arr


class InferenceService:
    def __init__(self) -> None:
        _ensure_loaded()
        self.model = _state.model  # type: ignore
        self.class_map = _state.class_map  # type: ignore
        self.input_size = _state.input_size
        # If the model graph contains a preprocess_input Lambda, feed raw pixels by default
        # Allow override via env var INPUT_SCALE_01=true to divide by 255
        self.scale01 = os.getenv("INPUT_SCALE_01", "false").lower() == "true"
        self.model_path = _state.model_path

    def predict(self, img_bytes: bytes) -> Dict[str, Any]:
        try:
            x = _preprocess(img_bytes, self.input_size, normalize01=self.scale01)
            preds = self.model.predict(x, verbose=0)
            if isinstance(preds, list):
                preds = preds[0]
            preds = np.array(preds).reshape(-1)
            idx = int(np.argmax(preds))
            conf = float(np.max(preds))
            class_name = self.class_map.get(idx, str(idx))
            # Pretty food name
            food_name = class_name.replace("_", " ").title()
            # Top-5 for debugging
            top5_idx = np.argsort(preds)[-5:][::-1]
            top5 = []
            for i in top5_idx:
                name = self.class_map.get(int(i), str(int(i)))
                top5.append({"class_name": name, "confidence": float(preds[int(i)])})
            return {
                "success": True,
                "class_name": class_name,
                "food_name": food_name,
                "confidence": conf,
                "top5": top5,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


_singleton: Optional[InferenceService] = None

def get_inference_service() -> InferenceService:
    global _singleton
    if _singleton is None:
        _singleton = InferenceService()
    return _singleton
