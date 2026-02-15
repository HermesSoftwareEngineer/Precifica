import os
import sys
from dotenv import load_dotenv

# Add project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app import create_app
from app.extensions import db
from app.models.evaluation import Evaluation, BaseListing


def normalize_property_type(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = value.strip()
    lowered = normalized.lower()

    mapping = [
        ("apartamento", "Apartamento"),
        ("apartment", "Apartamento"),
        ("casa", "Casa"),
        ("house", "Casa"),
        ("kitnet", "Kitnet"),
        ("loja", "Loja"),
        ("store", "Loja"),
        ("sala", "Sala"),
        ("office", "Sala"),
        ("terreno", "Terreno"),
        ("land", "Terreno")
    ]

    found = []
    for key, label in mapping:
        if key in lowered and label not in found:
            found.append(label)

    if found:
        return " / ".join(found)

    return normalized


def fix_property_type_values():
    app = create_app()
    with app.app_context():
        evals = Evaluation.query.all()
        listings = BaseListing.query.all()

        eval_updates = 0
        listing_updates = 0

        for ev in evals:
            normalized = normalize_property_type(ev.property_type)
            if ev.property_type != normalized:
                ev.property_type = normalized
                eval_updates += 1

        for listing in listings:
            normalized = normalize_property_type(listing.type)
            if listing.type != normalized:
                listing.type = normalized
                listing_updates += 1

        if eval_updates or listing_updates:
            db.session.commit()

        print(f"Updated evaluations: {eval_updates}")
        print(f"Updated base listings: {listing_updates}")


if __name__ == "__main__":
    fix_property_type_values()
