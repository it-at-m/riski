import asyncio
import sys
from logging import Logger

from config.config import Config, get_config
from core.db.db import create_db_and_tables, init_db
from src.extractor.city_council_faction_extractor import CityCouncilFactionExtractor
from src.extractor.city_council_meeting_extractor import CityCouncilMeetingExtractor
from src.extractor.city_council_meeting_template_extractor import CityCouncilMeetingTemplateExtractor
from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
from src.extractor.city_council_motion_extractor import CityCouncilMotionExtractor
from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
from src.filehandler.confidential_file_deleter import ConfidentialFileDeleter
from src.filehandler.filehandler import Filehandler
from src.version import get_version

from src.logtools import getLogger

config: Config
logger: Logger


async def main():
    config = get_config()
    config.print_config()
    logger = getLogger()
    version = get_version()

    init_db(config.core.db.database_url)
    create_db_and_tables()

    logger.info(f"RIS Indexer v{version} starting up")

    logger.info(f"Extract data from {config.start_date}{f' until {config.end_date}' if config.end_date else ''}")

    # --- City Council (StR) ---
    logger.info("Extracting City Council Factions")
    faction_extractor = CityCouncilFactionExtractor()
    faction_extractor.run()
    logger.info("Extracted City Council Factions")

    logger.info("Extracting City Council Members")
    city_council_member_extractor = CityCouncilMemberExtractor()
    city_council_member_extractor.run()
    logger.info("Extracted City Council Members")

    logger.info("Extracting Heads of Departments")
    head_of_department_extractor = HeadOfDepartmentExtractor()
    head_of_department_extractor.run()
    logger.info("Extracted Heads of Departments")

    logger.info("Extracting City Council Meetings")
    meeting_extractor = CityCouncilMeetingExtractor()
    meeting_extractor.run()
    logger.info("Extracted City Council Meetings")

    logger.info("Extracting City Council Meeting Templates")
    city_council_meeting_template_extractor = CityCouncilMeetingTemplateExtractor()
    city_council_meeting_template_extractor.run()
    logger.info("Extracted City Council Meeting Templates")

    logger.info("Extracting City Council Motions")
    city_council_motion_extractor = CityCouncilMotionExtractor()
    city_council_motion_extractor.run()
    logger.info("Extracted City Council Motions")

    logger.info("Extracting Agenda Items from Meeting Tagesordnung Pages")
    from src.extractor.meeting_tagesordnung_extractor import MeetingTagesordnungExtractor

    tagesordnung_extractor = MeetingTagesordnungExtractor()
    tagesordnung_extractor.run()
    logger.info("Extracted Agenda Items from Meeting Tagesordnung Pages")

    # --- District Committee (BA) ---
    logger.info("Extracting District Committee Members")
    from src.extractor.ba_member_extractor import BAMemberExtractor

    ba_member_extractor = BAMemberExtractor()
    ba_member_extractor.run()
    logger.info("Extracted District Committee Members")

    logger.info("Extracting District Committee Motions")
    from src.extractor.bezirksausschuss_paper_extractor import BAMotionExtractor

    ba_motion_extractor = BAMotionExtractor()
    ba_motion_extractor.run()
    logger.info("Extracted District Committee Motions")

    logger.info("Extracting Citizen Assembly Recommendations")
    from src.extractor.bezirksausschuss_paper_extractor import BVRecommendationExtractor

    bv_recommendation_extractor = BVRecommendationExtractor()
    bv_recommendation_extractor.run()
    logger.info("Extracted Citizen Assembly Recommendations")

    logger.info("Extracting Citizen Assembly Requests")
    from src.extractor.bezirksausschuss_paper_extractor import BVRequestExtractor

    bv_request_extractor = BVRequestExtractor()
    bv_request_extractor.run()
    logger.info("Extracted Citizen Assembly Requests")

    # --- Gremien (Committees/Factions) ---
    logger.info("Extracting City Council Committees")
    from src.extractor.gremium_organization_extractor import StRCommitteeExtractor

    str_committee_extractor = StRCommitteeExtractor()
    str_committee_extractor.run()
    logger.info("Extracted City Council Committees")

    logger.info("Extracting District Committees")
    from src.extractor.gremium_organization_extractor import BACommitteeExtractor

    ba_committee_extractor = BACommitteeExtractor()
    ba_committee_extractor.run()
    logger.info("Extracted District Committees")

    # --- Locations ---
    logger.info("Initializing Location placeholder")
    from src.extractor.location_extractor import LocationExtractor

    location_extractor = LocationExtractor()
    location_extractor.run()

    # --- Legislative Terms are created ad-hoc by parsers when encountered ---

    async with Filehandler() as filehandler:
        await filehandler.download_and_persist_files(batch_size=config.core.db.batch_size)

    confidential_file_deleter = ConfidentialFileDeleter()
    confidential_file_deleter.delete_confidential_files()

    # --- Gremium Memberships (must run after persons and organizations are in DB) ---
    logger.info("Extracting City Council Faction Memberships")
    from src.extractor.gremium_membership_extractor import StRFactionMembershipExtractor

    str_faction_membership_extractor = StRFactionMembershipExtractor()
    str_faction_membership_extractor.run()
    logger.info("Extracted City Council Faction Memberships")

    logger.info("Extracting City Council Committee Memberships")
    from src.extractor.gremium_membership_extractor import StRCommitteeMembershipExtractor

    str_committee_membership_extractor = StRCommitteeMembershipExtractor()
    str_committee_membership_extractor.run()
    logger.info("Extracted City Council Committee Memberships")

    logger.info("Extracting District Committee Memberships")
    from src.extractor.gremium_membership_extractor import BACommitteeMembershipExtractor

    ba_committee_membership_extractor = BACommitteeMembershipExtractor()
    ba_committee_membership_extractor.run()
    logger.info("Extracted District Committee Memberships")

    logger.info("Extraction process finished")

    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
