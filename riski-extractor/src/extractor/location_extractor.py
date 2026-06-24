"""Location (Ort) extraction.

Note: Location objects are not directly retrievable from RIS. They appear as references on
meeting and motion detail pages (e.g., "Stadtratsgebaude" as a meeting venue, district names
in motion keywords). For now, this extractor is a no-op placeholder; locations should be
created ad-hoc by parsers when encountered, or populated via a dedicated seed script.
"""

from logging import Logger

from src.logtools import getLogger


class LocationExtractor:
    """Placeholder extractor for locations."""

    def __init__(self) -> None:
        self.logger: Logger = getLogger()
        self.logger.info("LocationExtractor initialized (no-op).")

    def run(self) -> None:
        self.logger.warning(
            "LocationExtractor is a placeholder. Locations should be seeded via a dedicated migration or created ad-hoc by parsers."
        )
