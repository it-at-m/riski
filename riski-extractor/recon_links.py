"""Inspect how detail links appear on overview pages + dump a few detail pages."""

import sys

import httpx
from bs4 import BeautifulSoup

BASE = "https://risi.muenchen.de/risi"


def links(client, path):
    print(f"\n===== LINKS on {path} =====")
    r = client.get(BASE + path)
    soup = BeautifulSoup(r.text, "html.parser")
    detail_anchors = [a for a in soup.select("a[href]") if "/detail/" in a.get("href", "")]
    print(f"  {len(detail_anchors)} /detail/ anchors. classes seen:")
    classes = {}
    for a in detail_anchors:
        c = " ".join(a.get("class", [])) or "(none)"
        classes[c] = classes.get(c, 0) + 1
    for c, n in classes.items():
        print(f"    class={c!r:40} x{n}")
    print("  sample headline-link:")
    for a in soup.select("a.headline-link[href]")[:5]:
        print(f"    {a.get_text(' ', strip=True)[:35]!r:37} -> {a.get('href')}")


def detail(client, path):
    print(f"\n===== DETAIL {path} =====")
    r = client.get(BASE + path)
    soup = BeautifulSoup(r.text, "html.parser")
    t = soup.select_one("h1.page-title")
    print("  title:", t.get_text(" ", strip=True) if t else None)
    for row in soup.select(".keyvalue-container .keyvalue-row"):
        k = row.select_one(".keyvalue-key")
        v = row.select_one(".keyvalue-value")
        if k and v:
            print(f"    {k.get_text(strip=True)!r:28} = {v.get_text(' ', strip=True)[:60]!r}")


if __name__ == "__main__":
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (compatible; ScraperBot/1.0)"}) as c:
        c.get(BASE + "/")
        mode = sys.argv[1]
        for p in sys.argv[2:]:
            (links if mode == "links" else detail)(c, p)
