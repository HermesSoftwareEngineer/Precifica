import os
import sys
from dotenv import load_dotenv

# Add project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app import create_app
from app.extensions import db
from app.models.evaluation import Evaluation, BaseListing


def normalize_purpose(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = value.strip()
    lowered = normalized.lower()

    if "residential" in lowered and "commercial" in lowered:
        return "Residencial / Comercial"
    if "residencial" in lowered and "comercial" in lowered:
        return "Residencial / Comercial"
    if "residential" in lowered or "residencial" in lowered:
        return "Residencial"
    if "commercial" in lowered or "comercial" in lowered:
        return "Comercial"

    return normalized


def fix_purpose_values():
    app = create_app()
    with app.app_context():
        evals = Evaluation.query.all()
        listings = BaseListing.query.all()

        eval_updates = 0
        listing_updates = 0

        for ev in evals:
            normalized = normalize_purpose(ev.purpose)
            if ev.purpose != normalized:
                ev.purpose = normalized
                eval_updates += 1

        for listing in listings:
            normalized = normalize_purpose(listing.purpose)
            if listing.purpose != normalized:
                listing.purpose = normalized
                listing_updates += 1

        if eval_updates or listing_updates:
            db.session.commit()

        print(f"Updated evaluations: {eval_updates}")
        print(f"Updated base listings: {listing_updates}")


if __name__ == "__main__":
    fix_purpose_values()
