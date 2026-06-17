"""
Scraper dla gewobag.de
Krok 1: WordPress REST API → lista wszystkich mieszkań (szybko, JSON)
Krok 2: Playwright → strona szczegółów → tabela z danymi (Zimmer, Fläche, Miete, Adresse)
WBS: wykrywanie z class_list WP API (pewne źródło)
"""

import re
import time
import asyncio
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from playwright.async_api import async_playwright, Browser

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Apartment

# ── konfiguracja ───────────────────────────────────────────────────────────────
WP_API = "https://www.gewobag.de/wp-json/wp/v2/immobilien"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
OBJEKTTYP_WOHNUNG = "objekttyp-wohnung"
MIN_ROOMS = 4
DETAIL_CONCURRENCY = 3    # rownoleglose kart Playwright
DELAY_BETWEEN_PAGES = 0.5  # sekundy opoznienia miedzy stronami API

# ── Krok 1: WP REST API — lista wpisow ────────────────────────────────────────

def _wbs_from_classlist(class_list: list) -> tuple:
    """Wykrywa WBS z class_list WP API. Zwraca (wbs_required, wbs_type)."""
    for cls in class_list:
        if cls.startswith("wohnungstyp-wbs"):
            suffix = cls[len("wohnungstyp-wbs"):].strip("-").upper()
            wbs_type = f"WBS {suffix}" if suffix else "WBS"
            return True, wbs_type
    return False, None


def _wbs_type_from_title(title: str, fallback: str | None) -> str | None:
    """
    Wyciaga typy WBS z tytulu ogloszenia jako uzupelnienie/poprawka class_list.
    Obsluguje wzorce:
      'WBS 220'              -> WBS 220
      'WBS 160 / WBS 180'    -> WBS 160 / WBS 180
      'WBS 220/180/160'      -> WBS 160 / WBS 180 / WBS 220
      'WBS bis 160/180/220'  -> WBS 160 / WBS 180 / WBS 220
      '160er, 180er WBS'     -> WBS 160 / WBS 180
    """
    import re
    numbers: set[int] = set()

    # WBS bezposrednio przed lub po liczbie: "WBS 220", "WBS 160/180/220", "WBS bis 160/180"
    for m in re.finditer(r'WBS\s*(?:bis\s*)?(\d{3})(?:[/,\s]+(\d{3}))*', title, re.IGNORECASE):
        segment = title[m.start():m.end()]
        for n in re.findall(r'\d{3}', segment):
            numbers.add(int(n))

    # liczby przed WBS: "160er, 180er oder 220er WBS"
    for m in re.finditer(r'(\d{3})er\b', title, re.IGNORECASE):
        # sprawdz czy w poblizu (30 znakow) jest slowo WBS
        window = title[max(0, m.start() - 5): m.end() + 30]
        if re.search(r'\bWBS\b', window, re.IGNORECASE):
            numbers.add(int(m.group(1)))

    if numbers:
        return " / ".join(f"WBS {n}" for n in sorted(numbers))
    return fallback


