import re
from datetime import datetime
from logging import Logger

from bs4 import BeautifulSoup
from pydantic import HttpUrl

from src.data_models import Meeting
from src.logtools import getLogger


class STRParser:
    """
    Parser fuer Stadtratssitzungen
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()

    def parse(self, url: str, html: str) -> Meeting:
        soup = BeautifulSoup(html, "html.parser")
        # Extracting the title and meeting state
        title_element = soup.find("h1", class_="page-title")
        title = title_element.get_text(strip=True) if title_element else "N/A"

        # Check if the meeting is cancelled based on title
        cancelled = "(entfällt)" in title

        # Extracting dates and other information
        key_value_rows = soup.find_all("div", class_="keyvalue-row")
        data_dict = {}

        for row in key_value_rows:
            key = row.find("div", class_="keyvalue-key").get_text(strip=True)
            value = row.find("div", class_="keyvalue-value").get_text(strip=True)
            data_dict[key] = value

        type = data_dict["Gremium:"]
        print(type)
        name = title
        match = re.search(r"\((.*?)\)", title)
        if match:
            in_klammern = match.group(1)  # Der Inhalt in den Klammern
            meetingState = in_klammern

        else:
            meetingState = ""

        cancelled = "(entfällt)" in title

        # Regex, um den Teil vor den Klammern zu extrahieren
        match = re.search(r"^(.*?)\s*\(.*\)$", title)
        if match:
            date_time_str = match.group(1).strip()  # Der Text vor den Klammern
            date_time_str = date_time_str.replace(" Uhr", "")
            # Datum und Uhrzeit parsen
            try:
                # Datumsformat angeben, das mit dem extrahierten String übereinstimmt
                # TODO: Englisch/deutsch locale time anpassen
                start = datetime.strptime(date_time_str, "%A, %d. %B %Y, %H:%M")

            except ValueError as e:
                print(f"Fehler beim Parsen des Datums: {e}")
        else:
            start = datetime.min
        start = datetime.min
        end = datetime.min
        location = None
        organization = []
        participant = []
        invitation = ()
        resultsProtocol = ()
        verbatimProtocol = ()
        auxiliaryFile = []
        agendaItem = []
        license = ""
        keyword = ""
        created = datetime.min
        modified = datetime.min
        web = HttpUrl(url)
        deleted = False

        meeting = Meeting(
            type=type,
            name=name,
            cancelled=cancelled,
            start=start,
            end=end,
            location=location,
            organization=organization,
            participant=participant,
            invitation=invitation,
            resultsProtocol=resultsProtocol,
            verbatimProtocol=verbatimProtocol,
            auxiliaryFile=auxiliaryFile,
            agendaItem=agendaItem,
            license=license,
            keyword=keyword,
            created=created,
            modified=modified,
            web=web,
            deleted=deleted,
            meetingState=meetingState,
        )

        return meeting


def main():
    return


if __name__ == "__main__":
    main()
