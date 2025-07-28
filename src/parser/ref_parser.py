import re
from datetime import datetime
from logging import Logger

from bs4 import BeautifulSoup
from httpx import Client
from pydantic import HttpUrl

from src.data_models import Person
from src.logtools import getLogger


class RefParser:
    """
    Parser für Stadtratssitzungen
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("RefParser initialized.")

    """
    Methode zum Extrahieren der Akademischen Titel einer Person aus dem Namen.
    Der Methode wird eine Liste an potentiellen Titeln übergeben.
    Diese Liste wird am besten durch das Splitten des Namens an allen Leerzeichen. 
    Danach werden alle Teilstrings mit Sonderzeichen die nicht '-' sind ermittelt und übergeben.

    Bei diesen Strings kann es sein, dass ein Titel wie Dr.(Univ. Florenz) aufgeteilt ist in ['Dr.(Univ.','Florenz)']
    Diese müssne wieder zu einem Titel zusammgesetzt werden.
    Es werden der Reihe nach alle Strings durchlaufen und wenn eine '(' ohne ')' gefunden wird, wird ein temporärer
    string angelegt und solange die bestandeteile zu einem String zusammegefügt, bis eine ')' gefunden wird.
    """

    def _get_titles(self, titles: list[str]) -> list[str]:
        titel_array = []
        aktueller_titel = ""
        in_title = False

        for teil in titles:
            if "(" in teil and ")" not in teil:
                aktueller_titel += teil
                in_title = True
            elif ")" in teil and in_title:
                aktueller_titel += " " + teil
                in_title = False
                titel_array.append(aktueller_titel)
                aktueller_titel = ""
            elif in_title:
                aktueller_titel += teil
            else:
                titel_array.append(teil)

        return titel_array

    def _is_no_name(self, name: str) -> bool:
        special_char_regex = r"[\.\(\)]"
        return re.search(special_char_regex, name) is not None

    def _is_anrede(self, name: str) -> bool:
        anrede_regex = r"(Frau|Herr)"
        return re.search(anrede_regex, name) is not None

    def parse(self, url: str, html: str) -> Person:
        self.logger.info(f"Parsing referent: {url}")
        soup = BeautifulSoup(html, "html.parser")

        create_date = datetime.now()

        title_element = soup.find("h1", class_="page-title").find("span", class_="d-inline-block")
        name = title_element.contents[0] if title_element else "N/A"
        name = name.strip()

        status_element = soup.find("span", class_="d-inline-block page-additionaltitle")
        status = status_element.get_text()
        status = status[1 : len(status) - 1]
        self.logger.info(status)

        """
        Der Code zur Ermittlung der Namen orientiert sich noch am alten Namensrecht vor 2024.
        Seit 2024 können Ehepartner als Ehenamen auch einen Doppelnamen ohne "-" führen, dies war vorher nicht möglich.
        Vor der Änderung war somit lediglich ein Nachname zulässig, weshalb alle Namen davor automatisch Vornamen sind.
        Mit der Änderung ist das nicht mehr der Fall, da so allerdings überhaupt keine Differenzierung der Namen möglich wäre
        wird diese Annahme im Code weiter getroffen. Sollte das zu Problemen führen müsste man die Daten manuell korrigieren 
        oder den Code anpassen bzw. entfernen.
        """
        # Nachname
        namensbestandteile = name.split(" ")
        self.logger.info(namensbestandteile)
        vornamen = []
        nachname = namensbestandteile[-1]
        self.logger.info(nachname)

        pot_titles = []
        # Vornamen
        for i in range(2, len(namensbestandteile) + 1):
            if self._is_anrede(namensbestandteile[-i]):
                anrede = namensbestandteile[-i]
            elif self._is_no_name(namensbestandteile[-i]):
                pot_titles.append(namensbestandteile[-i])
                continue
            else:
                vornamen.append(namensbestandteile[-i])

        # Vornamen Umdrehen
        vornamen.reverse()

        pot_titles.reverse()

        # --- Key-Value Data Extraction ---
        # Relevant für Lebenslauf
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
            familyName=nachname,
            givenName=" ".join(vornamen),
            name=name,
            # schauen wie STR das macht oder leer lassen
            created=create_date,
            formOfAddress=anrede,
            life=data_dict["Lebenslauf:"],
            lifeSource=url,
            modified=create_date,
            status=[status],
            title=self._get_titles(pot_titles),
            web=HttpUrl(url),
            deleted=False,
        )

        self.logger.info(f"Person object created: {person.givenName} {person.familyName}")
        return person


def test():
    parser = RefParser()
    client = Client(proxy="http://internet-proxy-client.muenchen.de:80")
    response = client.get("https://risi.muenchen.de/risi/person/detail/1152817", follow_redirects=True)
    print(response)
    input()
    res = parser.parse("https://risi.muenchen.de/risi/person/detail/1152817", response.text)
    print(res)
    return


if __name__ == "__main__":
    test()
