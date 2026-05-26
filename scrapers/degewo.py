"""
Scraper dla degewo.de
Wyszukuje mieszkania 5-pokojowe i oznacza, czy wymagają WBS.
Strona renderowana server-side – używamy requests + BeautifulSoup (bez Playwright).
"""

import re
import time
import requests
from typing import Optional
from bs4 import BeautifulSoup

from models import Apartment

BASE_URL = "https://www.degewo.de"
SEARCH_URL = f"{BASE_URL}/immosuche/"
MIN_ROOMS = 4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}


def _parse_float(text: str) -> Optional[float]:
    """Wyciąga liczbę zmiennoprzecinkową z tekstu (format europejski: 1.234,56)."""
    if not text:
        return None
    clean = re.sub(r"[^\d,\.]", "", text.strip())
    clean = clean.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None


def _detect_wbs(text: str) -> tuple[bool, Optional[str]]:
    """
    Sprawdza czy ogłoszenie wymaga WBS.
    Zwraca (wbs_required: bool, wbs_type: str | None).
    """
    text_lower = text.lower()
    if "wbs" not in text_lower:
        return False, None

    # "ohne WBS" = WBS nie jest wymagany
    if re.search(r"\bohne\s+wbs\b", text_lower):
        return False, None

    # Szukaj konkretnego typu WBS (np. WBS 160, WBS 180, WBS 220)
    wbs_types = re.findall(r"wbs\s*(\d+)", text_lower)
    if wbs_types:
        return True, " / ".join(f"WBS {t}" for t in wbs_types)

    # Specjalne kategorie
    if "besonderer wohnbedarf" in text_lower:
        return True, "WBS – besonderer Wohnbedarf"

    return True, "WBS (typ nieokreślony)"


def _parse_page(soup: BeautifulSoup, min_rooms: float) -> list[Apartment]:
    """Parsuje jedną stronę wyników – zwraca listę mieszkań spełniających kryterium pokoi."""
    apartments = []
    listings = soup.select("div.c-teaser.c-teaser--apartment")

    for item in listings:
        copy = item.select_one("div.c-copy")
        if not copy:
            continue

        # Tytuł i URL
        title_el = copy.select_one("h3.c-headline a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        detail_url = href if href.startswith("http") else BASE_URL + href

        # Adres / dzielnica – format "Ulica 12 | Dzielnica"
        addr_el = copy.select_one("p")
        address_text = addr_el.get_text(strip=True) if addr_el else ""
        parts = [p.strip() for p in address_text.split("|")]
        address = parts[0] if parts else address_text
        district = parts[-1].strip() if len(parts) > 1 else ""

        # Dane z listy definicji dt (wartość) / dd (etykieta)
        rooms: Optional[float] = None
        area: Optional[float] = None
        warm_rent: Optional[float] = None
        available: Optional[str] = None

        for def_item in item.select("div.c-definition-list__item"):
            dt = def_item.select_one("dt")
            dd = def_item.select_one("dd")
            if not dt or not dd:
                continue
            label = dd.get_text(strip=True).lower()
            value = dt.get_text(strip=True)

            if "zimmer" in label:
                rooms = _parse_float(value)
            elif "warmmiete" in label:
                warm_rent = _parse_float(value)
            elif "m²" in label or "m2" in label:
                area = _parse_float(value)
            elif "frei ab" in label:
                available = value

        # Filtr – tylko >= min_rooms pokoi
        if rooms is None or rooms < min_rooms:
            continue

        # WBS – z tytułu i całego tekstu karty
        text_full = item.get_text(separator=" ", strip=True)
        wbs_required, wbs_type = _detect_wbs(text_full)

        apartments.append(Apartment(
            source="degewo",
            title=title,
            address=address,
            district=district,
            rooms=rooms,
            area_m2=area,
            warm_rent=warm_rent,
            cold_rent=None,
            available_from=available,
            wbs_required=wbs_required,
            wbs_type=wbs_type,
            url=detail_url,
        ))

    return apartments


def scrape_degewo(min_rooms: float = MIN_ROOMS) -> list[Apartment]:
    """
    Pobiera ogłoszenia z degewo.de i filtruje wg liczby pokoi.
    Strona SSR – używamy requests + BeautifulSoup (bez Playwright).
    """
    apartments: list[Apartment] = []
    url: Optional[str] = SEARCH_URL
    page_num = 1

    while url:
        print(f"[degewo] Przetwarzam stronę {page_num}...")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            print(f"[degewo] Błąd HTTP na stronie {page_num}: {exc} – przerywam paginację.")
            break
        soup = BeautifulSoup(resp.text, "html.parser")

        page_apts = _parse_page(soup, min_rooms)
        apartments.extend(page_apts)

        # Następna strona – szukaj linku "Zur nächsten Seite"
        next_link = None
        for a in soup.select("a[href*='tx_openimmo_immobilie']"):
            if re.search(r"n.chste", a.get_text(strip=True), re.IGNORECASE):
                next_link = a
                break

        if next_link:
            href = next_link.get("href", "")
            url = href if href.startswith("http") else BASE_URL + href
            page_num += 1
            time.sleep(0.5)
        else:
            url = None

    print(f"[degewo] Znaleziono {len(apartments)} mieszkań >= {min_rooms} pokoi.")
    return apartments


if __name__ == "__main__":
    results = scrape_degewo(min_rooms=4)
    if results:
        print("\n=== Wyniki ===")
        for apt in results:
            print(apt)
    else:
        print("Brak wyników dla podanych kryteriów.")
