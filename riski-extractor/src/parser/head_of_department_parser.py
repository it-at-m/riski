import re
from datetime import datetime
from logging import Logger

from bs4 import BeautifulSoup
from pydantic import HttpUrl

from src.data_models import Person
from src.logtools import getLogger


class HeadOfDepartmentParser:
    """
    Parser for Heads of Departments
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("Head of Department Parser initialized.")

    """
    Method for extracting the academic title of a person from their name.
    A list of potential titles is passed to the method.
    This list is best obtained by splitting the name at all spaces. 
    Then all substrings with special characters that are not '-' are determined and transferred.

    With these strings, it is possible that a title such as Dr.(Univ. Florence) is split into ['Dr.(Univ.','Florence)']
    These must be put together again to form a title.
    All strings are run through in sequence and if a '(' without ')' is found, a temporary
    string is created and the existing parts are joined together to form a string until a ')' is found.  
    """

    def _get_titles(self, titles: list[str]) -> list[str]:
        title_array = []
        current_academic_title = ""
        in_title = False

        for title_part in titles:
            if "(" in title_part and ")" not in title_part:
                current_academic_title += title_part
                in_title = True
            elif ")" in title_part and in_title:
                current_academic_title += " " + title_part
                in_title = False
                title_array.append(current_academic_title)
                current_academic_title = ""
            elif in_title:
                current_academic_title += title_part
            else:
                title_array.append(title_part)

        return title_array

    def _is_no_name(self, name: str) -> bool:
        special_char_regex = r"[\.\(\)]"
        return re.search(special_char_regex, name) is not None

    def _is_form_of_address(self, name: str) -> bool:
        form_of_address_regex = r"(Frau|Herr)"
        return re.search(form_of_address_regex, name) is not None

    def parse(self, url: str, html: str) -> Person:
        self.logger.info(f"Parsing Head of Department: {url}")
        soup = BeautifulSoup(html, "html.parser")

        create_date = datetime.now()

        title_wrapper = soup.find("h1", class_="page-title")
        title_element = title_wrapper.find("span", class_="d-inline-block") if title_wrapper else None
        name = title_element.contents[0] if title_element else "N/A"
        name = name.strip()

        status_element = soup.find("span", class_="d-inline-block page-additionaltitle")
        if status_element:
            status = status_element.get_text()
            status = status[1 : len(status) - 1]
        else:
            status = None
        self.logger.info(status)

        """
        The code for determining the names is still based on the old naming law before 2024.
        Since 2024, spouses can also have a double name without a "-" as a married name; this was not possible before.
        Before the change, only one surname was permitted, which is why all names before that were automatically first names.
        With the change, this is no longer the case, but since no differentiation of names would be possible at all, 
        this assumption is still made in the code. If this leads to problems, the data would have to be corrected manually 
        or the code would have to be adapted or removed. (Status: 2025-07-03)
        """
        # Last name
        parts_of_name = name.split(" ")
        self.logger.info(parts_of_name)
        given_name = []
        last_name = parts_of_name[-1]
        self.logger.info(last_name)

        potential_titles = []

        form_of_address: str | None = None
        for i in range(2, len(parts_of_name) + 1):
            if self._is_form_of_address(parts_of_name[-i]):
                form_of_address = parts_of_name[-i]
            elif self._is_no_name(parts_of_name[-i]):
                potential_titles.append(parts_of_name[-i])
                continue
            else:
                given_name.append(parts_of_name[-i])

        given_name.reverse()
        potential_titles.reverse()

        # --- Key-Value Data Extraction ---
        # Relevant for CV
        key_value_rows = soup.find_all("div", class_="keyvalue-row")
        data_dict = {}
        for row in key_value_rows:
            key_el = row.find("div", class_="keyvalue-key")
            val_el = row.find("div", class_="keyvalue-value")
            if key_el and val_el:
                key = key_el.get_text(strip=True)
                value = val_el.get_text(strip=True)
                data_dict[key] = value

        # --- Assemble Person ---
        person = Person(
            id=url,
            type="https://schema.oparl.org/1.1/Person",
            familyName=last_name,
            givenName=" ".join(given_name),
            name=name,
            created=create_date,
            formOfAddress=form_of_address,
            life=data_dict.get("Lebenslauf:"),
            lifeSource=url,
            modified=create_date,
            status=[status],
            title=self._get_titles(potential_titles),
            web=HttpUrl(url),
            deleted=False,
        )

        self.logger.info(f"Person object created: {person.givenName} {person.familyName}")
        return person
