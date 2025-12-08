from flask import Blueprint, jsonify
from flask_login import login_required
from app.controllers.dashboard_controller import DashboardController

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
@login_required
def get_summary():
    """
    Get summary statistics for the dashboard.
    """
    data = DashboardController.get_summary_stats()
    if "error" in data:
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/charts', methods=['GET'])
@login_required
def get_charts():
    """
    Get data for dashboard charts.
    """
    data = DashboardController.get_charts_data()
    if "error" in data:
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/trends', methods=['GET'])
@login_required
def get_trends():
    """
    Get evaluation trends over time.
    """
    data = DashboardController.get_evaluation_trends()
    if "error" in data:
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/distribution', methods=['GET'])
@login_required
def get_distribution():
    """
    Get price distribution data.
    """
    data = DashboardController.get_price_distribution()
    if "error" in data:
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/geographic', methods=['GET'])
@login_required
def get_geographic():
    """
    Get geographic statistics (top cities, neighborhoods).
    """
    data = DashboardController.get_geographic_stats()
    if "error" in data:
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/features', methods=['GET'])
@login_required
def get_features():
    """
    Get property features statistics (bedrooms, parking).
    """
    data = DashboardController.get_property_features_stats()
    if "error" in data:
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200
