"""
Scraper dla degewo.de
Wyszukuje mieszkania 5-pokojowe i oznacza, czy wymagają WBS.
"""

import re
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

from models import Apartment

BASE_URL = "https://www.degewo.de"
SEARCH_URL = f"{BASE_URL}/immosuche/"
MIN_ROOMS = 5


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

    # Szukaj konkretnego typu WBS (np. WBS 160, WBS 180, WBS 220)
    wbs_types = re.findall(r"wbs\s*(\d+)", text_lower)
    if wbs_types:
        return True, " / ".join(f"WBS {t}" for t in wbs_types)

    # Specjalne kategorie
    if "besonderer wohnbedarf" in text_lower:
        return True, "WBS – besonderer Wohnbedarf"

    return True, "WBS (typ nieokreślony)"


async def scrape_degewo(min_rooms: int = MIN_ROOMS) -> list[Apartment]:
    """
    Pobiera ogłoszenia z degewo.de i filtruje wg liczby pokoi.
    Używa Playwright do obsługi dynamicznie ładowanej treści.
    """
    apartments: list[Apartment] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="de-DE",
        )
        page = await context.new_page()

        print(f"[degewo] Otwieranie strony wyszukiwania...")
        await page.goto(SEARCH_URL, wait_until="networkidle", timeout=30000)

        # Akceptuj cookies jeśli pojawi się okno
        try:
            await page.click("button:has-text('Alle akzeptieren')", timeout=5000)
            await page.wait_for_timeout(1000)
        except PlaywrightTimeout:
            pass

        page_num = 1
        while True:
            print(f"[degewo] Przetwarzam stronę {page_num}...")
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Ogłoszenia – karty z klasą article lub immo-teaser
            # Ogłoszenia – karty z klasą article-list__item--immosearch
            listings = soup.select("article.article-list__item--immosearch")

            if not listings:
                print("[degewo] Nie znaleziono ogłoszeń na stronie.")
                break

            for item in listings:
                text_full = item.get_text(separator=" ", strip=True)

                # Liczba pokoi – ze span.text przy ikonach
                rooms_match = re.search(r"(\d+(?:[,.]\d+)?)\s*Zimmer", text_full, re.IGNORECASE)
                rooms = _parse_float(rooms_match.group(1)) if rooms_match else None

                # Filtr – tylko >= min_rooms pokoi
                if rooms is None or rooms < min_rooms:
                    continue

                # Tytuł – h2.article__title
                title_el = item.select_one("h2.article__title, h2, h3")
                title = title_el.get_text(strip=True) if title_el else "Brak tytułu"

                # Adres / dzielnica – span.article__meta  (format: "Ulica 12 | Dzielnica")
                addr_el = item.select_one("span.article__meta, .article__meta")
                address_text = addr_el.get_text(strip=True) if addr_el else ""
                parts = [p.strip() for p in address_text.split("|")]
                address = parts[0] if parts else address_text
                district = parts[-1].strip() if len(parts) > 1 else ""

                # Powierzchnia – "XX,XX m²"
                area_match = re.search(r"([\d]+[,.][\d]+|\d+)\s*m²", text_full)
                area = _parse_float(area_match.group(1)) if area_match else None

                # Ciepły czynsz – "X.XXX,XX €" po "Warmmiete" lub w liście właściwości
                warm_match = re.search(
                    r"(?:Warmmiete|warm)[:\s]*([\d.]+,\d{2})\s*€", text_full, re.IGNORECASE
                )
                if not warm_match:
                    # Szukaj dowolnej kwoty € jako ostatniej
                    all_prices = re.findall(r"([\d.]+,\d{2})\s*€", text_full)
                    warm_rent = _parse_float(all_prices[-1]) if all_prices else None
                else:
                    warm_rent = _parse_float(warm_match.group(1))

                # Dostępność
                avail_match = re.search(
                    r"ab\s+(\d{2}\.\d{2}\.\d{4}|sofort)", text_full, re.IGNORECASE
                )
                available = avail_match.group(1) if avail_match else None

                # WBS – tytuł + cały tekst
                wbs_required, wbs_type = _detect_wbs(text_full)

                # URL szczegółów
                link_el = item.select_one("a[href*='immosuche/details']")
                if not link_el:
                    link_el = item.select_one("a[href]")
                detail_url = ""
                if link_el:
                    href = link_el["href"]
                    detail_url = href if href.startswith("http") else BASE_URL + href

                apt = Apartment(
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
                )
                apartments.append(apt)

            # Następna strona – paginacja przez JavaScript (a.pager__next)
            next_btn = page.locator("a.pager__next")
            if await next_btn.count() > 0:
                await next_btn.first.click()
                await page.wait_for_load_state("networkidle", timeout=15000)
                page_num += 1
            else:
                break

        await browser.close()

    print(f"[degewo] Znaleziono {len(apartments)} mieszkań >= {min_rooms} pokoi.")
    return apartments


if __name__ == "__main__":
    results = asyncio.run(scrape_degewo(min_rooms=5))
    if results:
        print("\n=== Wyniki ===")
        for apt in results:
            print(apt)
    else:
        print("Brak wyników dla podanych kryteriów.")
