from datetime import datetime, time

from core.db.db_access import update_or_insert_objects_to_database
from core.model.data_models import LegislativeTerm

LEGISLATIVE_TERMS = (
    ("1996-2002", "1996-05-01", "2002-04-30"),
    ("2002-2008", "2002-05-01", "2008-04-30"),
    ("2008-2014", "2008-05-01", "2014-04-30"),
    ("2014-2020", "2014-05-01", "2020-04-30"),
    ("2020-2026", "2020-05-01", "2026-04-30"),
    ("2026-2032", "2026-05-01", "2032-04-30"),
)


def extract_legislative_terms() -> list[LegislativeTerm]:
    legislativeTerm_array = []

    for name, start, end in LEGISLATIVE_TERMS:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.combine(datetime.fromisoformat(end).date(), time.max)
        legislativeTerm = LegislativeTerm(name=name, id=name, startDate=start_date, endDate=end_date)
        legislativeTerm_array.append(legislativeTerm)

    return legislativeTerm_array


def add_legislative_terms():
    legislativeTerm_array = extract_legislative_terms()
    update_or_insert_objects_to_database(legislativeTerm_array)
