from app.extensions import db
from app.models.evaluation import Evaluation
from app.models.user import User
from app.models.chat import Conversation
from sqlalchemy import func, desc
from datetime import datetime

class DashboardController:
    @staticmethod
    def get_summary_stats():
        try:
            total_evaluations = Evaluation.query.count()
            total_users = User.query.count()
            total_conversations = Conversation.query.count()
            
            avg_price_sqm = db.session.query(func.avg(Evaluation.region_value_sqm)).scalar() or 0
            
            return {
                "total_evaluations": total_evaluations,
                "total_users": total_users,
                "total_conversations": total_conversations,
                "average_price_sqm": round(avg_price_sqm, 2)
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_charts_data():
        try:
            # Evaluations by City
            city_stats = db.session.query(
                Evaluation.city, func.count(Evaluation.id)
            ).group_by(Evaluation.city).all()
            
            evaluations_by_city = {city: count for city, count in city_stats if city}

            # Evaluations by Property Type
            type_stats = db.session.query(
                Evaluation.property_type, func.count(Evaluation.id)
            ).group_by(Evaluation.property_type).all()
            
            evaluations_by_type = {ptype: count for ptype, count in type_stats if ptype}

            # Evaluations by Purpose (Residential/Commercial)
            purpose_stats = db.session.query(
                Evaluation.purpose, func.count(Evaluation.id)
            ).group_by(Evaluation.purpose).all()
            
            evaluations_by_purpose = {purpose: count for purpose, count in purpose_stats if purpose}

            return {
                "evaluations_by_city": evaluations_by_city,
                "evaluations_by_type": evaluations_by_type,
                "evaluations_by_purpose": evaluations_by_purpose
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_evaluation_trends():
        try:
            # Group by date
            trends_query = db.session.query(
                func.date(Evaluation.created_at).label('date'),
                func.count(Evaluation.id).label('count'),
                func.avg(Evaluation.region_value_sqm).label('avg_sqm')
            ).group_by(func.date(Evaluation.created_at)).order_by(func.date(Evaluation.created_at)).all()

            trends = [
                {
                    "date": str(t.date),
                    "count": t.count,
                    "avg_sqm": round(t.avg_sqm, 2) if t.avg_sqm else 0
                } for t in trends_query
            ]
            return {"trends": trends}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_price_distribution():
        try:
            sqm_values = db.session.query(Evaluation.region_value_sqm).filter(Evaluation.region_value_sqm > 0).all()
            values = [v[0] for v in sqm_values]
            
            if not values:
                return {"distribution": {}}

            min_val = min(values)
            max_val = max(values)
            bucket_size = (max_val - min_val) / 10 if max_val > min_val else 100
            
            buckets = {}
            for v in values:
                bucket_index = int((v - min_val) // bucket_size)
                bucket_key = f"{int(min_val + bucket_index * bucket_size)}-{int(min_val + (bucket_index + 1) * bucket_size)}"
                buckets[bucket_key] = buckets.get(bucket_key, 0) + 1

            return {"distribution": buckets}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_geographic_stats():
        try:
            top_cities = db.session.query(
                Evaluation.city,
                func.avg(Evaluation.region_value_sqm).label('avg_price')
            ).group_by(Evaluation.city).order_by(desc('avg_price')).limit(5).all()
            
            top_neighborhoods = db.session.query(
                Evaluation.neighborhood,
                Evaluation.city,
                func.avg(Evaluation.region_value_sqm).label('avg_price')
            ).group_by(Evaluation.neighborhood, Evaluation.city).order_by(desc('avg_price')).limit(10).all()

            return {
                "top_cities_by_price": [{"city": c, "avg_price": round(p, 2)} for c, p in top_cities],
                "top_neighborhoods_by_price": [{"neighborhood": n, "city": c, "avg_price": round(p, 2)} for n, c, p in top_neighborhoods]
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_property_features_stats():
        try:
            bedrooms_stats = db.session.query(
                Evaluation.bedrooms,
                func.avg(Evaluation.region_value_sqm)
            ).group_by(Evaluation.bedrooms).order_by(Evaluation.bedrooms).all()

            parking_stats = db.session.query(
                Evaluation.parking_spaces,
                func.avg(Evaluation.region_value_sqm)
            ).group_by(Evaluation.parking_spaces).order_by(Evaluation.parking_spaces).all()

            return {
                "price_by_bedrooms": {str(b): round(p, 2) for b, p in bedrooms_stats if b is not None and p},
                "price_by_parking": {str(pk): round(p, 2) for pk, p in parking_stats if pk is not None and p}
            }
        except Exception as e:
            return {"error": str(e)}
