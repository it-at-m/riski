"""Throwaway reconnaissance script: discover RIS navigation paths and the
page-specific Wicket identifiers (filter form action, itemsperpage dropdown,
next-page AJAX url) needed to configure new extractors. Not shipped."""

import re
import sys

import httpx
from bs4 import BeautifulSoup

BASE = "https://risi.muenchen.de/risi"


def make_client() -> httpx.Client:
    return httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (compatible; ScraperBot/1.0)"})


def dump_nav(client: httpx.Client) -> None:
    r = client.get(BASE + "/")
    soup = BeautifulSoup(r.text, "html.parser")
    print(f"\n===== NAV LINKS (status {r.status_code}, final {r.url}) =====")
    seen = set()
    for a in soup.select("a[href]"):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if not text:
            continue
        key = (text, href)
        if key in seen:
            continue
        seen.add(key)
        if any(tok in href for tok in ("antrag", "person", "sitzung", "fraktion", "gremi", "ausschuss",
                                       "buerger", "versammlung", "vorlage", "wahlperiode", "ort", "empfehl")):
            print(f"  {text!r:55} -> {href}")


def dump_overview(client: httpx.Client, path: str) -> None:
    print(f"\n===== OVERVIEW {path} =====")
    r = client.get(BASE + path)
    print(f"status {r.status_code}, final {r.url}")
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # form actions
    forms = {f.get("action") for f in soup.find_all("form") if f.get("action")}
    print("  forms:")
    for f in sorted(forms):
        print(f"    {f}")

    # Wicket AJAX urls of interest
    scripts = soup.find_all("script")
    ajax = []
    for s in scripts:
        if s.string:
            ajax.extend(re.findall(r'Wicket\.Ajax\.ajax\(\{"u":"([^"]+)"', s.string))
    for tok in ("itemsperpage_dropdown_top", "nav_top-next", "-form"):
        hits = [u for u in ajax if tok in u]
        if hits:
            print(f"  ajax[{tok}]:")
            for h in hits[:4]:
                print(f"    {h}")

    # sample detail links
    links = [(a.get_text(' ', strip=True)[:40], a["href"]) for a in soup.select("a.headline-link[href]")][:5]
    print("  headline-links (sample):")
    for t, h in links:
        print(f"    {t!r:42} -> {h}")
    if not links:
        # alt: any detail links
        alt = [(a.get_text(' ', strip=True)[:40], a["href"]) for a in soup.select("a[href]") if "/detail/" in a.get("href", "")][:5]
        print("  /detail/ links (sample):")
        for t, h in alt:
            print(f"    {t!r:42} -> {h}")


if __name__ == "__main__":
    paths = sys.argv[1:]
    with make_client() as client:
        dump_nav(client)
        for p in paths:
            try:
                dump_overview(client, p)
            except Exception as e:  # noqa: BLE001
                print(f"  ERROR {p}: {e!r}")
