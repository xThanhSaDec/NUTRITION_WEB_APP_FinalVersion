from __future__ import annotations
from flask import Blueprint, request, jsonify
from app.services.inference_service import get_inference_service  # type: ignore
from app.services.nutrition_service import get_nutrition_service  # type: ignore

bp = Blueprint('predict', __name__, url_prefix='/api')

@bp.get('/predict/health')
def predict_health():
    """Quick check to ensure model and class map can be loaded."""
    try:
        infer = get_inference_service()
        ok = infer is not None and getattr(infer, 'model', None) is not None
        return jsonify({
            "success": True,
            "model_loaded": bool(ok),
            "model_path": getattr(infer, 'model_path', None),
            "input_scale_01": getattr(infer, 'scale01', None),
            "preprocess_source": getattr(getattr(__import__('app.services.inference_service', fromlist=['_state']), '_state'), 'preprocess_source', None),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.post('/predict')
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file"}), 400
        content = request.files['file'].read()
        # Acquire services (may raise if model/files missing)
        try:
            infer = get_inference_service()
        except Exception as e:
            return jsonify({"success": False, "error": f"Init model failed: {str(e)}"}), 500
        try:
            nutri = get_nutrition_service()
        except Exception as e:
            return jsonify({"success": False, "error": f"Init nutrition failed: {str(e)}"}), 500

        pred = infer.predict(content)
        if not pred.get('success'):
            return jsonify({"success": False, "error": pred.get('error', 'predict failed')}), 500
        nres = nutri.get_nutrition(pred.get('class_name',''))
        nutrition = nres.get('nutrition') if nres.get('success') else {"calories":0,"protein":0,"fat":0,"carbs":0,"fiber":0}
        pred['nutrition'] = nutrition
        return jsonify(pred)
    except Exception as e:
        # Final safety net to always return JSON
        return jsonify({"success": False, "error": f"Unexpected server error: {str(e)}"}), 500
