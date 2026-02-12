import re

from bs4 import BeautifulSoup
from core.db.db_access import request_person_by_full_name
from core.model.data_models import Person

from src.parser.base_parser import BaseParser


class PersonParser(BaseParser[Person]):
    def __init__(self) -> None:
        super().__init__()
        self.logger.info("Person Parser initialized.")

    def _get_titles(self, titles: list[str]) -> list[str]:
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
                current_academic_title += " " + title_part
            else:
                title_array.append(title_part)

        return title_array

    def _is_no_name(self, name: str) -> bool:
        special_char_regex = r"[\.\(\)]"
        return re.search(special_char_regex, name) is not None

    def _is_form_of_address(self, name: str) -> bool:
        form_of_address_regex = r"^(Frau|Herr)$"
        return re.search(form_of_address_regex, name) is not None

    def parse(self, url: str, html: str) -> Person:
        self.logger.debug(f"Parsing person: {url}")
        url = re.split(r"[\?\&]", url)[0]
        soup = BeautifulSoup(html, "html.parser")

        title_wrapper = soup.find("h1", class_="page-title")
        title_element = title_wrapper.find("span", class_="d-inline-block") if title_wrapper else None
        name = title_element.contents[0] if title_element else "N/A"
        name = name.strip()

        status_element = soup.find("span", class_="d-inline-block page-additionaltitle")
        status = []
        if status_element:
            status_text = status_element.get_text()
            status = [status_text[1 : len(status_text) - 1]]
        self.logger.debug(status)

        # The code for determining the names is still based on the old naming law before 2024.
        # Since 2024, spouses can also have a double name without a "-" as a married name; this was not possible before.
        # Before the change, only one surname was permitted, which is why all names before that were automatically first names.
        # With the change, this is no longer the case, but since no differentiation of names would be possible at all,
        # this assumption is still made in the code. If this leads to problems, the data would have to be corrected manually
        # or the code would have to be adapted or removed. (Status: 2025-07-03)
        parts_of_name = name.split(" ")
        self.logger.debug(parts_of_name)
        given_name = []
        last_name = parts_of_name[-1]
        self.logger.debug(last_name)

        potential_titles = []
        form_of_address = None
        for i in range(2, len(parts_of_name) + 1):
            if self._is_form_of_address(parts_of_name[-i]):
                form_of_address = parts_of_name[-i]
            elif self._is_no_name(parts_of_name[-i]):
                potential_titles.append(parts_of_name[-i])
                continue
            else:
                given_name.append(parts_of_name[-i])

        potential_titles.reverse()
        given_name.reverse()
        given_name = " ".join(given_name)

        # --- Key-Value Data Extraction ---
        # Relevant for CV
        person_info = soup.find("section", attrs={"aria-labelledby": "sectionheader-personinfo"})
        data_dict = {}

        if person_info:
            card_content = person_info.find("div", class_="card-body")

            key_value_rows = []
            if card_content:
                key_value_rows = card_content.find_all("div", class_="keyvalue-row")

            for row in key_value_rows:
                key_el = row.find("div", class_="keyvalue-key")
                val_el = row.find("div", class_="keyvalue-value")
                if key_el and val_el:
                    key = key_el.get_text(strip=True)
                    value = val_el.get_text(strip=True)
                    data_dict[key] = value

        life = data_dict.get("Lebenslauf:")

        if last_name and given_name:
            existing_person = request_person_by_full_name(last_name, given_name)
        else:
            existing_person = None

        if existing_person and any(s not in existing_person.status for s in status):
            person = existing_person
            if not existing_person.name and name:
                person.name = name
            if not existing_person.formOfAddress and form_of_address:
                person.formOfAddress = form_of_address
            if (not existing_person.life and life) or (life and existing_person.life and len(existing_person.life) < len(life)):
                person.life = life
                person.lifeSource = url
            for stat in status:
                if stat not in existing_person.status:
                    existing_person.status.append(stat)

            return person

        # --- Assemble Person ---
        person = Person(
            id=url,
            familyName=last_name,
            givenName=given_name,
            name=name,
            formOfAddress=form_of_address,
            life=data_dict.get("Lebenslauf:"),
            lifeSource=url,
            status=status,
            title=(" ".join(self._get_titles(potential_titles)).strip() or None),
            web=url,
            deleted=False,
        )

        self.logger.debug(f"Person - object created: {person.givenName} {person.familyName}")
        return person
