from __future__ import annotations
import io
import os
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image

# Import PyTorch
try:
    import torch
    import torch.nn as nn
    import torchvision
    import torchvision.transforms as transforms
    from torchvision.transforms import InterpolationMode
    _HAS_TORCH = True
except Exception as _e:
    torch = None
    _HAS_TORCH = False
    print(f"[inference] PyTorch import failed: {_e}")
    raise RuntimeError("PyTorch is required but not installed")

# Default locations for models
THIS_DIR = os.path.dirname(__file__)
CANDIDATE_MODEL_DIRS = [
    os.path.abspath(os.path.join(THIS_DIR, "..", "ml_models")),
    os.path.abspath(os.path.join(THIS_DIR, "..", "..", "..", "ml_models")),
]

# Model configurations - Only PyTorch models
MODEL_CONFIGS = {
    'vn30': {
        'name': 'Vietnamese Cuisine (VN30)',
        'type': 'pytorch',
        'file': 'best_vit_vn30food_model.pth',
        'architecture': 'vit_b_16',
        'input_size': 224,
    },
    'resnet_food101': {
        'name': 'ResNet-50 Food-101',
        'type': 'pytorch',
        'file': 'best_food101_model.pth',
        'architecture': 'resnet50',
        'input_size': 224,
    }
}


@dataclass
class _ModelState:
    model: Optional[Any] = None
    class_map: Optional[Dict[int, str]] = None
    input_size: int = 224
    model_path: Optional[str] = None
    model_type: Optional[str] = None
    config: Optional[Dict] = None
    device: Optional[Any] = None

# Store multiple model states
_model_cache: Dict[str, _ModelState] = {}


def _load_pytorch_vit(model_path: str, device) -> Tuple[Any, Dict[int, str]]:
    """Load Vision Transformer (ViT) PyTorch model"""
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch not installed")
    
    checkpoint = torch.load(model_path, map_location=device)
    num_classes = checkpoint['num_classes']
    
    # Initialize ViT architecture
    model = torchvision.models.vit_b_16(weights=None)
    
    # Modify classifier head to match training
    in_features = model.heads.head.in_features
    model.heads.head = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(in_features, 512),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(512, num_classes)
    )
    
    # Load weights
    model.load_state_dict(checkpoint['model_state_dict'])
    class_list = checkpoint['class_list']
    
    model = model.to(device)
    model.eval()
    
    # Convert class_list to dict mapping
    class_map = {i: class_name for i, class_name in enumerate(class_list)}
    
    return model, class_map


def _load_pytorch_resnet(model_path: str, device) -> Tuple[Any, Dict[int, str]]:
    """Load ResNet-50 PyTorch model"""
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch not installed")
    
    # Initialize ResNet architecture
    model = torchvision.models.resnet50(weights=None)
    
    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=device)
    num_classes = checkpoint['num_classes']
    
    # Modify classifier head
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.fc.in_features, num_classes)
    )
    
    # Load weights
    model.load_state_dict(checkpoint['model_state_dict'])
    class_list = checkpoint['class_list']
    
    model = model.to(device)
    model.eval()
    
    # Convert class_list to dict mapping
    class_map = {i: class_name for i, class_name in enumerate(class_list)}
    
    return model, class_map


def _ensure_model_loaded(model_key: str) -> _ModelState:
    """Load and cache model if not already loaded"""
    if model_key in _model_cache:
        return _model_cache[model_key]
    
    if model_key not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(MODEL_CONFIGS.keys())}")
    
    config = MODEL_CONFIGS[model_key]
    state = _ModelState(config=config, input_size=config['input_size'])
    
    # Resolve model path
    model_path = None
    for base in CANDIDATE_MODEL_DIRS:
        candidate = os.path.join(base, config['file'])
        if os.path.exists(candidate):
            model_path = candidate
            break
    
    if not model_path:
        raise FileNotFoundError(f"Model file not found: {config['file']}")
    
    state.model_path = model_path
    state.model_type = config['type']
    
    # Load PyTorch model
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch not installed but required for this model")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    start_load = time.time()
    state.device = device
    
    arch = config['architecture']
    try:
        if arch == 'vit_b_16':
            state.model, state.class_map = _load_pytorch_vit(model_path, device)
        elif arch == 'resnet50':
            state.model, state.class_map = _load_pytorch_resnet(model_path, device)
        else:
            raise ValueError(f"Unknown architecture: {arch}")
    except RuntimeError as re:
        if 'out of memory' in str(re).lower():
            raise RuntimeError("Model load OOM: consider removing large model or using smaller architecture") from re
        raise
    load_dur = (time.time() - start_load) * 1000
    try:
        fsz = os.path.getsize(model_path)
    except Exception:
        fsz = -1
    print(f"[inference] Loaded model '{model_key}' arch={arch} size={fsz} bytes in {load_dur:.1f}ms device={device}")
    
    # Cache the loaded model
    _model_cache[model_key] = state
    return state


