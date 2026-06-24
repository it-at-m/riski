"""Debug script to analyze the actual Tagesordnung page structure."""

import httpx
from bs4 import BeautifulSoup

url = "https://risi.muenchen.de/risi/sitzung/detail/9015032/tagesordnung/oeffentlich"

print(f"Fetching: {url}\n")

try:
    client = httpx.Client(timeout=10)
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all sections
    print("=" * 80)
    print("SECTIONS FOUND:")
    print("=" * 80)
    sections = soup.find_all("section")
    for i, section in enumerate(sections):
        aria_id = section.get("aria-labelledby", "N/A")
        print(f"{i + 1}. {aria_id}")

    # Look for tables
    print("\n" + "=" * 80)
    print("TABLES FOUND:")
    print("=" * 80)
    tables = soup.find_all("table")
    print(f"Total tables: {len(tables)}\n")

    for t_idx, table in enumerate(tables):
        print(f"Table {t_idx + 1}:")
        print(f"  Classes: {table.get('class', [])}")
        print(f"  ID: {table.get('id', 'N/A')}")

        # Show header
        thead = table.find("thead")
        if thead:
            headers = thead.find_all("th")
            print(f"  Headers ({len(headers)}):")
            for h in headers:
                print(f"    - {h.get_text(strip=True)[:60]}")

        # Show first few rows
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            print(f"  Rows: {len(rows)}")
            print("  First 3 rows:")
            for r_idx, row in enumerate(rows[:3]):
                cols = row.find_all("td")
                print(f"    Row {r_idx + 1} ({len(cols)} cols):")
                for c_idx, col in enumerate(cols):
                    text = col.get_text(strip=True)[:70]
                    print(f"      Col {c_idx + 1}: {text}")

    # Look for divs with specific classes
    print("\n" + "=" * 80)
    print("DIVS WITH 'AGENDA' OR 'TAGESORDNUNG' CLASS:")
    print("=" * 80)
    divs = soup.find_all("div", class_=True)
    for div in divs:
        classes = div.get("class", [])
        class_str = " ".join(classes)
        if "agenda" in class_str.lower() or "tagesordnung" in class_str.lower():
            print(f"  Classes: {class_str}")
            print(f"    Content: {div.get_text(strip=True)[:60]}")

    # Look for list structures
    print("\n" + "=" * 80)
    print("LIST STRUCTURES:")
    print("=" * 80)
    lists = soup.find_all(["ul", "ol"])
    print(f"Total lists: {len(lists)}")

    for l_idx, lst in enumerate(lists[:3]):
        items = lst.find_all("li")
        print(f"List {l_idx + 1}: {len(items)} items")
        print(f"  Classes: {lst.get('class', [])}")
        for i_idx, item in enumerate(items[:3]):
            text = item.get_text(strip=True)[:70]
            print(f"    Item {i_idx + 1}: {text}")

    # Save full HTML for inspection
    with open("tagesordnung_9015032.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("\n" + "=" * 80)
    print("Full HTML saved to: tagesordnung_9015032.html")
    print("=" * 80)

    client.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
