"""
Scraper dla wbm.de (Wohnungsbaugesellschaft Berlin-Mitte).
Metoda: requests + BeautifulSoup (strona renderowana server-side, brak JS).
Paginacja: GET ?tx_openimmo_immobilie[page]=N
"""

import re
import sys
import os
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Apartment

BASE_URL = "https://www.wbm.de/wohnungen-berlin/angebote/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}

WBS_DISTRICTS = [
    "Mitte", "Friedrichshain", "Kreuzberg", "Prenzlauer Berg", "Pankow",
    "Charlottenburg", "Wilmersdorf", "Spandau", "Zehlendorf", "Steglitz",
    "Schöneberg", "Tempelhof", "Neukölln", "Treptow", "Köpenick",
    "Lichtenberg", "Weißensee", "Marzahn", "Hohenschönhausen",
    "Reinickendorf", "Hellersdorf", "Tiergarten", "Wedding",
]


def _parse_number(text: str) -> float | None:
    """Konwertuje europejski format liczby (1.535,43) na float."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d,.]", "", text.strip())
    # European: 1.535,43  -> remove dots, replace comma
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_page(soup: BeautifulSoup) -> list[Apartment]:
    """Parsuje jedną stronę wyników – zwraca listę wszystkich mieszkań."""
    apartments = []

    # Każde ogłoszenie jest wewnątrz div.row.openimmo-search-list-item
    rows = soup.select("div.row.openimmo-search-list-item")
    if not rows:
        # Fallback: bezpośrednio article.immo-element
        rows = soup.select("article.immo-element")

    for row in rows:
        # W wierszu są dwa article.immo-element:
        #   [0] = teaserBox z zdjęciem i dzielnicą
        #   [1] = karta z danymi tekstowymi
        all_articles = row.select("article.immo-element")
        card = None
        for art in all_articles:
            if art.select_one("h2.imageTitle"):
                card = art
                break
        if not card:
            continue

        # --- Tytuł ---
        title_tag = card.select_one("h2.imageTitle")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # --- Liczba pokoi ---
        rooms_tag = card.select_one(".main-property-rooms")
        try:
            rooms = float(rooms_tag.get_text(strip=True).replace(",", ".")) if rooms_tag else 0.0
        except ValueError:
            rooms = 0.0

        # --- Powierzchnia ---
        size_tag = card.select_one(".main-property-size")
        area_m2 = _parse_number(size_tag.get_text(strip=True)) if size_tag else None

        # --- Ciepły czynsz ---
        rent_tag = card.select_one(".main-property-rent")
        warm_rent = _parse_number(rent_tag.get_text(strip=True)) if rent_tag else None

        # --- Adres ---
        addr_tag = card.select_one("div.address")
        address = addr_tag.get_text(strip=True) if addr_tag else ""

        # --- WBS ---
        check_items = [li.get_text(strip=True) for li in card.select(".check-property-list li")]
        wbs_required = "WBS" in check_items

        # Typ WBS z tytułu np. "mit WBS 100/140"
        wbs_type = None
        m = re.search(r"WBS\s*([\d/]+)", title)
        if m:
            wbs_type = f"WBS {m.group(1)}"
        elif wbs_required:
            wbs_type = "WBS (typ nieznany)"

        # --- URL ---
        link_tag = card.select_one("a.immo-button-cta")
        href = link_tag["href"] if link_tag and link_tag.get("href") else ""
        url = "https://www.wbm.de" + href if href.startswith("/") else href

        # --- Dzielnica ---
        # Szukamy div.area w tym samym div.row (element teaserBox z zdjęciem)
        area_tag = row.select_one("div.area")
        if area_tag:
            district = area_tag.get_text(strip=True)
        else:
            # Fallback: wyodrębnij z tytułu np. "3-Zimmer-Wohnung in Spandau"
            district = ""
            m2 = re.search(r"\bin\s+([A-ZÄÖÜ][a-zäöüß-]+)", title)
            if m2:
                district = m2.group(1)

        apartments.append(Apartment(
            source="wbm",
            title=title,
            address=address,
            district=district,
            rooms=rooms,
            area_m2=area_m2,
            warm_rent=warm_rent,
            cold_rent=None,
            available_from=None,
            wbs_required=wbs_required,
            wbs_type=wbs_type,
            url=url,
            extra={"check_features": check_items},
        ))

    return apartments


def scrape(min_rooms: float = 5.0) -> list[Apartment]:
    """
    Pobiera wszystkie mieszkania z wbm.de i filtruje po liczbie pokoi.

    Args:
        min_rooms: Minimalna liczba pokoi (domyślnie 5).

    Returns:
        Lista obiektów Apartment.
    """
    results: list[Apartment] = []
    page = 1

    while True:
        params = {"tx_openimmo_immobilie[page]": page} if page > 1 else {}
        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=20)
        resp.raise_for_status()
        resp.encoding = "utf-8"  # strona serwuje UTF-8, requests czasem błędnie wykrywa latin-1
        soup = BeautifulSoup(resp.text, "html.parser")

        apartments = _parse_page(soup)
        if not apartments:
            break

        results.extend(apartments)

        # Sprawdź czy jest następna strona
        next_link = soup.select_one("a.pagination__next, li.next a, .tx-openimmo-immobilie-pagination a[rel='next']")
        if not next_link:
            # Alternatywnie: sprawdź czy ilość wyników wskazuje na kolejną stronę
            # (WBM ma małą bazę – zazwyczaj 1 strona)
            break

        page += 1

    # Filtruj po liczbie pokoi
    filtered = [a for a in results if a.rooms >= min_rooms]
    return filtered


if __name__ == "__main__":
    print("Scrapuje wbm.de...")
    all_apts = scrape(min_rooms=1.0)  # min_rooms=1 żeby zobaczyć wszystkie
    print(f"Znaleziono lacznie {len(all_apts)} mieszkan:")
    for apt in all_apts:
        wbs_info = f" [WBS: {apt.wbs_type}]" if apt.wbs_required else " [bez WBS]"
        print(
            f"  {apt.rooms:.0f} pok. | {apt.area_m2} m² | {apt.warm_rent} € | "
            f"{apt.district} | {apt.title}{wbs_info}"
        )

    print()
    big = [a for a in all_apts if a.rooms >= 5]
    print(f"Mieszkania >= 5 pokoi: {len(big)}")
    for apt in big:
        wbs_info = f" [WBS: {apt.wbs_type}]" if apt.wbs_required else " [bez WBS]"
        print(f"  ** {apt.rooms:.0f} pok. | {apt.area_m2} m² | {apt.warm_rent} € | {apt.title}{wbs_info}")
        print(f"     {apt.address} | {apt.district}")
        print(f"     {apt.url}")
