"""Bootstrap of the OParl ``System`` and ``Body`` objects.

OParl requires a System entry point and at least one Body. The RIS extractor
does not currently produce these, so this module creates them once if they are
missing. It is invoked on application startup and can also be run standalone::

    uv run python -m app.seed
"""

import logging
import uuid

from core.model.data_models import Body, Organization, Meeting, Paper, Person, System
from sqlmodel import Session, select

from app.oparl.urls import body_sublist_url, system_url
from app.settings import OParlSettings, get_settings

logger = logging.getLogger(__name__)


def ensure_system_and_body(session: Session, settings: OParlSettings) -> tuple[System, Body]:
    """Create the System and Body objects if they do not yet exist.

    Returns the existing or newly created (system, body). Idempotent.
    """
    base = settings.base_url

    system = session.exec(select(System)).first()
    if system is None:
        system = System(
            id=system_url(base),
            name=settings.system_name,
            oparlVersion=settings.oparl_version,
            license=settings.license,
            contactEmail=settings.contact_email,
            contactName=settings.contact_name,
            website=settings.website,
            vendor=settings.vendor,
            product=settings.product,
            web=settings.website,
        )
        session.add(system)
        session.commit()
        session.refresh(system)
        logger.info("Seeded OParl System object (db_id=%s)", system.db_id)

    body = session.exec(select(Body)).first()
    if body is None:
        bid = uuid.uuid4()
        body = Body(
            db_id=bid,
            id=f"{base}/bodies/{bid}",
            name=settings.body_name,
            shortName=settings.body_short_name,
            system=system_url(base),
            system_id=system.db_id,
            website=settings.website,
            license=settings.license,
            web=settings.website,
            # Required list-reference fields. The serializer regenerates the
            # canonical list URLs at request time; these stored values mirror them.
            organization=body_sublist_url(base, bid, Organization),
            person=body_sublist_url(base, bid, Person),
            meeting=body_sublist_url(base, bid, Meeting),
            paper=body_sublist_url(base, bid, Paper),
            legislativeTerm=f"{base}/bodies/{bid}/legislativeTerms",
            legislativeTermList=f"{base}/bodies/{bid}/legislativeTerms",
            agendaItem=f"{base}/bodies/{bid}/agendaItems",
            file=f"{base}/bodies/{bid}/files",
            membership=f"{base}/bodies/{bid}/memberships",
        )
        session.add(body)
        session.commit()
        session.refresh(body)
        logger.info("Seeded OParl Body object (db_id=%s)", body.db_id)

    return system, body


def main() -> None:
    from app.db import init_engine

    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = init_engine(settings.core.db.database_url.encoded_string())
    with Session(engine) as session:
        system, body = ensure_system_and_body(session, settings)
        print(f"System: {system.id}")
        print(f"Body:   {body.id} (db_id={body.db_id})")


if __name__ == "__main__":
    main()
