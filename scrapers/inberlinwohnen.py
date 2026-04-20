"""
Scraper inberlinwohnen.de – portal zbiorczy 7 berlińskich spoldzielni panstwowych (LWU):
  degewo, GESOBAU, Gewobag, HOWOGE, STADT UND LAND, WBM, Berlinovo

Metoda: requests + BeautifulSoup4, parsowanie snapshotów Laravel Livewire
  - Komponent 'collapsible-apartment-title' -> itemId, rooms, area, rentNet, street, district
  - Komponent 'apartment-item'              -> hasWbs, deeplink, occupationDate, firma
Brak potrzeby uzywania Playwright.
"""

import html as html_mod
import json
import re
import time

import requests
from bs4 import BeautifulSoup

from models import Apartment

BASE_URL = "https://www.inberlinwohnen.de/wohnungsfinder"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}

# Mapowanie internalName -> kolor/skrot zrodla
COMPANY_MAP = {
    "degewo":        "degewo",
    "gesobau":       "gesobau",
    "gewobag":       "gewobag",
    "howoge":        "howoge",
    "stadtundland":  "stadtundland",
    "wbm":           "wbm",
    "berlinovo":     "berlinovo",
}


def _parse_float(val: str | None) -> float | None:
    """Konwertuje europejski format liczby ('1.234,56' lub '1234.56') na float."""
    if not val:
        return None
    val = str(val).strip()
    # Format europejski: '1.251,86'
    if "," in val and "." in val:
        val = val.replace(".", "").replace(",", ".")
    elif "," in val:
        val = val.replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


def _parse_page(soup: BeautifulSoup) -> tuple[dict[int, dict], dict[int, dict]]:
    """
    Parsuje strone i zwraca dwa slowniki:
      title_map: itemId -> {rooms, area, rentNet, street, number, zipCode, district}
      apt_map:   itemId -> {hasWbs, deeplink, occupationDate, company}
    """
    title_map: dict[int, dict] = {}
    apt_map: dict[int, dict] = {}

    for el in soup.find_all(attrs={"wire:snapshot": True}):
        snap_raw = el.get("wire:snapshot", "")
        try:
            snap = json.loads(html_mod.unescape(snap_raw))
        except (json.JSONDecodeError, ValueError):
            continue

        name = snap.get("memo", {}).get("name", "")
        d = snap.get("data", {})

        if name == "apartment-finder.item.partials.collapsible-apartment-title":
            item_id = d.get("itemId")
            if item_id:
                title_map[int(item_id)] = d

        elif name == "apartment-finder.item.apartment-item":
            item_list = d.get("item", [])
            if not item_list:
                continue
            item = item_list[0]
            item_id = item.get("id")
            if item_id:
                apt_map[int(item_id)] = {
                    "hasWbs":          d.get("hasWbs", False),
                    "deeplink":        item.get("deeplink", ""),
                    "occupationDate":  item.get("occupationDate"),
                    "rent_net":        item.get("rent_net"),
                    "extra_costs":     item.get("extra_costs"),
                    "heating_costs":   item.get("heating_costs"),
                    "objectId":        item.get("objectId", ""),
                }

        elif name == "apartment-finder.item.partials.association":
            # Firma (degewo, howoge itp.) jest w komponencie association
            company_name = d.get("companyInternalName", "")
            # Przypisujemy do apt_map - ale nie znamy jeszcze itemId
            # Bedziemy matchowac po pozycji w petli (patrz nizej)
            pass

    return title_map, apt_map


def _parse_page_with_company(soup: BeautifulSoup) -> list[dict]:
    """
    Zwraca liste slownikow z pelna informacja o kazdym mieszkaniu na stronie.
    Laczenie: collapsible-title (adres) + apartment-item (WBS, deeplink) + association (firma)
    Wszystkie trzy komponenty wystepuja w tej samej kolejnosci na stronie.
    """
    titles = []
    apts = []
    companies = []

    for el in soup.find_all(attrs={"wire:snapshot": True}):
        snap_raw = el.get("wire:snapshot", "")
        try:
            snap = json.loads(html_mod.unescape(snap_raw))
        except (json.JSONDecodeError, ValueError):
            continue

        name = snap.get("memo", {}).get("name", "")
        d = snap.get("data", {})

        if name == "apartment-finder.item.partials.collapsible-apartment-title":
            titles.append(d)
        elif name == "apartment-finder.item.apartment-item":
            item_list = d.get("item", [])
            if item_list:
                item = item_list[0]
                apts.append({
                    "hasWbs":         d.get("hasWbs", False),
                    "deeplink":       item.get("deeplink", ""),
                    "occupationDate": item.get("occupationDate"),
                    "rent_net":       item.get("rent_net"),
                    "extra_costs":    item.get("extra_costs"),
                    "heating_costs":  item.get("heating_costs"),
                    "objectId":       item.get("objectId", ""),
                })
        elif name == "apartment-finder.item.partials.association":
            companies.append(d.get("companyInternalName", "unknown"))

    results = []
    for i in range(min(len(titles), len(apts), len(companies))):
        merged = {}
        merged.update(titles[i])
        merged.update(apts[i])
        merged["company"] = companies[i]
        results.append(merged)

    return results


