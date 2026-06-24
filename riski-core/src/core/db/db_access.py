import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import List, TypeVar, overload

from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Session, select

from core.db.db import get_session
from core.model.data_models import (
    RIS_NAME_OBJECT,
    RIS_PARSED_DB_OBJECT,
    AgendaItem,
    Consultation,
    File,
    Keyword,
    LegislativeTerm,
    Location,
    Meeting,
    Membership,
    Organization,
    Paper,
    Person,
    Post,
)
from src.logtools import getLogger

T = TypeVar("T", bound=RIS_PARSED_DB_OBJECT)
N = TypeVar("N", bound=RIS_NAME_OBJECT)
UPDATE_EXCLUDED_FIELDS_BY_CLASS = {
    File: {"content", "size"},
}

logger = getLogger()


def log_execution_time(func):
    """Decorator to log execution time and entrance/exit of a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log entrance
        logger.debug(f"Entering: {func.__name__}")

        start_time = time.time()

        try:
            # call function
            result = func(*args, **kwargs)
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            # Log exit
            logger.debug(f"Exiting: {func.__name__}")
            logger.debug(f"Execution time for {func.__name__}: {execution_time:.4f} seconds")

        return result

    return wrapper


@contextmanager
def _get_session_ctx():
    """
    Yield a session from `get_session()`.
    Use as: `with _get_session_ctx() as sess:`
    The code that owns the session must own commit/rollback.
    """
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def optional_session(session: Session | None = None):
    if session is not None:
        yield session
    else:
        with _get_session_ctx() as sess:
            yield sess


@log_execution_time
def request_object_by_risid(risid: str, object_type: type[T], session: Session) -> T | None:
    statement = select(object_type).where(object_type.id == risid)
    obj = session.exec(statement).first()
    return obj


@log_execution_time
def request_all(object_type: type[T]) -> List[T]:
    statement = select(object_type)
    with _get_session_ctx() as sess:
        objects = list(sess.exec(statement).all())
        return objects


@overload
def request_object_by_name(name: str, object_type: type[N], session: Session | None = None) -> N | None: ...


@overload
def request_object_by_name(name: str, object_type: type[Keyword], session: Session | None = None) -> Keyword | None: ...


@log_execution_time
def request_object_by_name(name: str, object_type: type[N] | type[Keyword], session: Session | None = None) -> N | Keyword | None:
    with optional_session(session) as sess:
        statement = select(object_type).where(object_type.name == name)
        obj = sess.exec(statement).first()
        return obj


@log_execution_time
def remove_object_by_id(id: str, object_type: type[T]):
    statement = select(object_type).where(object_type.id == id)
    with _get_session_ctx() as session:
        obj = session.exec(statement).first()
        if obj is None:
            logger.warning(f"Object with id '{id}' not found for deletion")
            return
        session.delete(obj)
        session.commit()


@log_execution_time
def insert_and_return_object(obj: RIS_PARSED_DB_OBJECT | Keyword, session: Session | None = None) -> RIS_PARSED_DB_OBJECT | Keyword:
    with optional_session(session) as sess:
        try:
            sess.add(obj)
            if session is None:
                sess.commit()
                sess.refresh(obj)
            return obj
        except Exception:
            if session is None:
                sess.rollback()
            raise


@log_execution_time
def request_person_by_familyName(familyName: str) -> Person | None:
    statement = select(Person).where(Person.familyName == familyName)
    with _get_session_ctx() as sess:
        results = list(sess.exec(statement).all())
        if len(results) > 1:
            logger.warning(f"Multiple Person records found for familyName '{familyName}'. Returning first match.")
        return results[0] if results else None


@log_execution_time
def update_or_insert_objects_to_database(objects: List[T]) -> None:
    total = len(objects)
    logger.debug("update_or_insert_objects_to_database: processing %d objects", total)
    for idx, obj in enumerate(objects, start=1):
        # Each object gets its own session/transaction for fault isolation
        # failures on individual objects won't roll back the entire batch.
        with _get_session_ctx() as sess:
            obj_db = request_object_by_risid(obj.id, type(obj), sess)
            if obj_db:
                logger.debug("updating existing %s id=%s (item %d/%d)", type(obj).__name__, getattr(obj, "id", None), idx, total)
                update_object(obj, obj_db, sess)
            else:
                logger.debug("inserting new %s id=%s (item %d/%d)", type(obj).__name__, getattr(obj, "id", None), idx, total)
                insert_object_to_database(obj, sess)
            sess.commit()


@log_execution_time
def update_object(obj, obj_db, session: Session) -> None:
    """
    Update a persistent ORM object using PUT semantics.

    The incoming `obj` is treated as the complete desired state:
    - Scalar fields are fully overwritten
    - Relationship collections are replaced wholesale
    - Missing or empty relationships remove existing associations
    - Related rows are NOT deleted unless cascade rules specify it

    Assumptions / guarantees:
    - `obj` is NOT attached to the session
    - `obj_db` IS persistent in the session
    - Related objects may already exist in the database
    - Related objects may be transient or detached
    - Relationship existence / authorization has been validated beforehand

    PUT impact:
    - Missing relationships ⇒ cleared
    - Removed collection items ⇒ disassociated
    - Orphan deletion occurs ONLY if `delete-orphan` is configured
    """
    mapper = inspect(obj_db).mapper
    pk_keys = {col.key for col in mapper.primary_key}
    excluded = UPDATE_EXCLUDED_FIELDS_BY_CLASS.get(type(obj_db), set())

    for attr in mapper.attrs:
        name = attr.key

        # Never overwrite identity or audit fields
        if name in pk_keys or name in {"created", "modified"}:
            continue

        if name in excluded:
            continue

        incoming = getattr(obj, name, None)
        updated_value = None

        # ---------- relationships ----------
        if isinstance(attr, RelationshipProperty):
            if attr.uselist:
                if incoming is None:
                    updated_value = []
                else:
                    updated_items = []
                    for item in incoming:
                        state = inspect(item)

                        if state.detached:
                            item = session.merge(item)
                        elif state.transient:
                            session.add(item)

                        updated_items.append(item)

                    updated_value = updated_items
            else:
                if incoming is None:
                    updated_value = None
                else:
                    state = inspect(incoming)

                    if state.detached:
                        incoming = session.merge(incoming)
                    elif state.transient:
                        session.add(incoming)

                    updated_value = incoming

        # ---------- scalar columns ----------
        else:
            updated_value = incoming

        setattr(obj_db, name, updated_value)


@log_execution_time
def update_file_content(file_id, content, fileName=None):
    with _get_session_ctx() as session:
        file_db = session.get(File, file_id)
        if not file_db:
            return

        file_db.content = content
        file_db.size = len(content)
        if fileName:
            file_db.fileName = fileName
        session.commit()


@log_execution_time
def insert_object_to_database(obj: T, session: Session) -> None:
    session.add(obj)


@log_execution_time
def get_or_insert_object_to_database(obj: RIS_PARSED_DB_OBJECT | Keyword) -> RIS_PARSED_DB_OBJECT | Keyword:
    """
    Retrieves or inserts an object into the database.

    Args:
        obj (T | Keyword): The object to retrieve or insert, identified by 'name' (keyword)
                 or 'id' (for others).

    Returns:
        obj_db: The retrieved or inserted object.
    """
    with _get_session_ctx() as sess:
        logger.debug("get_or_inserting new %s id=%s", type(obj).__name__, getattr(obj, "id", None))
        if isinstance(obj, Keyword):
            obj_db = request_object_by_name(obj.name, type(obj), sess)
        else:
            obj_db = request_object_by_risid(obj.id, type(obj), sess)

        if not obj_db:
            logger.debug("Not found. Inserting new %s id=%s", type(obj).__name__, getattr(obj, "id", None))
            obj_db = insert_and_return_object(obj, sess)
            sess.commit()
    return obj_db


@log_execution_time
def request_paper_by_reference(reference: str) -> None | Paper:
    stmt = select(Paper).where(Paper.reference == reference)
    with _get_session_ctx() as sess:
        results = list(sess.exec(stmt).all())

        if not results:
            logger.warning(f"No paper found for {reference}")
            return None
        elif len(results) > 1:
            logger.warning(f"Multiple papers found for reference '{reference}' — using the first one")

        paper = results[0]
        logger.debug(f"Found paper {reference} in DB (id={paper.id})")
        return paper


@log_execution_time
def request_person_by_full_name(familyName: str, givenName: str) -> Person | None:
    stmt = select(Person).where(Person.familyName == familyName, Person.givenName == givenName)
    with _get_session_ctx() as sess:
        results = list(sess.exec(stmt).all())

        if not results:
            logger.warning(f"No person found for {givenName} {familyName}")
            return None
        elif len(results) > 1:
            logger.warning(f"Multiple persons found for {givenName} {familyName} — using the first one")

        person = results[0]
        logger.debug(f"Found person {givenName} {familyName} in DB (id={person.id})")
        return person


@log_execution_time
def request_batch(model: type[T], offset: int, limit: int) -> List[T]:
    """
    Loads a batch of records for a given model with offset and limit.
    """
    statement = select(model).order_by(model.db_id).offset(offset).limit(limit)
    with _get_session_ctx() as sess:
        return list(sess.exec(statement).all())


@log_execution_time
def get_or_create_legislative_term(name: str) -> LegislativeTerm:
    """
    Retrieves or creates a LegislativeTerm by name (e.g., '2026-2032').

    Args:
        name: The name of the legislative term, e.g., '2026-2032'

    Returns:
        The retrieved or newly created LegislativeTerm object.
    """
    from core.model.data_models import LegislativeTerm

    with _get_session_ctx() as sess:
        # Check if it exists
        statement = select(LegislativeTerm).where(LegislativeTerm.name == name)
        existing = sess.exec(statement).first()
        if existing:
            return existing

        # Create new
        term = LegislativeTerm(id=f"term:{name}", name=name)
        sess.add(term)
        sess.commit()
        sess.refresh(term)
        return term


@log_execution_time
def get_or_create_agenda_item(id: str, name: str, number: str | None = None, order: int | None = None) -> "AgendaItem":
    """
    Retrieves or creates an AgendaItem by ID.

    Args:
        id: Unique identifier for the agenda item (e.g., 'meeting_url#agenda-1')
        name: Name/title of the agenda item
        number: Optional outline number (e.g., '1.', '1.1', 'A.')
        order: Optional position in the agenda (starting from 0)

    Returns:
        The retrieved or newly created AgendaItem object.
    """
    with _get_session_ctx() as sess:
        # Check if it exists
        statement = select(AgendaItem).where(AgendaItem.id == id)
        existing = sess.exec(statement).first()
        if existing:
            logger.debug(f"AgendaItem {id} already exists")
            return existing

        # Create new
        agenda_item = AgendaItem(
            id=id,
            name=name,
            number=number,
            order=order,
            public=True,
            deleted=False,
        )
        agenda_item.meetings = []
        agenda_item.keywords = []

        sess.add(agenda_item)
        sess.commit()
        sess.refresh(agenda_item)
        logger.debug(f"Created new AgendaItem {id}: {name}")
        return agenda_item


@log_execution_time
def create_agenda_items_for_meeting(meeting_id: str, agenda_data: List[dict]) -> List["AgendaItem"]:
    """
    Creates multiple agenda items for a meeting.

    Args:
        meeting_id: The ID/URL of the meeting
        agenda_data: List of dicts with keys: id, name, number (optional), order (optional), public (optional)

    Returns:
        List of created or retrieved AgendaItem objects.

    Example:
        agenda_data = [
            {"id": "url#agenda-1", "name": "Eröffnung", "number": "1", "order": 0},
            {"id": "url#agenda-2", "name": "Genehmigung Protokoll", "number": "2", "order": 1},
        ]
        items = create_agenda_items_for_meeting("meeting_url", agenda_data)
    """
    from core.model.data_models import Meeting

    agenda_items = []

    with _get_session_ctx() as sess:
        # Get the meeting from DB
        meeting = sess.exec(select(Meeting).where(Meeting.id == meeting_id)).first()
        if not meeting:
            logger.warning(f"Meeting {meeting_id} not found in database")
            return []

        # Create agenda items
        for item_data in agenda_data:
            item_id = item_data.get("id")
            name = item_data.get("name")

            if not item_id or not name:
                logger.warning(f"Skipping agenda item data with missing id or name: {item_data}")
                continue

            number = item_data.get("number")
            order = item_data.get("order")
            public = item_data.get("public", True)

            # Check if it exists
            existing = sess.exec(select(AgendaItem).where(AgendaItem.id == item_id)).first()
            if existing:
                logger.debug(f"AgendaItem {item_id} already exists, skipping")
                agenda_items.append(existing)
                continue

            # Create new
            agenda_item = AgendaItem(
                id=item_id,
                name=name,
                number=number,
                order=order,
                public=public,
                deleted=False,
            )
            agenda_item.meetings = [meeting]
            agenda_item.keywords = []

            sess.add(agenda_item)
            agenda_items.append(agenda_item)
            logger.debug(f"Created AgendaItem {item_id} for meeting {meeting_id}")

        sess.commit()
        # Refresh all items to get their db_ids
        for item in agenda_items:
            sess.refresh(item)

    return agenda_items


@log_execution_time
def request_agenda_items_by_meeting(meeting_id: str) -> List["AgendaItem"]:
    """
    Retrieves all agenda items for a specific meeting.

    Args:
        meeting_id: The ID/URL of the meeting

    Returns:
        List of AgendaItem objects for this meeting.
    """
    from core.model.data_models import Meeting, MeetingAgendaItemLink

    with _get_session_ctx() as sess:
        # Get all agenda items linked to this meeting
        statement = (
            select(AgendaItem)
            .join(MeetingAgendaItemLink, MeetingAgendaItemLink.agenda_item_id == AgendaItem.db_id)
            .join(Meeting, Meeting.db_id == MeetingAgendaItemLink.meeting_id)
            .where(Meeting.id == meeting_id)
        )

        results = list(sess.exec(statement).all())
        logger.debug(f"Found {len(results)} agenda items for meeting {meeting_id}")
        return results


@log_execution_time
def bulk_create_agenda_items(agenda_items: List["AgendaItem"]) -> int:
    """
    Bulk creates agenda items in the database.

    Args:
        agenda_items: List of AgendaItem objects to create

    Returns:
        Number of items successfully created.

    Note:
        Existing items (by ID) are skipped. Items should have their relationships
        (meetings, keywords) already set up before calling this function.
    """
    created_count = 0

    with _get_session_ctx() as sess:
        for item in agenda_items:
            try:
                # Check if exists
                existing = sess.exec(select(AgendaItem).where(AgendaItem.id == item.id)).first()
                if existing:
                    logger.debug(f"AgendaItem {item.id} already exists, skipping")
                    continue

                sess.add(item)
                created_count += 1
                logger.debug(f"Added AgendaItem {item.id} to session")
            except Exception as e:
                logger.warning(f"Error adding AgendaItem {item.id}: {e!r}")
                continue

        if created_count > 0:
            sess.commit()
            logger.info(f"Successfully created {created_count} agenda items")

    return created_count


@log_execution_time
def create_membership(
    person_id: str,
    organization_id: str,
    role: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    voting_right: bool = True,
    on_behalf_of: str | None = None,
) -> Membership | None:
    """
    Creates a Membership linking a Person to an Organization.

    Args:
        person_id: The Person's ID/URL
        organization_id: The Organization's ID/URL
        role: Role in the organization (e.g., "Vorsitz", "Mitglied")
        start_date: Start date of membership (ISO format or datetime object)
        end_date: End date of membership (ISO format or datetime object)
        voting_right: Whether the person has voting rights
        on_behalf_of: Optional grouping the person represents

    Returns:
        The created Membership object, or None if Person/Organization not found.
    """
    with _get_session_ctx() as sess:
        logger.debug(f"Looking for Person: {person_id}")
        person = sess.exec(select(Person).where(Person.id == person_id)).first()

        logger.debug(f"Looking for Organization: {organization_id}")
        organization = sess.exec(select(Organization).where(Organization.id == organization_id)).first()

        if not person:
            logger.warning(f"Person not found: {person_id}")
            # Debug: show what persons exist
            all_persons = sess.exec(select(Person)).all()
            sample_person_ids = [p.id for p in list(all_persons)[:3]]
            logger.debug(f"Sample person IDs in DB: {sample_person_ids}")
            return None
        if not organization:
            logger.warning(f"Organization not found: {organization_id}")
            # Debug: show what organizations exist
            all_orgs = sess.exec(select(Organization)).all()
            sample_org_ids = [o.id for o in list(all_orgs)[:3]]
            logger.debug(f"Sample org IDs in DB: {sample_org_ids}")
            return None

        # Parse dates if they are strings
        start_dt = _parse_date(start_date) if start_date else None
        end_dt = _parse_date(end_date) if end_date else None

        # Create membership with a unique ID
        membership_id = f"urn:riski:membership:{organization_id.split('/')[-1]}:{person_id.split('/')[-1]}"
        membership = Membership(
            id=membership_id,
            organization=organization.db_id,
            role=role,
            startDate=start_dt,
            endDate=end_dt,
            votingRight=voting_right,
            onBehalfOf=on_behalf_of,
            deleted=False,
        )
        membership.person = [person]
        membership.organizations = [organization]
        membership.keywords = []

        sess.add(membership)
        sess.commit()
        sess.refresh(membership)
        logger.info(f"Created Membership: {person.id} → {organization.id} (role: {role})")
        return membership


def _parse_date(date_input: str | datetime | None) -> datetime | None:
    """Parse a date string or return datetime as-is."""
    if not date_input:
        return None
    if isinstance(date_input, datetime):
        return date_input
    if isinstance(date_input, str):
        try:
            return datetime.fromisoformat(date_input)
        except ValueError:
            logger.warning(f"Could not parse date: {date_input}")
            return None
    return None


@log_execution_time
def create_post(name: str, organization_id: str) -> Post | None:
    """
    Creates a Post (position/role) in an Organization.

    Args:
        name: Name of the post (e.g., "Vorsitzender", "Stellvertreter")
        organization_id: The Organization's ID/URL

    Returns:
        The created Post object, or None if Organization not found.
    """
    with _get_session_ctx() as sess:
        organization = sess.exec(select(Organization).where(Organization.id == organization_id)).first()

        if not organization:
            logger.warning(f"Organization {organization_id} not found in database")
            return None

        post = Post(name=name, organization_id=organization.db_id)
        sess.add(post)
        sess.commit()
        sess.refresh(post)
        logger.info(f"Created Post: {name} in {organization.id}")
        return post


@log_execution_time
def create_consultation(
    paper_id: str,
    agenda_item_id: str,
    meeting_id: str,
    authoritative: bool = False,
    role: str | None = None,
) -> Consultation | None:
    """
    Creates a Consultation linking a Paper to an AgendaItem in a Meeting.

    Args:
        paper_id: The Paper's ID/URL
        agenda_item_id: The AgendaItem's ID/URL
        meeting_id: The Meeting's ID/URL
        authoritative: Whether a resolution was made
        role: Function of the consultation (e.g., "Anhörung")

    Returns:
        The created Consultation object, or None if any referenced object not found.
    """
    with _get_session_ctx() as sess:
        paper = sess.exec(select(Paper).where(Paper.id == paper_id)).first()
        agenda_item = sess.exec(select(AgendaItem).where(AgendaItem.id == agenda_item_id)).first()
        meeting = sess.exec(select(Meeting).where(Meeting.id == meeting_id)).first()

        if not paper:
            logger.warning(f"Paper {paper_id} not found in database")
            return None
        if not agenda_item:
            logger.warning(f"AgendaItem {agenda_item_id} not found in database")
            return None
        if not meeting:
            logger.warning(f"Meeting {meeting_id} not found in database")
            return None

        # Create consultation with a unique ID
        consultation_id = f"urn:riski:consultation:{meeting_id.split('/')[-1]}:{agenda_item_id.split('#')[-1]}:{paper_id.split('/')[-1]}"
        consultation = Consultation(
            id=consultation_id,
            paper=paper.db_id,
            agenda_item=agenda_item.db_id,
            meeting=meeting.db_id,
            authoritative=authoritative,
            role=role,
            deleted=False,
        )

        sess.add(consultation)
        sess.commit()
        sess.refresh(consultation)
        logger.info(f"Created Consultation: Paper {paper.id} → AgendaItem {agenda_item_id} in Meeting {meeting_id}")
        return consultation


@log_execution_time
def get_or_create_location(name: str) -> Location:
    """
    Retrieves or creates a Location by description/name.

    Args:
        name: The name/description of the location (e.g., 'Rathaus', 'Plenarsaal')

    Returns:
        The retrieved or newly created Location object.
    """
    with _get_session_ctx() as sess:
        existing = sess.exec(select(Location).where(Location.description == name)).first()
        if existing:
            logger.info(f"Location '{name}' already exists (db_id: {existing.db_id})")
            return existing

        location_id = f"urn:riski:location:{name.casefold().replace(' ', '-')}"
        location = Location(id=location_id, description=name, deleted=False)

        sess.add(location)
        sess.commit()
        sess.refresh(location)
        logger.info(f"Created new Location: {name} (db_id: {location.db_id}, id: {location.id})")
        return location