def _preprocess_pytorch(img_bytes: bytes, size: int, architecture: str):
    """Preprocess image for PyTorch models"""
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch not installed")
    
    # Choose interpolation based on architecture
    if architecture == 'vit_b_16':
        interpolation = InterpolationMode.BICUBIC
    else:
        interpolation = InterpolationMode.BILINEAR
    
    transform = transforms.Compose([
        transforms.Resize((256, 256), interpolation=interpolation),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_tensor = transform(img)
    return img_tensor.unsqueeze(0)  # Add batch dimension


class InferenceService:
    def __init__(self, model_key: str = 'resnet_food101') -> None:
        self.model_key = model_key
        self.state = _ensure_model_loaded(model_key)
        self.model = self.state.model
        self.class_map = self.state.class_map
        self.input_size = self.state.input_size
        self.model_type = self.state.model_type
        self.config = self.state.config

    def predict(self, img_bytes: bytes) -> Dict[str, Any]:
        try:
            return self._predict_pytorch(img_bytes)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _predict_pytorch(self, img_bytes: bytes) -> Dict[str, Any]:
        """Predict using PyTorch model"""
        arch = self.config['architecture']
        img_tensor = _preprocess_pytorch(img_bytes, self.input_size, arch)
        img_tensor = img_tensor.to(self.state.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            
            # Get top 5
            top_probs, top_indices = torch.topk(probabilities, min(5, len(self.class_map)))
        
        # Top prediction
        idx = top_indices[0][0].item()
        conf = top_probs[0][0].item()
        class_name = self.class_map.get(idx, str(idx))
        food_name = class_name.replace("_", " ").title()
        
        # Top-5
        top5 = []
        for i in range(len(top_indices[0])):
            class_idx = top_indices[0][i].item()
            name = self.class_map.get(class_idx, str(class_idx))
            top5.append({
                "class_name": name,
                "confidence": float(top_probs[0][i].item())
            })
        
        return {
            "success": True,
            "class_name": class_name,
            "food_name": food_name,
            "confidence": conf,
            "top5": top5,
            "model_used": self.model_key,
            "model_name": self.config['name']
        }


_service_cache: Dict[str, InferenceService] = {}

def get_inference_service(model_key: str = 'resnet_food101') -> InferenceService:
    """Get or create inference service for specified model"""
    if model_key not in _service_cache:
        _service_cache[model_key] = InferenceService(model_key)
    return _service_cache[model_key]


def get_available_models() -> Dict[str, Dict[str, str]]:
    """Return list of available models"""
    return {
        key: {
            'name': config['name'],
            'type': config['type'],
            'file': config['file']
        }
        for key, config in MODEL_CONFIGS.items()
    }

def get_model_status() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for key, cfg in MODEL_CONFIGS.items():
        # Existence
        found_path = None
        for base in CANDIDATE_MODEL_DIRS:
            cand = os.path.join(base, cfg['file'])
            if os.path.exists(cand):
                found_path = cand
                break
        size = None
        if found_path:
            try:
                size = os.path.getsize(found_path)
            except Exception:
                size = None
        loaded = key in _model_cache and _model_cache[key].model is not None
        out[key] = {
            'architecture': cfg['architecture'],
            'file': cfg['file'],
            'exists': bool(found_path),
            'path': found_path,
            'size_bytes': size,
            'loaded': loaded,
        }
    return out