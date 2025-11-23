from __future__ import annotations
from flask import Blueprint, request, jsonify
from app.services.inference_service import get_inference_service, get_available_models  # type: ignore
from app.services.nutrition_service import get_nutrition_service  # type: ignore

bp = Blueprint('predict', __name__, url_prefix='/api')

@bp.get('/predict/models')
def list_models():
    """List all available models"""
    try:
        models = get_available_models()
        return jsonify({
            "success": True,
            "models": models
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.get('/predict/health')
def predict_health():
    """Quick check to ensure default model can be loaded"""
    try:
        # Check default model (changed to resnet_food101)
        infer = get_inference_service('resnet_food101')
        ok = infer is not None and getattr(infer, 'model', None) is not None
        
        return jsonify({
            "success": True,
            "model_loaded": bool(ok),
            "model_key": infer.model_key,
            "model_name": infer.config['name'],
            "model_type": infer.model_type,
            "available_models": list(get_available_models().keys())
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.post('/predict')
def predict():
    try:
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        content = request.files['file'].read()
        
        # Get model selection from request (default to resnet_food101)
        model_key = request.form.get('model', 'resnet_food101')
        
        # Validate model key
        available_models = get_available_models()
        if model_key not in available_models:
            return jsonify({
                "success": False, 
                "error": f"Invalid model: {model_key}. Available models: {list(available_models.keys())}"
            }), 400
        
        # Load inference service for selected model
        try:
            infer = get_inference_service(model_key)
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"Failed to load model '{model_key}': {str(e)}"
            }), 500
        
        # Load nutrition service
        try:
            nutri = get_nutrition_service()
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"Failed to load nutrition service: {str(e)}"
            }), 500

        # Make prediction
        pred = infer.predict(content)
        
        if not pred.get('success'):
            return jsonify({
                "success": False, 
                "error": pred.get('error', 'Prediction failed')
            }), 500
        
        # Get nutrition info
        nres = nutri.get_nutrition(pred.get('class_name', ''))
        nutrition = nres.get('nutrition') if nres.get('success') else {
            "calories": 0,
            "protein": 0,
            "fat": 0,
            "carbs": 0,
            "fiber": 0
        }
        
        pred['nutrition'] = nutrition
        
        return jsonify(pred)
    
    except Exception as e:
        # Final safety net
        return jsonify({
            "success": False, 
            "error": f"Unexpected server error: {str(e)}"
        }), 500