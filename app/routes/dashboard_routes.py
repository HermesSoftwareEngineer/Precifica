from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.controllers.dashboard_controller import DashboardController
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """
    Get summary statistics for the dashboard.
    """
    logger.info("Dashboard summary requested")
    data = DashboardController.get_summary_stats()
    if "error" in data:
        logger.error(f"Error in dashboard summary: {data['error']}")
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/charts', methods=['GET'])
@jwt_required()
def get_charts():
    """
    Get data for dashboard charts.
    """
    logger.info("Dashboard charts requested")
    data = DashboardController.get_charts_data()
    if "error" in data:
        logger.error(f"Error in dashboard charts: {data['error']}")
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """
    Get evaluation trends over time.
    """
    logger.info("Dashboard trends requested")
    data = DashboardController.get_evaluation_trends()
    if "error" in data:
        logger.error(f"Error in dashboard trends: {data['error']}")
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/distribution', methods=['GET'])
@jwt_required()
def get_distribution():
    """
    Get price distribution data.
    """
    logger.info("Dashboard distribution requested")
    data = DashboardController.get_price_distribution()
    if "error" in data:
        logger.error(f"Error in dashboard distribution: {data['error']}")
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/geographic', methods=['GET'])
@jwt_required()
def get_geographic():
    """
    Get geographic statistics (top cities, neighborhoods).
    """
    logger.info("Dashboard geographic stats requested")
    data = DashboardController.get_geographic_stats()
    if "error" in data:
        logger.error(f"Error in dashboard geographic stats: {data['error']}")
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200

@dashboard_bp.route('/api/dashboard/features', methods=['GET'])
@jwt_required()
def get_features():
    """
    Get property features statistics (bedrooms, parking).
    """
    logger.info("Dashboard features stats requested")
    data = DashboardController.get_property_features_stats()
    if "error" in data:
        logger.error(f"Error in dashboard features stats: {data['error']}")
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200