def _rooms_from_title(title: str) -> Optional[float]:
    """
    Fallback: wyciaga liczbe pokoi z tytulu gdy strona szczegolów nie podaje danych.
    Obsluguje: '1 Zimmerwohnung', '2-Zimmer', '3,5 Zimmer' itd.
    """
    m = re.search(r'(\d+(?:[,\.]\d+)?)\s*[-–]?\s*Zimmer', title, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except ValueError:
            pass
    return None


def _district_from_classlist(class_list: list) -> str:
    """Wyciaga dzielnice z class_list np. bezirke-spandau-haselhorst."""
    for cls in class_list:
        if cls.startswith("bezirke-") and not cls.startswith("bezirke-stellplatz"):
            parts = cls[len("bezirke-"):].split("-")
            return " - ".join(p.capitalize() for p in parts if p)
    return ""


def fetch_all_wp_apartments() -> list:
    """
    Pobiera wszystkie mieszkania z WP REST API.
    Zwraca liste slownikow z: url, slug, title, wbs_required, wbs_type, district.
    """
    results = []
    page = 1
    per_page = 100

    print("[gewobag] Pobieranie listy z WP REST API...")
    while True:
        params = {
            "per_page": per_page,
            "page": page,
            "_fields": "id,slug,link,title,class_list",
        }
        try:
            resp = requests.get(WP_API, params=params, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            print(f"[gewobag] Blad HTTP str.{page}: {e}")
            break

        if resp.status_code == 400:
            break
        if resp.status_code != 200:
            print(f"[gewobag] HTTP {resp.status_code} str.{page}")
            break

        posts = resp.json()
        if not posts:
            break

        for post in posts:
            class_list = post.get("class_list", [])
            # Tylko mieszkania, bez garaży
            if OBJEKTTYP_WOHNUNG not in class_list:
                continue
            wbs_required, wbs_type = _wbs_from_classlist(class_list)
            district = _district_from_classlist(class_list)
            title = BeautifulSoup(
                post.get("title", {}).get("rendered", ""), "html.parser"
            ).get_text(strip=True)
            results.append({
                "url": post.get("link", ""),
                "slug": post.get("slug", ""),
                "title": title,
                "wbs_required": wbs_required,
                "wbs_type": wbs_type,
                "district": district,
            })

        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        print(f"[gewobag]   str. {page}/{total_pages}: {len(posts)} wpisow "
              f"({len(results)} mieszkan lacznie)")
        if page >= total_pages:
            break
        page += 1
        time.sleep(DELAY_BETWEEN_PAGES)

    print(f"[gewobag] Lacznie mieszkan w WP: {len(results)}")
    return results


# ── Krok 2: Playwright — dane szczegolowe z tabeli ────────────────────────────

def _parse_number(s: str) -> Optional[float]:
    """'1.802,70' → 1802.70  lub  '66,16' → 66.16"""
    s = s.strip().replace("\xa0", "").replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_detail_table(table_rows: list) -> dict:
    """Parsuje wiersze tabeli ze strony szczegolów na slownik danych."""
    data: dict = {}
    for row in table_rows:
        if len(row) < 2:
            continue
        key = row[0].strip().lower()
        val = row[1].strip()

        if "anzahl zimmer" in key:
            data["rooms"] = _parse_number(val)
        elif "fl" in key and "m" in key:  # Flache in m2
            v = re.sub(r"m[²2]", "", val).strip()
            data["area_m2"] = _parse_number(v)
        elif key == "grundmiete":
            v = re.sub(r"[^0-9,.]", "", val)
            data["cold_rent"] = _parse_number(v)
        elif "gesamtmiete" in key:
            v = re.sub(r"[^0-9,.]", "", val)
            data["warm_rent"] = _parse_number(v)
        elif "anschrift" in key:
            data["address"] = val if val not in ("", ",") else ""
        elif "bezirk" in key:
            data["district_detail"] = val
        elif "frei ab" in key:
            data["available_from"] = val if val else None
        elif "objektnummer" in key:
            data["objektnummer"] = val

    return data


async def _fetch_detail(browser: Browser, url: str, semaphore: asyncio.Semaphore) -> dict:
    """Laduje strone szczegolów i parsuje tabele. Zwraca slownik danych."""
    async with semaphore:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=25000)
            await asyncio.sleep(0.8)

            table_rows = []
            tables = await page.query_selector_all("table")
            for tbl in tables:
                rows = await tbl.query_selector_all("tr")
                for row in rows:
                    cells = await row.query_selector_all("td,th")
                    texts = [await c.inner_text() for c in cells]
                    texts = [t.strip() for t in texts]
                    if any(texts):
                        table_rows.append(texts)

            return _parse_detail_table(table_rows)

        except Exception as e:
            print(f"[gewobag] Blad {url.split('/')[-2]}: {e}")
            return {}
        finally:
            await page.close()


async def _fetch_all_details(entries: list) -> list:
    """Pobiera szczegoly dla wszystkich wpisow rownolegloscia DETAIL_CONCURRENCY."""
    semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)
    total = len(entries)
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print(f"[gewobag] Pobieranie szczegolów dla {total} mieszkan "
              f"(rownoleglosc {DETAIL_CONCURRENCY})...")

        batch_size = DETAIL_CONCURRENCY * 5
        for i in range(0, total, batch_size):
            batch = entries[i: i + batch_size]
            tasks = [_fetch_detail(browser, e["url"], semaphore) for e in batch]
            details_list = await asyncio.gather(*tasks)
            results.extend(zip(batch, details_list))
            done = min(i + len(batch), total)
            print(f"[gewobag]   {done}/{total} pobrano")

        await browser.close()

    return results


