from flask import Blueprint, current_app, jsonify, request
from src.models.lead import Lead

# Establish the v1 API Blueprint container
api_blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Simple ping endpoint to verify the server backbone is responsive."""
    return jsonify({"status": "healthy", "service": "AcademyOps API"}), 200

@api_blueprint.route('/leads', methods=['GET'])
def list_leads():
    # 1. Extract query parameters from the URL (with safe defaults)
    stage = request.args.get('stage')
    source = request.args.get('source')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # 2. Prevent negative pages or massive limits
    if page < 1: page = 1
    if limit < 1 or limit > 100: limit = 10
    
    repo = current_app.config['REPOSITORY']
    
    # 3. Fetch the data from your new repository method
    leads, total_count = repo.get_leads_advanced(stage, source, page, limit)
    
    # 4. Construct a professional JSON response with metadata
    return jsonify({
        "meta": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit
        },
        "data": [vars(lead) for lead in leads]
    }), 200

@api_blueprint.route('/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    repo = current_app.config['REPOSITORY']
    lead = repo.get_lead_by_id(lead_id)
    
    return jsonify(vars(lead)), 200

@api_blueprint.route('/leads', methods=['POST'])
def create_lead():
    data = request.get_json()
    
    # Validation: Ensure payload exists and required fields are present
    if not data or 'name' not in data or 'phone' not in data:
        return jsonify({"error": "Missing required fields: name and phone"}), 400
        
    repo = current_app.config['REPOSITORY']
    
    # Bundle the JSON data into your WP-01 Lead model
    new_lead = Lead(
        id=None, 
        name=data['name'], 
        phone=data['phone'], 
        source=data.get('source', 'Unknown'), 
        stage="New", 
        notes=data.get('notes', ''),
        created_at="", # Handled by Repo
        updated_at=""  # Handled by Repo
    )
    
    repo.add_lead(new_lead)
    return jsonify({"message": "Lead created successfully"}), 201

@api_blueprint.route('/leads/<int:lead_id>/stage', methods=['PATCH'])
def update_stage(lead_id):
    data = request.get_json()
    
    if not data or 'stage' not in data:
        return jsonify({"error": "Missing required field: stage"}), 400
        
    repo = current_app.config['REPOSITORY']
    
    # 1. Fetch the existing lead
    lead = repo.get_lead_by_id(lead_id)
    
    # 2. Update the stage
    lead.stage = data['stage']
    
    # 3. Save it back to the database
    repo.update_lead(lead)
    
    return jsonify({"message": f"Lead {lead_id} stage updated successfully"}), 200

@api_blueprint.route('/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    repo = current_app.config['REPOSITORY']
    repo.delete_lead(lead_id)
    
    return '', 204