def _to_apartment(raw: dict) -> Apartment | None:
    """Konwertuje surowy slownik na obiekt Apartment."""
    # Czynsz: rentNet z title (europejski format) lub rent_net z item (dot format)
    rent_cold = _parse_float(raw.get("rentNet")) or _parse_float(raw.get("rent_net"))
    extra = _parse_float(raw.get("extra_costs")) or 0.0
    heating = _parse_float(raw.get("heating_costs")) or 0.0
    rent_warm = (rent_cold or 0.0) + extra + heating if rent_cold else None

    rooms = _parse_float(raw.get("rooms"))
    area = _parse_float(raw.get("area"))

    street = raw.get("street", "")
    number = raw.get("number", "")
    zip_code = raw.get("zipCode", "")
    district = raw.get("district", "")
    address = f"{street} {number}, {zip_code} Berlin".strip(", ")

    occupation = raw.get("occupationDate")
    if occupation:
        # ISO -> DD.MM.YYYY
        try:
            from datetime import date
            d = date.fromisoformat(occupation[:10])
            occupation = d.strftime("%d.%m.%Y")
        except ValueError:
            pass

    deeplink = raw.get("deeplink", "")
    if not deeplink:
        return None

    company_internal = (raw.get("company") or "").lower().replace("-", "").replace(" ", "")
    source = COMPANY_MAP.get(company_internal, company_internal or "inberlinwohnen")

    wbs = bool(raw.get("hasWbs", False))
    wbs_type = None
    if wbs:
        # Proba wyciagniecia typu WBS z objectId lub deeplink
        m = re.search(r"wbs[-_\s]*(\d{2,3})", deeplink, re.IGNORECASE)
        if m:
            wbs_type = f"WBS {m.group(1)}"

    return Apartment(
        source=source,
        title=f"{rooms:.0f}-Zimmer-Wohnung" if rooms else "Wohnung",
        address=address,
        district=district,
        rooms=rooms,
        area_m2=area,
        warm_rent=round(rent_warm, 2) if rent_warm else None,
        cold_rent=round(rent_cold, 2) if rent_cold else None,
        available_from=occupation,
        wbs_required=wbs,
        wbs_type=wbs_type,
        url=deeplink,
        extra={"objectId": raw.get("objectId", ""), "portal": "inberlinwohnen.de"},
    )


def scrape(min_rooms: float = 1.0) -> list[Apartment]:
    """
    Scrapeuje wszystkie strony inberlinwohnen.de.
    Zwraca liste obiektow Apartment z wszystkich 7 spoldzielni LWU
    (bez degewo, gewobag, wbm, howoge - te sa juz scrapowane osobno).
    """
    print("[inberlinwohnen] Pobieranie ofert ze wszystkich 7 LWU...")

    apartments: list[Apartment] = []
    seen_urls: set[str] = set()
    page = 1

    # Tylko te spoldzielnie ktore NIE maja jeszcze osobnego scrapera
    SKIP_COMPANIES = {"degewo", "gewobag", "howoge", "wbm"}

    while True:
        url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"[inberlinwohnen] Blad strony {page}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        raw_list = _parse_page_with_company(soup)

        if not raw_list:
            break

        for raw in raw_list:
            apt = _to_apartment(raw)
            if apt is None:
                continue
            if apt.url in seen_urls:
                continue
            seen_urls.add(apt.url)
            # Pomijamy spoldzielnie z osobnymi scraperami
            if apt.source in SKIP_COMPANIES:
                continue
            apartments.append(apt)

        print(f"[inberlinwohnen]   str. {page}: {len(raw_list)} ofert "
              f"({len(apartments)} lacznie po filtrowaniu)")

        # Sprawdz czy jest nastepna strona
        has_next = bool(soup.find("a", attrs={"wire:click": re.compile(r"nextPage|page")}))
        # Alternatywnie - sprawdz liczbe wynikow
        results_count = 0
        for el in soup.find_all(attrs={"wire:snapshot": True}):
            try:
                snap = json.loads(html_mod.unescape(el.get("wire:snapshot", "")))
                rc = snap.get("data", {}).get("resultsCount")
                if rc is not None:
                    results_count = int(rc)
                    break
            except Exception:
                pass

        max_pages = (results_count + 9) // 10 if results_count else 30
        if page >= max_pages:
            break

        page += 1
        time.sleep(0.5)

    filtered = [a for a in apartments if a.rooms is None or a.rooms >= min_rooms]
    print(f"[inberlinwohnen] Znaleziono {len(apartments)} ofert "
          f"({len(filtered)} >= {min_rooms} pokoi) z GESOBAU/STADTUNDLAND/Berlinovo")
    return filtered


if __name__ == "__main__":
    results = scrape(min_rooms=1.0)
    print(f"\nLacznie: {len(results)} mieszkan\n")
    by_source: dict[str, list] = {}
    for a in results:
        by_source.setdefault(a.source, []).append(a)
    for src, apts in sorted(by_source.items()):
        print(f"\n--- {src.upper()} ({len(apts)}) ---")
        for a in sorted(apts, key=lambda x: -(x.rooms or 0)):
            wbs = f"WBS: {a.wbs_type}" if a.wbs_required else "bez WBS"
            rent = f"{a.warm_rent:.0f} EUR" if a.warm_rent else "?"
            print(f"  {a.rooms or '?'} pok. | {a.area_m2 or '?'} m2 | {rent} | {wbs}")
            print(f"    {a.address}")
            print(f"    {a.url}")
