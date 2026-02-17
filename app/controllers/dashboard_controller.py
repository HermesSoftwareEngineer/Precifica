from app.extensions import db
from app.models.evaluation import Evaluation
from app.models.user import User
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, desc, case
import logging

logger = logging.getLogger(__name__)

class DashboardController:
    @staticmethod
    def get_dashboard_stats():
        """
        Retorna todas as estatísticas do dashboard em uma única resposta:
        - Top Bairros por preço médio do m² (agrupados por venda e aluguel)
        - Top Cidades por preço médio do m² (agrupados por venda e aluguel)
        - Avaliações por tipo de imóvel
        - Avaliações por finalidade (Residencial vs Comercial)
        - Preço médio do m² por finalidade (Residencial vs Comercial)
        - Preço médio do m² por tipo de imóvel
        - Preço médio do m² por nº de quartos
        """
        logger.info("Fetching dashboard statistics")
        try:
            # Get user's active unit
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            if not user or not user.active_unit_id:
                return {"error": "No active unit selected"}, 400
            
            active_unit_id = user.active_unit_id
            
            # Top Bairros por preço médio do m² (Venda)
            top_neighborhoods_sale = db.session.query(
                Evaluation.neighborhood,
                Evaluation.city,
                func.avg(Evaluation.region_value_sqm).label('avg_price')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                (Evaluation.classification.ilike('%venda%') | Evaluation.classification.ilike('%sale%')),
                Evaluation.neighborhood.isnot(None),
                Evaluation.region_value_sqm.isnot(None),
                Evaluation.region_value_sqm > 0,
                Evaluation.area.isnot(None),
                Evaluation.area > 0
            ).group_by(
                Evaluation.neighborhood, Evaluation.city
            ).order_by(desc('avg_price')).limit(10).all()

            # Top Bairros por preço médio do m² (Aluguel)
            top_neighborhoods_rent = db.session.query(
                Evaluation.neighborhood,
                Evaluation.city,
                func.avg(Evaluation.region_value_sqm).label('avg_price')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                (Evaluation.classification.ilike('%aluguel%') | Evaluation.classification.ilike('%rent%')),
                Evaluation.neighborhood.isnot(None),
                Evaluation.region_value_sqm.isnot(None),
                Evaluation.region_value_sqm > 0,
                Evaluation.area.isnot(None),
                Evaluation.area > 0
            ).group_by(
                Evaluation.neighborhood, Evaluation.city
            ).order_by(desc('avg_price')).limit(10).all()

            # Top Cidades por preço médio do m² (Venda)
            top_cities_sale = db.session.query(
                Evaluation.city,
                func.avg(Evaluation.region_value_sqm).label('avg_price'),
                func.count(Evaluation.id).label('count')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                (Evaluation.classification.ilike('%venda%') | Evaluation.classification.ilike('%sale%')),
                Evaluation.city.isnot(None),
                Evaluation.region_value_sqm.isnot(None),
                Evaluation.region_value_sqm > 0,
                Evaluation.area.isnot(None),
                Evaluation.area > 0
            ).group_by(Evaluation.city).order_by(desc('avg_price')).limit(10).all()

            # Top Cidades por preço médio do m² (Aluguel)
            top_cities_rent = db.session.query(
                Evaluation.city,
                func.avg(Evaluation.region_value_sqm).label('avg_price'),
                func.count(Evaluation.id).label('count')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                (Evaluation.classification.ilike('%aluguel%') | Evaluation.classification.ilike('%rent%')),
                Evaluation.city.isnot(None),
                Evaluation.region_value_sqm.isnot(None),
                Evaluation.region_value_sqm > 0,
                Evaluation.area.isnot(None),
                Evaluation.area > 0
            ).group_by(Evaluation.city).order_by(desc('avg_price')).limit(10).all()

            # Avaliações por tipo de imóvel
            evaluations_by_type = db.session.query(
                Evaluation.property_type,
                func.count(Evaluation.id).label('count')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                Evaluation.property_type.isnot(None)
            ).group_by(Evaluation.property_type).all()

            # Avaliações por finalidade (Residencial vs Comercial)
            evaluations_by_purpose = db.session.query(
                Evaluation.purpose,
                func.count(Evaluation.id).label('count')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                Evaluation.purpose.isnot(None)
            ).group_by(Evaluation.purpose).all()

            # Preço médio do m² por finalidade
            avg_price_by_purpose = db.session.query(
                Evaluation.purpose,
                func.avg(Evaluation.region_value_sqm).label('avg_price')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                Evaluation.purpose.isnot(None),
                Evaluation.region_value_sqm.isnot(None),
                Evaluation.region_value_sqm > 0,
                Evaluation.area.isnot(None),
                Evaluation.area > 0
            ).group_by(Evaluation.purpose).all()

            # Preço médio do m² por tipo de imóvel
            avg_price_by_type = db.session.query(
                Evaluation.property_type,
                func.avg(Evaluation.region_value_sqm).label('avg_price')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                Evaluation.property_type.isnot(None),
                Evaluation.region_value_sqm.isnot(None),
                Evaluation.region_value_sqm > 0,
                Evaluation.area.isnot(None),
                Evaluation.area > 0
            ).group_by(Evaluation.property_type).all()

            # Preço médio do m² por número de quartos
            avg_price_by_bedrooms = db.session.query(
                Evaluation.bedrooms,
                func.avg(Evaluation.region_value_sqm).label('avg_price'),
                func.count(Evaluation.id).label('count')
            ).filter(
                Evaluation.unit_id == active_unit_id,
                Evaluation.bedrooms.isnot(None),
                Evaluation.region_value_sqm.isnot(None),
                Evaluation.region_value_sqm > 0,
                Evaluation.area.isnot(None),
                Evaluation.area > 0
            ).group_by(Evaluation.bedrooms).order_by(Evaluation.bedrooms).all()

            return {
                "top_neighborhoods": {
                    "sale": [
                        {
                            "neighborhood": n,
                            "city": c,
                            "avg_price_sqm": round(p, 2) if p else 0
                        } for n, c, p in top_neighborhoods_sale
                    ],
                    "rent": [
                        {
                            "neighborhood": n,
                            "city": c,
                            "avg_price_sqm": round(p, 2) if p else 0
                        } for n, c, p in top_neighborhoods_rent
                    ]
                },
                "top_cities": {
                    "sale": [
                        {
                            "city": c,
                            "avg_price_sqm": round(p, 2) if p else 0,
                            "count": cnt
                        } for c, p, cnt in top_cities_sale
                    ],
                    "rent": [
                        {
                            "city": c,
                            "avg_price_sqm": round(p, 2) if p else 0,
                            "count": cnt
                        } for c, p, cnt in top_cities_rent
                    ]
                },
                "evaluations_by_type": {
                    ptype: count for ptype, count in evaluations_by_type
                },
                "evaluations_by_purpose": {
                    purpose: count for purpose, count in evaluations_by_purpose
                },
                "avg_price_sqm_by_purpose": {
                    purpose: round(p, 2) if p else 0 for purpose, p in avg_price_by_purpose
                },
                "avg_price_sqm_by_type": {
                    ptype: round(p, 2) if p else 0 for ptype, p in avg_price_by_type
                },
                "avg_price_sqm_by_bedrooms": [
                    {
                        "bedrooms": b,
                        "avg_price_sqm": round(p, 2) if p else 0,
                        "count": cnt
                    } for b, p, cnt in avg_price_by_bedrooms
                ]
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}", exc_info=True)
            return {"error": str(e)}
