"""
Scraper dla howoge.de (HOWOGE Wohnungsbaugesellschaft mbH).
Metoda: POST JSON API (TYPO3 EXT:howrealestate)
Endpoint: POST /?type=999&tx_howrealestate_json_list[action]=immoList
Odpowiedz: JSON z lista mieszkan, wszystkie dane juz w odpowiedzi.
Brak potrzeby Playwright.
"""

import re
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Apartment

BASE_URL = "https://www.howoge.de"
API_URL = f"{BASE_URL}/?type=999&tx_howrealestate_json_list[action]=immoList"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/immobiliensuche/wohnungssuche.html",
}


def _parse_wbs_type(notice: str) -> str | None:
    """Wyciaga typ WBS z pola notice, np. '3-Zimmer-Wohnung (WBS 100-140)' -> 'WBS 100-140'."""
    if not notice:
        return None
    m = re.search(r"WBS\s*([\d\-/]+)", notice)
    if m:
        return f"WBS {m.group(1)}"
    return None


def _fetch_all() -> list[dict]:
    """
    Pobiera wszystkie obiekty z API.
    API zwraca wszystkie wyniki w jednym zapytaniu (niezaleznie od limit/page),
    wiec paginacja jest zbedna – wysylamy jedno zadanie z duzym limitem.
    """
    data = {
        "tx_howrealestate_json_list[page]": "1",
        "tx_howrealestate_json_list[limit]": "500",
        "tx_howrealestate_json_list[lang]": "",
    }
    resp = requests.post(API_URL, headers=HEADERS, data=data, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("immoobjects", [])


def scrape(min_rooms: float = 4.0) -> list[Apartment]:
    """
    Pobiera wszystkie mieszkania z howoge.de i filtruje po liczbie pokoi.

    Args:
        min_rooms: Minimalna liczba pokoi (domyslnie 4).

    Returns:
        Lista obiektow Apartment.
    """
    raw = _fetch_all()
    results: list[Apartment] = []

    for obj in raw:
        rooms = float(obj.get("rooms") or 0) or None

        wbs_raw = str(obj.get("wbs", "")).strip().lower()
        wbs_required = wbs_raw in ("ja", "yes", "true", "1")

        notice = obj.get("notice", "") or ""
        wbs_type = _parse_wbs_type(notice) if wbs_required else None

        link = obj.get("link", "") or ""
        url = BASE_URL + link if link.startswith("/") else link

        results.append(Apartment(
            source="howoge",
            title=obj.get("title", ""),
            address=obj.get("title", ""),   # 'title' zawiera adres np. "Streitstrasse 5, 13587 Berlin"
            district=obj.get("district", ""),
            rooms=rooms,
            area_m2=float(obj.get("area") or 0) or None,
            warm_rent=float(obj.get("rent") or 0) or None,
            cold_rent=None,
            available_from=None,
            wbs_required=wbs_required,
            wbs_type=wbs_type,
            url=url,
            extra={
                "uid": obj.get("uid"),
                "features": obj.get("features", []),
                "notice": notice.strip(),
            },
        ))

    # Filtruj po liczbie pokoi
    filtered = [a for a in results if (a.rooms or 0) >= min_rooms]
    return filtered


if __name__ == "__main__":
    print("Scrapuje howoge.de...")
    all_apts = scrape(min_rooms=1.0)  # min_rooms=1 zeby zobaczyc wszystkie
    print(f"Znaleziono lacznie {len(all_apts)} mieszkan.")

    rooms_dist: dict[float, int] = {}
    for a in all_apts:
        rooms_dist[a.rooms] = rooms_dist.get(a.rooms, 0) + 1
    print("Rozklad pokoi:", sorted(rooms_dist.items()))

    big = [a for a in all_apts if a.rooms >= 5]
    print(f"\nMieszkania >= 5 pokoi: {len(big)}")
    for apt in big:
        wbs_info = f" [WBS: {apt.wbs_type}]" if apt.wbs_required else " [bez WBS]"
        print(
            f"  {apt.rooms:.0f} pok. | {apt.area_m2} m2 | {apt.warm_rent} EUR | "
            f"{apt.district} | {apt.title}{wbs_info}"
        )
        print(f"     {apt.url}")
