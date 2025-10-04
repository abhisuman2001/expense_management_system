from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from app.services.ocr_service import OCRService
from app.utils.decorators import auth_required
import uuid

ocr_bp = Blueprint('ocr', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ocr_bp.route('/extract', methods=['POST'])
@auth_required
def extract_receipt_data(current_user):
    try:
        # Check if file is present
        if 'receipt' not in request.files:
            return jsonify({'message': 'No receipt file provided'}), 400
        
        file = request.files['receipt']
        
        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'message': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP, TIFF'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.instance_path, current_app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        try:
            # Process receipt with OCR
            ocr_service = OCRService()
            extracted_data = ocr_service.process_receipt(file_path)
            
            if not extracted_data:
                return jsonify({'message': 'Failed to extract data from receipt'}), 400
            
            # Return extracted data
            response_data = {
                'message': 'Receipt processed successfully',
                'extracted_data': {
                    'amount': str(extracted_data.get('amount', '')),
                    'date': extracted_data.get('date').isoformat() if extracted_data.get('date') else '',
                    'merchant_name': extracted_data.get('merchant_name', ''),
                    'category': extracted_data.get('category', 'Other'),
                    'confidence': 'medium'  # You could implement confidence scoring
                },
                'raw_text': extracted_data.get('extracted_text', ''),
                'file_path': unique_filename
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            # Clean up file if processing fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        return jsonify({'message': 'OCR processing failed', 'error': str(e)}), 500

@ocr_bp.route('/supported-formats', methods=['GET'])
@auth_required
def get_supported_formats(current_user):
    return jsonify({
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size_mb': current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
    }), 200