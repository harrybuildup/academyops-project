from flask import Flask, jsonify
from src.models.errors import LeadNotFoundError, DuplicatePhoneError
from src.repository.lead_repository import LeadRepository

def create_app(db_path):
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    app.config['REPOSITORY'] = LeadRepository(db_path)

    from src.web.routes import api_blueprint
    app.register_blueprint(api_blueprint)

    @app.errorhandler(LeadNotFoundError)
    def handle_not_found(error):
        """Intercepts missing database records and returns a 404."""
        return jsonify({"error": str(error)}), 404
        
    @app.errorhandler(DuplicatePhoneError)
    def handle_duplicate(error):
        """Intercepts database constraints and returns a 400."""
        return jsonify({"error": str(error)}), 400
        
    @app.errorhandler(400)
    def bad_request(error):
        """Catches generic bad requests (e.g., malformed JSON)."""
        return jsonify({"error": "Bad request or missing required fields."}), 400
        
    @app.errorhandler(404)
    def not_found(error):
        """Catches standard 404 routing errors."""
        return jsonify({"error": "The requested API endpoint was not found."}), 404
        
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """The ultimate safety net to prevent HTML stack traces from leaking."""
        # In a real app, you would log 'error' to academyops.log here!
        return jsonify({"error": "An internal server error occurred."}), 500

    return app