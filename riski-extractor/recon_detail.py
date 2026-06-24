"""Dump key-value labels, section headers, title and download links of detail pages."""
import sys
import httpx
from bs4 import BeautifulSoup

BASE = "https://risi.muenchen.de/risi"


def dump(client, path):
    print(f"\n===== DETAIL {path} =====")
    r = client.get(BASE + path)
    print(f"status {r.status_code} final {r.url}")
    soup = BeautifulSoup(r.text, "html.parser")
    t = soup.select_one("h1.page-title")
    print("  title:", t.get_text(' ', strip=True) if t else None)
    add = soup.select_one("span.page-additionaltitle")
    print("  additionaltitle:", add.get_text(' ', strip=True) if add else None)
    print("  keyvalue rows:")
    for row in soup.select(".keyvalue-container .keyvalue-row"):
        k = row.select_one(".keyvalue-key")
        v = row.select_one(".keyvalue-value")
        if k and v:
            print(f"    {k.get_text(strip=True)!r:30} = {v.get_text(' ', strip=True)[:70]!r}")
    print("  section aria-labelledby:")
    for s in soup.select("section[aria-labelledby]"):
        print(f"    {s.get('aria-labelledby')}")
    print("  downloadlinks:")
    for a in soup.select("a.downloadlink")[:6]:
        print(f"    {a.get_text(strip=True)!r:40} -> {a.get('href')}")
    print("  tabs:")
    for a in soup.select("a[href*='tab=']")[:10]:
        print(f"    {a.get_text(' ',strip=True)[:30]!r:32} -> {a.get('href')}")


if __name__ == "__main__":
    with httpx.Client(timeout=30, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (compatible; ScraperBot/1.0)"}) as c:
        # establish session
        c.get(BASE + "/")
        for p in sys.argv[1:]:
            try:
                dump(c, p)
            except Exception as e:  # noqa: BLE001
                print("  ERR", p, repr(e))
