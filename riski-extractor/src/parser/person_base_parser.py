import re

from src.data_models import Person
from src.parser.base_parser import BaseParser


class PersonBaseParser(BaseParser[Person]):
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