# ── główna funkcja ─────────────────────────────────────────────────────────────

def scrape_gewobag(min_rooms: float = MIN_ROOMS) -> List[Apartment]:
    """
    Pobiera wszystkie oferty mieszkan z gewobag.de.
    Filtruje do rooms >= min_rooms (lub rooms=None jesli nie podano).
    """
    # Krok 1: lista mieszkan z WP API
    wp_entries = fetch_all_wp_apartments()
    if not wp_entries:
        return []

    # Krok 2: szczegoly przez Playwright
    pairs = asyncio.run(_fetch_all_details(wp_entries))

    apartments: List[Apartment] = []
    for entry, details in pairs:
        rooms = details.get("rooms")

        # Fallback: wyciagnij liczbe pokoi z tytulu (np. dla ofert "Auf Anfrage")
        if rooms is None:
            rooms = _rooms_from_title(entry["title"])

        # Filtr pokojowy
        if rooms is not None and rooms < min_rooms:
            continue

        # Dzielnica: preferuj dane ze strony szczegolów
        district_detail = details.get("district_detail", "")
        district = district_detail if district_detail else entry["district"]

        apt = Apartment(
            source="gewobag",
            title=entry["title"],
            address=details.get("address", ""),
            district=district,
            rooms=rooms,
            area_m2=details.get("area_m2"),
            warm_rent=details.get("warm_rent"),
            cold_rent=details.get("cold_rent"),
            available_from=details.get("available_from"),
            wbs_required=entry["wbs_required"],
            wbs_type=_wbs_type_from_title(entry["title"], entry["wbs_type"]),
            url=entry["url"],
            extra={
                "slug": entry["slug"],
                "objektnummer": details.get("objektnummer", ""),
            },
        )
        apartments.append(apt)

    print(f"\n[gewobag] Wynik koncowy: {len(apartments)} mieszkan >= {min_rooms} pokoi.")
    return apartments


# ── uruchomienie bezposrednie ──────────────────────────────────────────────────
if __name__ == "__main__":
    apartments = scrape_gewobag()
    if not apartments:
        print("Brak wynikow.")
    else:
        print("\n" + "=" * 80)
        print(f"ZNALEZIONE MIESZKANIA ({len(apartments)}):")
        print("=" * 80)
        for apt in apartments:
            wbs_info = f"WBS: {apt.wbs_type}" if apt.wbs_required else "Bez WBS"
            rooms_str = f"{apt.rooms:.0f} pok." if apt.rooms else "? pok."
            area_str = f"{apt.area_m2:.2f} m2" if apt.area_m2 else "? m2"
            rent_str = (
                f"{apt.warm_rent:.2f} EUR (caly)" if apt.warm_rent
                else f"{apt.cold_rent:.2f} EUR (zimny)" if apt.cold_rent
                else "? EUR"
            )
            avail = apt.available_from or "?"
            print(
                f"  [{apt.source}] {apt.title}\n"
                f"    {rooms_str} | {area_str} | {rent_str} | od: {avail}\n"
                f"    Adres: {apt.address} | {apt.district}\n"
                f"    {wbs_info}\n"
                f"    {apt.url}\n"
            )
