"""
Generuje dokumentacje projektu w formacie PDF.
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import date


class PDF(FPDF):
    def header(self):
        self.set_fill_color(30, 80, 160)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_y(4)
        self.cell(0, 10, "Dokumentacja projektu - Wyszukiwarka mieszkan Berlin", align="C")
        self.set_text_color(0, 0, 0)
        self.ln(14)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Strona {self.page_no()} | Wygenerowano: {date.today().strftime('%d.%m.%Y')}", align="C")
        self.set_text_color(0, 0, 0)

    def section_title(self, text: str):
        self.ln(4)
        self.set_fill_color(220, 230, 245)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 9, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.ln(2)

    def subsection_title(self, text: str):
        self.ln(2)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 80, 160)
        self.cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text: str):
        self.set_font("Helvetica", "", 9)
        x = self.get_x()
        self.cell(4, 5.5, "  -")
        self.multi_cell(0, 5.5, " " + text)
        self.set_x(x)

    def code_block(self, text: str):
        self.set_fill_color(240, 240, 240)
        self.set_font("Courier", "", 8)
        self.set_draw_color(180, 180, 180)
        self.rect(self.get_x(), self.get_y(), 180, len(text.split("\n")) * 4.5 + 4, "D")
        self.set_fill_color(240, 240, 240)
        self.rect(self.get_x(), self.get_y(), 180, len(text.split("\n")) * 4.5 + 4, "F")
        self.ln(2)
        for line in text.split("\n"):
            self.cell(4)
            self.cell(0, 4.5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)
        self.set_draw_color(0, 0, 0)
        self.set_font("Helvetica", "", 9)

    def table_row(self, cols, widths, header=False):
        fill_color = (30, 80, 160) if header else (255, 255, 255)
        text_color = (255, 255, 255) if header else (0, 0, 0)
        self.set_fill_color(*fill_color)
        self.set_text_color(*text_color)
        self.set_font("Helvetica", "B" if header else "", 8)
        for col, w in zip(cols, widths):
            self.cell(w, 6.5, col, border=1, fill=header)
        self.ln()
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)

    def alt_table_row(self, cols, widths, idx):
        self.set_fill_color(245, 248, 255) if idx % 2 == 0 else self.set_fill_color(255, 255, 255)
        self.set_font("Helvetica", "", 8)
        for col, w in zip(cols, widths):
            self.cell(w, 6.5, col, border=1, fill=True)
        self.ln()
        self.set_fill_color(255, 255, 255)

    def status_badge(self, text: str, color: tuple):
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 8)
        self.cell(28, 6, text, fill=True, border=0)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)


def generate():
    pdf = PDF()
    pdf.set_margins(15, 22, 15)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # -- TYTUL -----------------------------------------------------------------
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 80, 160)
    pdf.cell(0, 12, "Wyszukiwarka mieszkan na wynajem - Berlin", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, f"Dokumentacja techniczna  |  {date.today().strftime('%d.%m.%Y')}",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)
    pdf.set_draw_color(30, 80, 160)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    # -- PODSUMOWANIE STANU ----------------------------------------------------
    pdf.section_title("Stan realizacji projektu (20.04.2026)")
    widths_s = [35, 95, 40]
    pdf.table_row(["Modul", "Metoda / Uwagi", "Status"], widths_s, header=True)
    status_rows = [
        ("degewo.de",      "Playwright + BeautifulSoup4 / TYPO3+OpenImmo",    "GOTOWY"),
        ("gewobag.de",     "WP REST API (lista) + Playwright (szczegoly)",     "GOTOWY"),
        ("wbm.de",         "requests + BeautifulSoup4 / TYPO3+OpenImmo",      "GOTOWY"),
        ("howoge.de",      "POST JSON API / TYPO3 EXT:howrealestate",         "GOTOWY"),
        ("inberlinwohnen.de", "requests + BS4 / Laravel Livewire snapshots (GESOBAU, STADT UND LAND, Berlinovo)", "GOTOWY"),
        ("db.py",          "SQLite - upsert, historia, migracja",             "GOTOWY"),
        ("notify.py",      "SMTP email HTML, Gmail App Password",             "GOTOWY"),
        ("GitHub Actions", "Cron co 30 min, DB persistence via git commit",   "GOTOWY"),
    ]
    for i, row in enumerate(status_rows):
        pdf.alt_table_row(list(row), widths_s, i)
    pdf.ln(4)

    # -- 1. CEL PROJEKTU -------------------------------------------------------
    pdf.section_title("1. Cel projektu")
    pdf.body_text(
        "Projekt ma na celu automatyczne wyszukiwanie mieszkan 5-pokojowych "
        "dostepnych do wynajecia w Berlinie na stronach internetowych czterech "
        "spoldzielni mieszkaniowych: degewo, gewobag, wbm oraz howoge.\n\n"
        "Kluczowym wymaganiem jest rozroznienie ofert wymagajacych "
        "Wohnberechtigungsschein (WBS) od ofert bez tego wymagania, "
        "z jednoczesnym identyfikowaniem kategorii WBS "
        "(np. WBS 100, WBS 140, WBS 160, WBS 180, WBS 220, WBS z besonderem Wohnbedarf)."
    )

    # -- 2. ARCHITEKTURA -------------------------------------------------------
    pdf.section_title("2. Architektura projektu")
    pdf.body_text("Projekt sklada sie z nastepujacych plikow i katalogow:")
    pdf.code_block(
        "Wyszukiwanie/\n"
        "  models.py            # Klasa danych Apartment (wspolna)\n"
        "  scrapers/\n"
        "    __init__.py\n"
        "    degewo.py           # Scraper degewo.de   [Playwright]\n"
        "    gewobag.py          # Scraper gewobag.de  [WP API + Playwright]\n"
        "    wbm.py              # Scraper wbm.de      [requests + BS4]\n"
        "    howoge.py           # Scraper howoge.de   [POST JSON API]\n"
        "    inberlinwohnen.py   # Scraper inberlinwohnen.de [Livewire / GESOBAU+STADTUNDLAND+Berlinovo]\n"
        "  main.py               # Orchestrator - uruchamia wszystkie 4 scrapery\n"
        "  db.py                 # SQLite - zapis/odczyt ogloszenia, historia\n"
        "  notify.py             # Powiadomienia email (SMTP) o nowych ogloszeniach\n"
        "  mieszkania.db         # Baza danych SQLite (sledzona przez git)\n"
        "  .env.example          # Szablon zmiennych srodowiskowych\n"
        "  requirements.txt      # Zaleznosci Python\n"
        "  .gitignore            # Wykluczenia Git\n"
        "  .github/\n"
        "    workflows/\n"
        "      scrape.yml        # GitHub Actions - cron co 30 min\n"
        "  generate_docs.py      # Skrypt generujacy te dokumentacje\n"
        "  dokumentacja.pdf      # Wygenerowana dokumentacja"
    )

    # -- 3. STOS TECHNOLOGICZNY ------------------------------------------------
    pdf.section_title("3. Stos technologiczny")
    widths = [42, 28, 100]
    pdf.table_row(["Pakiet", "Wersja", "Zastosowanie"], widths, header=True)
    rows = [
        ("playwright",     "1.58.0", "Sterowanie przegladarka Chromium - JS rendering, tabele AJAX"),
        ("beautifulsoup4", "4.14.3", "Parsowanie HTML stron (degewo, wbm)"),
        ("requests",       "2.33.1", "HTTP GET/POST do REST API (gewobag WP API, howoge JSON API)"),
        ("fpdf2",          "2.8.7",  "Generowanie raportu PDF"),
        ("sqlite3",        "wbudowany", "Baza danych SQLite - trwale przechowywanie ogloszenia (db.py)"),
        ("smtplib",        "wbudowany", "Wysylanie emaili HTML przez SMTP (notify.py)"),
        ("Python",         "3.14.3", "Jezyk implementacji (srodowisko wirtualne .venv)"),
    ]
    for i, row in enumerate(rows):
        pdf.alt_table_row(list(row), widths, i)
    pdf.ln(4)

    # -- 4. MODEL DANYCH -------------------------------------------------------
    pdf.section_title("4. Model danych - klasa Apartment (models.py)")
    pdf.body_text("Kazde ogloszenie reprezentowane jest przez obiekt dataclass Apartment:")
    widths2 = [42, 30, 98]
    pdf.table_row(["Pole", "Typ", "Opis"], widths2, header=True)
    apt_fields = [
        ("source",         "str",          "Zrodlo: 'degewo' / 'gewobag' / 'wbm' / 'howoge'"),
        ("title",          "str",          "Tytul ogloszenia"),
        ("address",        "str",          "Adres ulicy (Strasse + nr)"),
        ("district",       "str",          "Dzielnica Berlina"),
        ("rooms",          "float | None", "Liczba pokoi"),
        ("area_m2",        "float | None", "Powierzchnia w m2"),
        ("warm_rent",      "float | None", "Czynsz calkowity (Gesamtmiete) w EUR"),
        ("cold_rent",      "float | None", "Czynsz zimny (Grundmiete/Kaltmiete) w EUR"),
        ("available_from", "str | None",   "Data dostepnosci (dd.mm.rrrr lub 'sofort')"),
        ("wbs_required",   "bool",         "Czy wymagany WBS"),
        ("wbs_type",       "str | None",   "Typ WBS: 'WBS 160', 'WBS 220', 'WBS 100/140' itp."),
        ("url",            "str",          "Bezposredni link do ogloszenia"),
        ("extra",          "dict",         "Dodatkowe dane (uid, features, objektnummer, ...)"),
    ]
    for i, row in enumerate(apt_fields):
        pdf.alt_table_row(list(row), widths2, i)
    pdf.ln(4)

    # -- 5. SCRAPER DEGEWO -----------------------------------------------------
    pdf.section_title("5. Scraper degewo.de")

    pdf.subsection_title("5.1  Metoda scrapowania")
    pdf.body_text(
        "Strona degewo.de uzywa silnika TYPO3 z OpenImmo. Wyniki sa renderowane "
        "server-side, ale paginacja dziala przez jQuery submit formularza. "
        "Scraper uzywa Playwright (headless Chromium) z asyncio."
    )
    for item in [
        "URL: https://www.degewo.de/immosuche/",
        "Funkcja: async def scrape_degewo(min_rooms)",
        "Selektor kart: article.article-list__item--immosearch",
        "Paginacja: klik a.pager__next + czekanie na networkidle (7 stron)",
        "Filtr po pokojach: po stronie klienta po pobraniu wszystkich stron",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("5.2  Wyodrebniane dane")
    for item in [
        "Adres i dzielnica: span.article__meta ('Ulica nr | Dzielnica')",
        "Liczba pokoi: regex '(\\d+[,.]?\\d*) Zimmer' z tytulu/tekstu",
        "Powierzchnia: regex '(\\d+[,.]\\d+) m2'",
        "Czynsz cieplo: regex kwoty EUR",
        "Data dostepnosci: fraza 'frei ab' + data lub 'sofort'",
        "WBS: regex 'wbs\\s*(\\d+)' lub fraza 'besonderer Wohnbedarf'",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("5.3  Wyniki testowe (20.04.2026)")
    widths3 = [55, 18, 22, 40, 35]
    pdf.table_row(["Adres", "Pok.", "m2", "Czynsz calkowity", "WBS"], widths3, header=True)
    res_d = [
        ("Bismarckstrasse 17A",     "5", "99,46",  "1.504,83 EUR", "WBS 160/180/220"),
        ("Bismarckstrasse 17A",     "5", "111,18", "2.071,28 EUR", "Bez WBS"),
        ("Furstenwalder Allee 324", "5", "107,81", "2.186,38 EUR", "Bez WBS"),
    ]
    for i, row in enumerate(res_d):
        pdf.alt_table_row(list(row), widths3, i)
    pdf.ln(4)

    # -- 6. SCRAPER GEWOBAG ----------------------------------------------------
    pdf.section_title("6. Scraper gewobag.de")

    pdf.subsection_title("6.1  Architektura dwuetapowa")
    pdf.body_text(
        "Strona gewobag.de uzywa WordPress jako CMS. Dane sa ladowane przez "
        "JavaScript z zewnetrznego systemu. Wymagana jest architektura dwuetapowa:"
    )
    for item in [
        "Etap 1: WordPress REST API (/wp-json/wp/v2/immobilien) - lista wszystkich "
        "ofert w formacie JSON, bez Playwright, bardzo szybko.",
        "Etap 2: Playwright (headless Chromium) - ladowanie strony szczegolów "
        "kazdej oferty i odczyt tabeli z danymi po wyrenderowaniu JS.",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("6.2  Etap 1 - WordPress REST API")
    pdf.body_text("Endpoint: https://www.gewobag.de/wp-json/wp/v2/immobilien")
    pdf.code_block(
        "GET /wp-json/wp/v2/immobilien?per_page=100&page=N\n"
        "  &_fields=id,slug,link,title,class_list\n\n"
        "Odpowiedz JSON - kazdy wpis zawiera class_list:\n"
        "  ['objekttyp-wohnung', 'wohnungstyp-wbs-220',\n"
        "   'bezirke-spandau-haselhorst', ...]\n\n"
        "Filtrowanie:  class 'objekttyp-wohnung' musi byc obecna\n"
        "WBS:          class 'wohnungstyp-wbs' lub 'wohnungstyp-wbs-220' itp.\n"
        "Dzielnica:    class 'bezirke-<district>-<ortsteil>'\n"
        "Paginacja:    naglowek X-WP-TotalPages"
    )

    pdf.subsection_title("6.3  Etap 2 - Playwright, tabela szczegolów")
    for item in [
        "Rownoleglosc: 3 strony jednoczesnie (asyncio.Semaphore)",
        "Anzahl Zimmer  -> rooms",
        "Flache in m2   -> area_m2",
        "Grundmiete     -> cold_rent",
        "Gesamtmiete    -> warm_rent",
        "Anschrift      -> address",
        "Bezirk/Ortsteil -> district",
        "Frei ab        -> available_from",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("6.4  Wydajnosc")
    for item in [
        "Etap 1 (API): ~5 sek. - 7 stron * 100 wpisow = 648 wpisow lacznie",
        "Po filtrowaniu (tylko objekttyp-wohnung): 52 mieszkania",
        "Etap 2 (Playwright, rownoleglosc 3): ~2-3 minuty dla 52 stron",
        "Laczny czas: ok. 2-3 minuty",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("6.5  Wyniki testowe (20.04.2026)")
    pdf.body_text("Mieszkania z co najmniej 5 pokojami (7 znalezionych):")
    widths_g = [60, 14, 22, 38, 36]
    pdf.table_row(["Adres", "Pok.", "m2", "Czynsz calkowity", "WBS"], widths_g, header=True)
    res_g = [
        ("Daumstr. 66, 13599 Berlin",          "5", "95,16",  "1.570,14 EUR", "WBS"),
        ("Rotfederstrasse 64, 13599 Berlin",    "5", "95,74",  "1.464,83 EUR", "WBS"),
        ("Daumstr. 74, 13599 Berlin",           "5", "98,25",  "2.038,60 EUR", "Bez WBS"),
        ("Daumstr. 66, 13599 Berlin",           "5", "95,16",  "1.570,14 EUR", "WBS"),
        ("Wendenschlossstr. 160, 12557 Berlin", "5", "100,01", "1.530,10 EUR", "WBS"),
        ("Daumstr. 76A, 13599 Berlin",          "5", "111,67", "2.318,54 EUR", "Bez WBS"),
        ("(brak danych tabeli JS)",             "?", "?",      "?",            "Bez WBS"),
    ]
    for i, row in enumerate(res_g):
        pdf.alt_table_row(list(row), widths_g, i)
    pdf.ln(4)

    # -- 7. SCRAPER WBM --------------------------------------------------------
    pdf.section_title("7. Scraper wbm.de")

    pdf.subsection_title("7.1  Metoda scrapowania")
    pdf.body_text(
        "Strona wbm.de (Wohnungsbaugesellschaft Berlin-Mitte) uzywa TYPO3 z "
        "rozszerzeniem OpenImmo. Strona jest renderowana server-side - "
        "nie wymaga Playwright. Scraper uzywa tylko requests + BeautifulSoup4."
    )
    for item in [
        "URL: https://www.wbm.de/wohnungen-berlin/angebote/",
        "Funkcja: def scrape(min_rooms)",
        "Paginacja: GET ?tx_openimmo_immobilie[page]=N",
        "Selektor wiersza: div.row.openimmo-search-list-item",
        "Karta danych: article.immo-element zawierajacy h2.imageTitle (drugi article w wierszu)",
        "Karta zdjecia: article.teaserBox.immo-element (pierwszy - zawiera div.area z dzielnica)",
        "Brak potrzeby Playwright - wszystkie dane w HTML",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("7.2  Wyodrebniane dane")
    widths_w = [48, 122]
    pdf.table_row(["Pole", "Selektor / metoda"], widths_w, header=True)
    wbm_fields = [
        ("Tytul",    "h2.imageTitle"),
        ("Adres",    "div.address"),
        ("Pokoje",   ".main-property-rooms (text -> float)"),
        ("Metraz",   ".main-property-size (strip 'm2')"),
        ("Czynsz",   ".main-property-rent (format europejski: 1.535,43)"),
        ("WBS",      "'WBS' in [li.text for li in .check-property-list li]"),
        ("Typ WBS",  "regex r'WBS\\s*([\\d/]+)' z tytulu"),
        ("Dzielnica","div.area w rodzicielskim div.row (element teaserBox)"),
        ("URL",      "a.immo-button-cta[href], prepend 'https://www.wbm.de'"),
    ]
    for i, row in enumerate(wbm_fields):
        pdf.alt_table_row(list(row), widths_w, i)
    pdf.ln(2)

    pdf.subsection_title("7.3  Wyniki testowe (20.04.2026)")
    pdf.body_text(
        "WBM oferuje aktualnie 7 mieszkan (1-3 pokojowe). "
        "Brak ofert >= 5 pokoi w dniu testowania."
    )
    widths_wt = [55, 18, 22, 40, 35]
    pdf.table_row(["Adres", "Pok.", "m2", "Czynsz (Warmmiete)", "WBS"], widths_wt, header=True)
    res_w = [
        ("Friedenstrasse 90, 10249 Berlin", "2", "44",  "443,69 EUR",  "WBS 100/140"),
        ("Friedenstrasse 90, 10249 Berlin", "2", "47",  "1.218 EUR",   "Bez WBS"),
        ("Grumbkowstr. 2, 13187 Berlin",    "2", "59",  "1.257 EUR",   "Bez WBS"),
        ("Pepitapromenade 29, 13587 Berlin","2", "61",  "1.021 EUR",   "Bez WBS"),
        ("Friedenstrasse 90, 10249 Berlin", "2", "62",  "1.562 EUR",   "Bez WBS"),
        ("Pepitapromenade 9, 13587 Berlin", "3", "84",  "1.535 EUR",   "Bez WBS"),
        ("Pepitapromenade 9, 13587 Berlin", "3", "91",  "1.557 EUR",   "Bez WBS"),
    ]
    for i, row in enumerate(res_w):
        pdf.alt_table_row(list(row), widths_wt, i)
    pdf.ln(4)

    # -- 8. SCRAPER HOWOGE -----------------------------------------------------
    pdf.section_title("8. Scraper howoge.de")

    pdf.subsection_title("8.1  Metoda scrapowania")
    pdf.body_text(
        "Strona howoge.de uzywa TYPO3 z rozszerzeniem EXT:howrealestate. "
        "Formularz wyszukiwania wysyla dane POST pod specjalny endpoint TYPO3 "
        "(?type=999) zwracajacy czysty JSON ze wszystkimi wynikami. "
        "Brak potrzeby Playwright - jedno zapytanie HTTP zwraca wszystkie dane."
    )
    pdf.code_block(
        "POST https://www.howoge.de/?type=999\n"
        "     &tx_howrealestate_json_list[action]=immoList\n\n"
        "Body (form-urlencoded):\n"
        "  tx_howrealestate_json_list[page]  = 1\n"
        "  tx_howrealestate_json_list[limit] = 500\n"
        "  tx_howrealestate_json_list[lang]  = (pusty)\n\n"
        "Naglowki:\n"
        "  Content-Type: application/x-www-form-urlencoded; charset=UTF-8\n"
        "  X-Requested-With: XMLHttpRequest"
    )
    pdf.ln(2)

    pdf.subsection_title("8.2  Struktura odpowiedzi JSON")
    pdf.body_text("Kazdy obiekt w tablicy 'immoobjects' zawiera:")
    widths_h = [30, 25, 115]
    pdf.table_row(["Pole JSON", "Typ", "Opis / Mapowanie -> Apartment"], widths_h, header=True)
    howoge_fields = [
        ("uid",        "int",    "Identyfikator oferty -> extra['uid']"),
        ("title",      "str",    "Adres: 'Streitstrasse 5, 13587 Berlin' -> address + title"),
        ("district",   "str",    "Dzielnica np. 'Hakenfelde' -> district"),
        ("rent",       "int",    "Czynsz calkowity (Warmmiete) w EUR -> warm_rent"),
        ("area",       "int",    "Powierzchnia w m2 -> area_m2"),
        ("rooms",      "int",    "Liczba pokoi -> rooms"),
        ("wbs",        "str",    "'ja' / 'nein' -> wbs_required (bool)"),
        ("notice",     "str",    "Opis np. '3-Zimmer-Wohnung (WBS 100-140)' -> wbs_type"),
        ("features",   "list",   "Lista cech ['WBS erforderlich', 'Aufzug', ...] -> extra"),
        ("link",       "str",    "Wzgledny URL -> url (prepend howoge.de)"),
        ("coordinates","dict",   "lat/lng -> nie uzywane"),
    ]
    for i, row in enumerate(howoge_fields):
        pdf.alt_table_row(list(row), widths_h, i)
    pdf.ln(2)

    pdf.subsection_title("8.3  Wydajnosc")
    for item in [
        "Jedno zapytanie POST zwraca wszystkie wyniki (API ignoruje parametr limit/page)",
        "Czas wykonania: < 2 sekundy",
        "Lacznie ofert: 47 (wg stanu na 20.04.2026)",
        "Rozklad pokoi: 1 pok. x9, 2 pok. x18, 3 pok. x15, 4 pok. x5",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("8.4  Wyniki testowe (20.04.2026)")
    pdf.body_text(
        "Howoge aktualnie nie oferuje mieszkan >= 5 pokoi. "
        "Przykladowe oferty 4-pokojowe:"
    )
    widths_ht = [55, 18, 22, 40, 35]
    pdf.table_row(["Adres", "Pok.", "m2", "Czynsz (Warmmiete)", "WBS"], widths_ht, header=True)
    res_h = [
        ("Streitstrasse 5, 13587 Berlin",  "3", "73", "803 EUR",  "WBS (ja)"),
        ("Landsberger Allee (przyklad)",   "4", "89", "1.100 EUR","Bez WBS"),
        ("(max. 4 pokoje w tej dacie)",    "-", "-",  "-",        "-"),
    ]
    for i, row in enumerate(res_h):
        pdf.alt_table_row(list(row), widths_ht, i)
    pdf.ln(4)

    # -- 9. SCRAPER inberlinwohnen.de ------------------------------------------
    pdf.section_title("9. Scraper inberlinwohnen.de (GESOBAU + STADT UND LAND + Berlinovo)")

    pdf.subsection_title("9.1  Metoda scrapowania")
    pdf.body_text(
        "Scraper korzysta z bibliotek requests + BeautifulSoup4. Portal inberlinwohnen.de "
        "uzywa frameworka Laravel Livewire (PHP) - dane mieszkan sa przechowywane w atrybutach "
        "wire:snapshot jako JSON osadzony w HTML, a nie pobierane przez API REST."
    )
    pdf.ln(2)

    pdf.subsection_title("9.2  Parsowanie komponentow Livewire")
    pdf.body_text(
        "Kazde mieszkanie sklada sie z trojki komponentow Livewire w tej samej kolejnosci:"
    )
    for item in [
        "collapsible-apartment-title: itemId, rooms, area, rentNet, street, district",
        "apartment-item: hasWbs, deeplink, occupationDate, rent_net / rent_extra / heating",
        "association: companyInternalName (gesobau / stadtundland / berlinovo)",
    ]:
        pdf.bullet(item)
    pdf.body_text(
        "Paginacja: parametr ?page=N, zatrzymuje sie gdy page >= ceil(resultsCount / 10). "
        "Przy 204 wynikach = 21 stron."
    )
    pdf.ln(2)

    pdf.subsection_title("9.3  Pomijanie duplikatow - SKIP_COMPANIES")
    pdf.body_text(
        "inberlinwohnen.de agreguje oferty wszystkich 7 LWU, w tym degewo, gewobag, wbm i howoge, "
        "ktore sa juz objete dedykowanymi scraperami. Aby uniknac duplikatow w bazie danych, "
        "scraper filtruje te zrodla:"
    )
    pdf.code_block(
        "SKIP_COMPANIES = {\"degewo\", \"gewobag\", \"howoge\", \"wbm\"}\n"
        "# Zwraca tylko: gesobau, stadtundland, berlinovo"
    )
    pdf.ln(2)

    pdf.subsection_title("9.4  Wydajnosc")
    pdf.body_text(
        "Czas wykonania: ~36 sekund dla 204 ofert (21 stron x 10 pozycji). "
        "Nie wymaga Playwright - brak JavaScript do wykonania. "
        "Requests + BS4 jest wystarczajace do odczytu wire:snapshot z HTML."
    )
    pdf.ln(2)

    pdf.subsection_title("9.5  Wyniki testowe (20.04.2026, min 5 pokoi)")
    widths_ib = [50, 10, 12, 22, 44, 30]
    pdf.table_row(
        ["Adres", "Pok.", "m2", "Czynsz", "Spoldzielnia", "WBS"],
        widths_ib, header=True
    )
    res_ib = [
        ("Hadlichstrasse 24a, Pankow", "5", "155", "2090 EUR", "GESOBAU AG", "Bez WBS"),
    ]
    for i, row in enumerate(res_ib):
        pdf.alt_table_row(list(row), widths_ib, i)
    pdf.body_text(
        "Wyniki STADT UND LAND i Berlinovo: brak ofert >= 5 pokoi w tej dacie. "
        "Lacznie scraper zwrocil 19 ofert po filtrowaniu SKIP_COMPANIES (6 GESOBAU + 13 STADT UND LAND + 0 Berlinovo), "
        "z czego 1 spelniala kryterium >= 5 pokoi."
    )
    pdf.ln(4)

    # -- 10. ORCHESTRATOR main.py ----------------------------------------------
    pdf.section_title("10. Orchestrator - main.py")

    pdf.subsection_title("10.1  Dzialanie")
    pdf.body_text(
        "main.py uruchamia wszystkie 5 scraperow rownoczesnie w oddzielnych watkach "
        "(ThreadPoolExecutor, max_workers=5). Scrapery asynchroniczne (degewo, gewobag) "
        "sa owijane przez asyncio.run() wewnatrz watku."
    )
    pdf.code_block(
        "# Uruchomienie z domyslnym filtrem >= 5 pokoi:\n"
        "python main.py\n\n"
        "# Uruchomienie z innym progiem (np. 4 pokoje):\n"
        "python main.py 4"
    )
    pdf.ln(2)

    pdf.subsection_title("10.2  Schemat dzialania")
    for item in [
        "Importuje dynamicznie kazdy modul scrapera (importlib.import_module)",
        "Uruchamia scrapery rownoczesnie - howoge, wbm i inberlinwohnen konczy sie w < 40 sek.",
        "degewo (Playwright) i gewobag (Playwright) dzialaja rownoleglo ~2-3 min",
        "inberlinwohnen.de: requests + BS4 (Laravel Livewire snapshots), bez Playwright",
        "Wyniki sa zbierane i wyswietlane po zakonczeniu wszystkich scraperow",
        "Sortowanie: najpierw oferty bez WBS, potem z WBS; malejaco po pokojach",
        "inberlinwohnen pomija degewo/gewobag/wbm/howoge (te maja osobne scrapery)",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("10.3  Podsumowanie wynikow (20.04.2026, min 5 pokoi)")
    widths_m = [38, 18, 18, 18, 76]
    pdf.table_row(["Zrodlo", "Bez WBS", "Z WBS", "Razem", "Uwagi"], widths_m, header=True)
    main_rows = [
        ("degewo.de",         "2", "1", "3",  "5-pok. Spandau/Friedrichshagen"),
        ("gewobag.de",        "2", "4", "6",  "5-pok. Spandau/Treptow-Koepenick"),
        ("wbm.de",            "0", "0", "0",  "Brak ofert >= 5 pok. (max 3 pok.)"),
        ("howoge.de",         "0", "0", "0",  "Brak ofert >= 5 pok. (max 4 pok.)"),
        ("inberlinwohnen.de", "1", "0", "1",  "GESOBAU 5-pok. Pankow (155 m2, 2090 EUR)"),
        ("RAZEM",             "5", "5", "10", "~2 minuty calkowitego czasu"),
    ]
    for i, row in enumerate(main_rows):
        pdf.alt_table_row(list(row), widths_m, i)
    pdf.ln(4)

    # -- 10. BAZA DANYCH db.py ------------------------------------------------
    pdf.section_title("11. Baza danych - db.py (SQLite)")

    pdf.subsection_title("11.1  Cel i technologia")
    pdf.body_text(
        "Modul db.py zapewnia trwale przechowywanie ogloszenia w lokalnej bazie "
        "SQLite (plik mieszkania.db). Baza jest sledzona przez git - po kazdym "
        "uruchomieniu GitHub Actions commituje zaktualizowany plik z powrotem do "
        "repozytorium, dzieki czemu historia ogloszenia nigdy nie wygasa."
    )
    pdf.ln(1)

    pdf.subsection_title("11.2  Tabele")
    widths_db = [42, 30, 98]
    pdf.table_row(["Tabela", "Klucz glowny", "Opis"], widths_db, header=True)
    db_tables = [
        ("apartments",   "url (UNIQUE)",  "Upsert po URL; pola: first_seen_at, last_seen_at, last_updated_at"),
        ("scrape_runs",  "id (auto)",     "Historia uruchomien: found_total, new, updated, removed, bledy"),
    ]
    for i, row in enumerate(db_tables):
        pdf.alt_table_row(list(row), widths_db, i)
    pdf.ln(2)

    pdf.subsection_title("11.3  Kluczowe funkcje")
    widths_dbf = [52, 118]
    pdf.table_row(["Funkcja", "Dzialanie"], widths_dbf, header=True)
    db_funcs = [
        ("init_db()",                    "Tworzy tabele jesli nie istnieja; migracja (ALTER TABLE)"),
        ("save_apartments(source, apts)","INSERT OR REPLACE upsert; zwraca (nowe_apt, updated_count)"),
        ("remove_inactive(src, urls)",   "Usuwa rekordy zrodla, ktorych URL nie ma na liscie aktywnych"),
        ("start_run() / finish_run()",   "Rejestruje uruchomienie w tabeli scrape_runs"),
        ("print_stats()",                "Wypisuje liczby ogloszenia per zrodlo i ostatnie uruchomienia"),
        ("query_apartments(**filtry)",   "Zapytanie z filtrami: min_rooms, source, wbs_required"),
    ]
    for i, row in enumerate(db_funcs):
        pdf.alt_table_row(list(row), widths_dbf, i)
    pdf.ln(2)

    pdf.subsection_title("11.4  Zmienna srodowiskowa DB_PATH")
    pdf.body_text(
        "Domyslna sciezka do bazy to mieszkania.db w katalogu projektu. "
        "Mozna ja nadpisac zmienna srodowiskowa DB_PATH - przydatne np. gdy baza "
        "ma byc przechowywana w innym katalogu niz glowny katalog projektu."
    )
    pdf.code_block(
        "# Uzycie domyslnej sciezki:\n"
        "python main.py\n\n"
        "# Uzycie niestandardowej sciezki:\n"
        "DB_PATH=/data/mieszkania.db python main.py"
    )
    pdf.ln(4)

    # -- 11. POWIADOMIENIA notify.py -------------------------------------------
    pdf.section_title("12. Powiadomienia email - notify.py")

    pdf.subsection_title("14.1  Cel i technologia")
    pdf.body_text(
        "Modul notify.py wysyla email HTML przez SMTP gdy scraper znajdzie nowe "
        "ogloszenia (nieobecne wczesniej w bazie danych). Uzywa wbudowanego modulu "
        "smtplib - brak dodatkowych zaleznosci. Obsluguje Gmail App Password."
    )
    pdf.ln(1)

    pdf.subsection_title("14.2  Struktura emaila HTML")
    pdf.body_text(
        "Email jest podzielony na dwie osobne sekcje, dzieki czemu oferty bez WBS "
        "sa od razu widoczne na gorze bez koniecznosci przeszukiwania listy:"
    )
    for item in [
        "Naglowek: liczba wszystkich ofert + liczniki 'bez WBS: X | z WBS: Y'",
        "Sekcja 1 (zielona) - Bez WBS: oferty niewymagajace Wohnberechtigungsschein",
        "Sekcja 2 (czerwona) - Wymagany WBS: oferty z wymogiem WBS (z typem np. WBS 160)",
        "Kazda sekcja renderuje sie tylko jesli zawiera oferty (brak pustych tabel)",
        "W obu sekcjach oferty posortowane wg zrodla, malejaco po liczbie pokoi",
        "Naprzemienne tlo wierszy (biale / jasnoszare) dla czytelnosci",
        "Wersja tekstowa (fallback) rowniez podzielona na == BEZ WBS == i == WYMAGANY WBS ==",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("14.3  Przykladowy wyglad emaila")
    pdf.body_text("Ponizej przedstawiono przykladowy wyglad wiadomosci email dla 5 nowych ofert (2 bez WBS, 3 z WBS):")
    pdf.ln(1)

    # --- Mock email card ---
    lm = pdf.l_margin
    card_w = 180
    card_x = lm

    # Naglowek emaila (ciemny)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_draw_color(44, 62, 80)
    pdf.rect(card_x, pdf.get_y(), card_w, 16, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(card_x + 4, pdf.get_y() + 2)
    pdf.cell(0, 5, "Nowe oferty mieszkan w Berlinie", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_x(card_x + 4)
    pdf.cell(0, 5, "Znaleziono 5 nowych ofert  |  bez WBS: 2   z WBS: 3", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)

    # Sekcja 1 – Bez WBS (zielona)
    pdf.set_fill_color(39, 174, 96)
    pdf.set_draw_color(39, 174, 96)
    pdf.rect(card_x, pdf.get_y(), 3, 8, "F")
    pdf.set_draw_color(200, 200, 200)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(39, 174, 96)
    pdf.set_x(card_x + 6)
    pdf.cell(0, 8, "Bez WBS  (2 oferty)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    # Naglowek tabeli
    pdf.set_fill_color(236, 240, 241)
    pdf.set_font("Helvetica", "B", 7)
    for col, w in zip(["Zrodlo", "Oferta / Adres", "Dzielnica", "Pok.", "Metraz", "Czynsz", "WBS", "Wolne od"],
                      [18, 50, 22, 10, 16, 20, 22, 22]):
        pdf.cell(w, 5.5, col, border=1, fill=True)
    pdf.ln()

    # Wiersze bez WBS
    mock_no_wbs = [
        ("DEGEWO",  "#2980b9", "Neubau Altstadt Spandau / Bismarckstr. 17A",  "Spandau",              "5", "111 m2", "2 071 EUR", "bez WBS", "sofort"),
        ("GEWOBAG", "#8e44ad", "Geraumige Dachwohnung / Daumstr. 76A Berlin",  "Spandau",              "5", "112 m2", "2 319 EUR", "bez WBS", "01.04.2026"),
    ]
    for idx, (src, src_col, addr, district, rooms, area, rent, wbs, avail) in enumerate(mock_no_wbs):
        bg = (250, 250, 250) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        # source badge
        r, g, b = int(src_col[1:3], 16), int(src_col[3:5], 16), int(src_col[5:7], 16)
        pdf.set_fill_color(r, g, b)
        pdf.cell(18, 6, src, border=1, fill=True)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.cell(50, 6, addr,     border=1, fill=True)
        pdf.cell(22, 6, district, border=1, fill=True)
        pdf.cell(10, 6, rooms,    border=1, fill=True, align="C")
        pdf.cell(16, 6, area,     border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.cell(20, 6, rent,     border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_fill_color(39, 174, 96)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(22, 6, wbs,  border=1, fill=True, align="C")
        pdf.set_fill_color(*bg)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(22, 6, avail, border=1, fill=True)
        pdf.ln()
    pdf.ln(3)

    # Sekcja 2 – Wymagany WBS (czerwona)
    pdf.set_fill_color(231, 76, 60)
    pdf.rect(card_x, pdf.get_y(), 3, 8, "F")
    pdf.set_draw_color(200, 200, 200)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(231, 76, 60)
    pdf.set_x(card_x + 6)
    pdf.cell(0, 8, "Wymagany WBS  (3 oferty)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    # Naglowek tabeli
    pdf.set_fill_color(236, 240, 241)
    pdf.set_font("Helvetica", "B", 7)
    for col, w in zip(["Zrodlo", "Oferta / Adres", "Dzielnica", "Pok.", "Metraz", "Czynsz", "WBS", "Wolne od"],
                      [18, 50, 22, 10, 16, 20, 22, 22]):
        pdf.cell(w, 5.5, col, border=1, fill=True)
    pdf.ln()

    # Wiersze z WBS
    mock_wbs = [
        ("DEGEWO",  "#2980b9", "WBS 220 - Neubau Altstadt / Bismarckstr. 17A",  "Spandau",           "5", "99 m2",  "1 505 EUR", "WBS 160/180/220", "sofort"),
        ("GEWOBAG", "#8e44ad", "Neubau Fussbodenhzg. / Rotfederstr. 64 Berlin",  "Reinickendorf",     "5", "96 m2",  "1 465 EUR", "WBS 220",         "01.04.2026"),
        ("GEWOBAG", "#8e44ad", "Neubau an der Dahme / Wendenschlossstr. 160",    "Treptow-Koepenick", "5", "100 m2", "1 530 EUR", "WBS 160/180/220", "01.04.2026"),
    ]
    for idx, (src, src_col, addr, district, rooms, area, rent, wbs, avail) in enumerate(mock_wbs):
        bg = (250, 250, 250) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        r, g, b = int(src_col[1:3], 16), int(src_col[3:5], 16), int(src_col[5:7], 16)
        pdf.set_fill_color(r, g, b)
        pdf.cell(18, 6, src, border=1, fill=True)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.cell(50, 6, addr,     border=1, fill=True)
        pdf.cell(22, 6, district, border=1, fill=True)
        pdf.cell(10, 6, rooms,    border=1, fill=True, align="C")
        pdf.cell(16, 6, area,     border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.cell(20, 6, rent,     border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_fill_color(231, 76, 60)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(22, 6, wbs,  border=1, fill=True, align="C")
        pdf.set_fill_color(*bg)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(22, 6, avail, border=1, fill=True)
        pdf.ln()

    # Stopka emaila
    pdf.set_fill_color(236, 240, 241)
    pdf.set_draw_color(236, 240, 241)
    pdf.rect(card_x, pdf.get_y(), card_w, 7, "F")
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.set_x(card_x + 4)
    pdf.cell(0, 7, "Wiadomosc wygenerowana automatycznie przez wyszukiwarke mieszkan Berlin.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)
    pdf.ln(4)

    pdf.subsection_title("13.4  Zmienne srodowiskowe")
    widths_n = [52, 20, 98]
    pdf.table_row(["Zmienna", "Wymagana", "Opis / Wartosc domyslna"], widths_n, header=True)
    notify_vars = [
        ("NOTIFY_SMTP_HOST",     "nie", "Serwer SMTP  (domyslnie: smtp.gmail.com)"),
        ("NOTIFY_SMTP_PORT",     "nie", "Port SMTP    (domyslnie: 587)"),
        ("NOTIFY_SMTP_USER",     "tak", "Login SMTP / adres nadawcy"),
        ("NOTIFY_SMTP_PASSWORD", "tak", "Haslo SMTP / Gmail App Password"),
        ("NOTIFY_TO",            "tak", "Adresy odbiorcow oddzielone przecinkami"),
    ]
    for i, row in enumerate(notify_vars):
        pdf.alt_table_row(list(row), widths_n, i)
    pdf.ln(2)

    pdf.subsection_title("12.5  Jak skonfigurowac Gmail App Password")
    for item in [
        "Wejdz na: myaccount.google.com/apppasswords",
        "Nazwa aplikacji: np. 'Berlin Scraper', kliknij 'Utworz'",
        "Skopiuj 16-znakowe haslo (format: xxxx xxxx xxxx xxxx)",
        "NOTIFY_SMTP_USER = twoj.adres@gmail.com",
        "NOTIFY_SMTP_PASSWORD = wygenerowane haslo aplikacji (bez spacji)",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("12.6  Testowanie lokalne")
    pdf.code_block(
        "# Plik .env (na podstawie .env.example):\n"
        "NOTIFY_SMTP_USER=twoj@gmail.com\n"
        "NOTIFY_SMTP_PASSWORD=xxxxxxxxxxxx\n"
        "NOTIFY_TO=odbiorca@example.com\n\n"
        "# Wczytaj .env i uruchom (Windows PowerShell):\n"
        "Get-Content .env | ForEach-Object {\n"
        "  if ($_ -match '^([^#=]+)=(.*)$') {\n"
        "    [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim())\n"
        "  }\n"
        "}\n"
        "python main.py"
    )
    pdf.ln(2)

    pdf.subsection_title("12.7  Zabezpieczenie danych wrazliwych")
    pdf.body_text(
        "Dane dostepowe (haslo SMTP, adres email) nigdy nie powinny trafic do "
        "repozytorium git. Ponizej opisane sa wszystkie warstwy zabezpieczen stosowane "
        "w projekcie."
    )
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Lokalnie - plik .env", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for item in [
        "Plik .env przechowuje dane dostepowe lokalnie - jest w .gitignore (nigdy nie trafia do git)",
        "Szablon .env.example (bez hasel) jest w repo - sluzy jako dokumentacja zmiennych",
        "Opcjonalnie: pip install python-dotenv, a nastepnie dodac 'from dotenv import load_dotenv;"
        " load_dotenv()' na poczatku main.py - automatyczne wczytanie .env",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "GitHub Actions - GitHub Secrets", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for item in [
        "Sekrety sa zaszyfrowane po stronie GitHub i nigdy nie pojawiaja sie w logach",
        "Sciezka: repo -> Settings -> Secrets and variables -> Actions -> New repository secret",
        "W scrape.yml odczytywane przez ${{ secrets.NAZWA }} - nie ma ich w kodzie",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Gmail App Password - ograniczone uprawnienia", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for item in [
        "App Password nie daje dostepu do skrzynki odbiorczej - tylko do wysylania przez SMTP",
        "Mozna je uniewaznic w dowolnej chwili: myaccount.google.com/apppasswords",
        "Nawet jesli wycieknie - nie kompromituje calego konta Google",
        "Wymagane: wlaczona weryfikacja dwuetapowa (2FA) na koncie Gmail",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Weryfikacja - co NIE trafia do git", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.code_block(
        "# Sprawdz czy .env przypadkowo nie jest sledzony:\n"
        "git ls-files .env        # powinno zwrocic puste wyjscie\n"
        "git status               # .env nie powinien pojawiac sie na liscie\n\n"
        "# Jesli .env pojawil sie kiedys w historii git - zmien haslo (App Password)\n"
        "# i wygeneruj nowe. Opcjonalnie usun z historii przez git filter-repo:\n"
        "pip install git-filter-repo\n"
        "git filter-repo --path .env --invert-paths"
    )
    pdf.ln(4)

    # -- 12. GITHUB ACTIONS ----------------------------------------------------
    pdf.section_title("13. Wdrozenie - GitHub Actions")

    pdf.subsection_title("14.1  Harmonogram i architektura")
    pdf.body_text(
        "Plik .github/workflows/scrape.yml definiuje workflow uruchamiany "
        "automatycznie co 30 minut (cron) oraz recznie z poziomu GitHub UI. "
        "Baza danych mieszkania.db jest sledzona przez git - po kazdym uruchomieniu "
        "bot commituje zaktualizowany plik z powrotem do repozytorium "
        "(commit message: 'chore: update DB [skip ci]' zapobiega petli triggerow)."
    )
    for item in [
        "Runner: ubuntu-latest, timeout: 20 minut",
        "Jednoczesnosc: concurrency: group: scraper (brak rownoleglosci)",
        "Uprawnienia: contents: write (potrzebne do git push)",
        "Python: 3.12 z cache pip (szybszy start)",
        "Playwright: chromium --with-deps (automatyczna instalacja systemowych zaleznosci)",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("14.2  Kroki workflow")
    widths_ga = [52, 118]
    pdf.table_row(["Krok", "Opis"], widths_ga, header=True)
    ga_steps = [
        ("Checkout kodu",         "actions/checkout@v4 - pobiera kod + mieszkania.db z repo"),
        ("Ustaw Python 3.12",     "actions/setup-python@v5 z cache pip"),
        ("Zainstaluj zaleznosci", "pip install -r requirements.txt"),
        ("Playwright Chromium",   "playwright install chromium --with-deps"),
        ("Uruchom scraper",       "python main.py MIN_ROOMS (sekrety SMTP z GitHub Secrets)"),
        ("Statystyki bazy",       "python -c 'import db; db.init_db(); db.print_stats()'"),
        ("Zapisz DB do repo",     "git add mieszkania.db && git commit && git push (if: always())"),
    ]
    for i, row in enumerate(ga_steps):
        pdf.alt_table_row(list(row), widths_ga, i)
    pdf.ln(2)

    pdf.subsection_title("14.3  Schemat krolow do uruchomienia")
    pdf.code_block(
        "# Krok 1 - Inicjalizacja repozytorium:\n"
        "git init\n"
        "git add .\n"
        "git commit -m 'Initial commit'\n\n"
        "# Krok 2 - Polacz z GitHub i wgraj:\n"
        "git remote add origin https://github.com/LOGIN/REPO.git\n"
        "git push -u origin main\n\n"
        "# Krok 3 - Pierwsze uruchomienie (tworzy mieszkania.db):\n"
        "Actions -> Scraper mieszkan Berlin -> Run workflow"
    )
    pdf.ln(2)

    pdf.subsection_title("13.4  GitHub Secrets (Settings > Secrets > Actions)")
    widths_sec = [52, 20, 98]
    pdf.table_row(["Secret", "Wymagany", "Opis"], widths_sec, header=True)
    secrets = [
        ("NOTIFY_SMTP_USER",     "tak", "Login SMTP / adres Gmail nadawcy"),
        ("NOTIFY_SMTP_PASSWORD", "tak", "Gmail App Password (16 znakow)"),
        ("NOTIFY_TO",            "tak", "Adresy odbiorcow oddzielone przecinkami"),
        ("NOTIFY_SMTP_HOST",     "nie", "Serwer SMTP (domyslnie smtp.gmail.com)"),
        ("NOTIFY_SMTP_PORT",     "nie", "Port SMTP (domyslnie 587)"),
    ]
    for i, row in enumerate(secrets):
        pdf.alt_table_row(list(row), widths_sec, i)
    pdf.ln(4)

    # -- 13. INSTALACJA I URUCHOMIENIE ----------------------------------------
    pdf.section_title("14. Instalacja i uruchomienie lokalne")

    pdf.subsection_title("14.1  Wymagania wstepne")
    for item in [
        "Python 3.10+ (testowane na 3.14.3)",
        "Windows / Linux / macOS",
        "Polaczenie z internetem",
    ]:
        pdf.bullet(item)
    pdf.ln(2)

    pdf.subsection_title("14.2  Kroki instalacji")
    pdf.code_block(
        "# 1. Stworzenie srodowiska wirtualnego\n"
        "python -m venv .venv\n\n"
        "# 2. Aktywacja (Windows PowerShell)\n"
        ".venv\\Scripts\\Activate.ps1\n\n"
        "# 3. Instalacja pakietow\n"
        "pip install -r requirements.txt\n\n"
        "# 4. Pobranie przegladarki Chromium dla Playwright\n"
        "playwright install chromium\n\n"
        "# 5. Uruchomienie wyszukiwarki (min. 5 pokoi)\n"
        "python main.py\n\n"
        "# 6. Wyszukiwanie z innym progiem pokoi\n"
        "python main.py 4"
    )
    pdf.ln(2)

    pdf.subsection_title("14.3  Uruchomienie pojedynczego scrapera")
    pdf.code_block(
        "python scrapers/degewo.py    # ~20 sek., Playwright\n"
        "python scrapers/gewobag.py   # ~3 min,  WP API + Playwright\n"
        "python scrapers/wbm.py       # ~2 sek.,  requests + BS4\n"
        "python scrapers/howoge.py    # <1 sek.,  POST JSON API"
    )
    pdf.ln(2)

    pdf.subsection_title("13.4  requirements.txt")
    pdf.body_text(
        "Plik requirements.txt zawiera wszystkie zaleznosci projektu. "
        "fpdf2 jest potrzebny wylacznie do generowania dokumentacji PDF "
        "i nie jest wymagany do dzialania scrapera."
    )
    pdf.code_block(
        "# Zaleznosci uruchomieniowe (scraper)\n"
        "beautifulsoup4==4.14.3\n"
        "playwright==1.58.0\n"
        "requests==2.33.1\n\n"
        "# Zaleznosci deweloperskie (generowanie dokumentacji PDF)\n"
        "fpdf2==2.8.7"
    )

    # -- ZAPIS -----------------------------------------------------------------
    out_path = r"d:\privat\mieszkanie\Wyszukiwanie\dokumentacja.pdf"
    pdf.output(out_path)
    print(f"Dokumentacja zapisana: {out_path}")


if __name__ == "__main__":
    generate()


