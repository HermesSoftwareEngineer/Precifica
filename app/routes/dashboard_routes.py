from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.controllers.dashboard_controller import DashboardController
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """
    Retorna todas as estatísticas do dashboard:
    - Top Bairros por preço médio do m² (agrupados por venda e aluguel)
    - Top Cidades por preço médio do m² (agrupados por venda e aluguel)
    - Avaliações por tipo de imóvel
    - Avaliações por finalidade (Residencial vs Comercial)
    - Preço médio do m² por finalidade (Residencial vs Comercial)
    - Preço médio do m² por tipo de imóvel
    - Preço médio do m² por nº de quartos
    """
    logger.info("Dashboard stats requested")
    data = DashboardController.get_dashboard_stats()
    if "error" in data:
        logger.error(f"Error in dashboard stats: {data['error']}")
        return jsonify({"error": data["error"]}), 500
    return jsonify(data), 200
