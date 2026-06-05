"""
Orkiestrator scrapera mieszkan w Berlinie.
Uruchamia wszystkie 5 scraperow rownoczesnie i wyswietla wyniki.

Zrodla: degewo.de, gewobag.de, wbm.de, howoge.de, inberlinwohnen.de
Filtr:  >= 4 pokoi (domyslnie)
"""

import concurrent.futures
import time
from typing import Callable

import db
import notify
from models import Apartment

MIN_ROOMS = 4.0


def _run_scraper(name: str, fn: Callable, min_rooms: float) -> tuple[str, list[Apartment], str | None, list[Apartment]]:
    """
    Uruchamia jeden scraper (sync lub async).
    Pobiera WSZYSTKIE oferty (min_rooms=1), zapisuje do bazy,
    zwraca tylko te spelniajace prog min_rooms do wyswietlenia.
    """
    import asyncio, inspect
    run_id = db.start_run(name)
    try:
        start = time.time()
        if inspect.iscoroutinefunction(fn):
            all_apts = asyncio.run(fn(min_rooms=1.0))
        else:
            all_apts = fn(min_rooms=1.0)
        elapsed = time.time() - start

        # Zapis wszystkich ofert do bazy
        new_apts, upd_cnt = db.save_apartments(all_apts)

        # Usun z bazy oferty ktore zniknely ze strony
        # Dla inberlinwohnen: usuwamy per kazde podrzrodlo osobno
        active_urls = [a.url for a in all_apts]
        subsources = set(a.source for a in all_apts)
        if subsources - {name}:
            # Scraper zwrocil wiele zrodel (np. inberlinwohnen -> gesobau, stadtundland, ...)
            rem_cnt = 0
            for subsrc in subsources:
                urls_for_src = [a.url for a in all_apts if a.source == subsrc]
                rem_cnt += db.remove_inactive(subsrc, urls_for_src)
        else:
            rem_cnt = db.remove_inactive(name, active_urls)

        db.finish_run(run_id, len(all_apts), len(new_apts), upd_cnt, rem_cnt)

        # Filtruj do wyswietlenia: >= min_rooms LUB jakikolwiek WBS
        results = [a for a in all_apts if (a.rooms or 0) >= min_rooms or a.wbs_required]
        wbs_count = sum(1 for a in results if a.wbs_required)
        non_wbs_count = sum(1 for a in results if not a.wbs_required)
        print(f"  [{name}] OK - {len(all_apts)} ofert "
              f"({non_wbs_count} bez WBS >= {min_rooms:.0f} pok. | {wbs_count} z WBS dowolna liczba pokoi) "
              f"| baza: +{len(new_apts)} nowych, ~{upd_cnt} zmian, -{rem_cnt} usunietych ({elapsed:.1f}s)")
        return name, results, None, new_apts
    except Exception as exc:
        db.finish_run(run_id, 0, 0, 0, error=str(exc))
        print(f"  [{name}] BLAD: {exc}")
        return name, [], str(exc), []


def print_apartment(apt: Apartment) -> None:
    wbs = f"WBS: {apt.wbs_type}" if apt.wbs_required and apt.wbs_type else ("WBS wymagane" if apt.wbs_required else "bez WBS")
    rent = f"{apt.warm_rent:.0f} EUR" if apt.warm_rent else "czynsz nieznany"
    area = f"{apt.area_m2:.0f} m2" if apt.area_m2 else "?"
    rooms_val = apt.rooms or 0
    rooms = f"{rooms_val:.0f} pok." if rooms_val == int(rooms_val) else f"{rooms_val} pok."
    print(f"  {'='*60}")
    print(f"  {rooms} | {area} | {rent} | [{wbs}]")
    print(f"  Tytul:    {apt.title}")
    print(f"  Adres:    {apt.address}")
    if apt.district:
        print(f"  Dzielnica:{apt.district}")
    if apt.available_from:
        print(f"  Wolne od: {apt.available_from}")
    print(f"  URL:      {apt.url}")


def main(min_rooms: float = MIN_ROOMS) -> None:
    db.init_db()

    print(f"Wyszukiwanie mieszkan >= {min_rooms:.0f} pokoi w Berlinie")
    print(f"Zrodla: degewo.de, gewobag.de, wbm.de, howoge.de, inberlinwohnen.de")
    print("=" * 62)

    # Importy scraperoow tutaj, zeby blad importu nie zabijabl calego skryptu
    # Nazwy funkcji roznia sie miedzy scraperami
    SCRAPER_FUNC = {
        "degewo":          "scrape_degewo",
        "gewobag":         "scrape_gewobag",
        "wbm":             "scrape",
        "howoge":          "scrape",
        "inberlinwohnen":  "scrape",
    }

    scrapers: list[tuple[str, Callable]] = []
    for mod_name, scraper_name in [
        ("scrapers.degewo",          "degewo"),
        ("scrapers.gewobag",         "gewobag"),
        ("scrapers.wbm",             "wbm"),
        ("scrapers.howoge",          "howoge"),
        ("scrapers.inberlinwohnen",  "inberlinwohnen"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(mod_name)
            fn_name = SCRAPER_FUNC[scraper_name]
            fn = getattr(mod, fn_name)
            scrapers.append((scraper_name, fn))
        except (ImportError, AttributeError) as e:
            print(f"  [{scraper_name}] Pominieto: {e}")

    print(f"\nUruchamianie {len(scrapers)} scraperow...\n")
    start_all = time.time()

    # degewo i gewobag uzywaja Playwright (async/sync wrappers) –
    # uruchamiamy sekwencyjnie w osobnych watkach zeby uniknac konfliktow event loop
    all_results: dict[str, list[Apartment]] = {}
    errors: dict[str, str] = {}
    all_new_apts: list[Apartment] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_run_scraper, name, fn, min_rooms): name
            for name, fn in scrapers
        }
        for future in concurrent.futures.as_completed(futures):
            name, results, err, new_apts = future.result()
            all_results[name] = results
            all_new_apts.extend(new_apts)
            if err:
                errors[name] = err

    # Wyslij email dla nowych ofert >= min_rooms pokoi LUB z WBS (tak samo jak widok)
    notif_apts = [a for a in all_new_apts if (a.rooms or 0) >= min_rooms or a.wbs_required]
    if notif_apts:
        print(f"\n  Wyslij powiadomienie o {len(notif_apts)} nowych ofertach >= {min_rooms:.0f} pok. "
              f"({sum(1 for a in notif_apts if not a.wbs_required)} bez WBS "
              f"+ {sum(1 for a in notif_apts if a.wbs_required)} z WBS)...")
        notify.send(notif_apts)

    elapsed_all = time.time() - start_all
    print(f"\nLacznie: {elapsed_all:.1f}s\n")

    # Wyswietl wyniki
    total = sum(len(v) for v in all_results.values())
    total_no_wbs  = sum(1 for v in all_results.values() for a in v if not a.wbs_required)
    total_yes_wbs = sum(1 for v in all_results.values() for a in v if a.wbs_required)
    print(f"{'='*62}")
    print(f"WYNIKI: {total_no_wbs} bez WBS (>= {min_rooms:.0f} pok.) + {total_yes_wbs} z WBS (dowolna l. pok.) = {total} lacznie")
    print(f"{'='*62}")

    for source in ["degewo", "gewobag", "wbm", "howoge", "inberlinwohnen"]:
        apts = all_results.get(source, [])
        label = {
            "degewo":         "DEGEWO (degewo.de)",
            "gewobag":        "GEWOBAG (gewobag.de)",
            "wbm":            "WBM (wbm.de)",
            "howoge":         "HOWOGE (howoge.de)",
            "inberlinwohnen": "GESOBAU + STADT UND LAND + Berlinovo (inberlinwohnen.de)",
        }.get(source, source.upper())

        print(f"\n--- {label}: {len(apts)} ---")

        if source in errors:
            print(f"  BLAD: {errors[source]}")
            continue

        if not apts:
            print("  Brak ofert spelniajacych kryteria.")
            continue

        # Sortuj: najpierw bez WBS, potem z WBS; w obrebie grupy wg liczby pokoi malejaco
        apts_sorted = sorted(apts, key=lambda a: (a.wbs_required, -(a.rooms or 0), a.warm_rent or 0))
        for apt in apts_sorted:
            print_apartment(apt)

    # Podsumowanie WBS
    all_apts = [a for v in all_results.values() for a in v]
    if all_apts:
        no_wbs  = [a for a in all_apts if not a.wbs_required]
        yes_wbs = [a for a in all_apts if a.wbs_required]
        print(f"\n{'='*62}")
        print(f"PODSUMOWANIE:")
        print(f"  Bez WBS (>= {min_rooms:.0f} pok.):  {len(no_wbs)}")
        print(f"  Z WBS (dowolna l. pok.):  {len(yes_wbs)}")
        print(f"  Razem:                    {total}")
        if errors:
            print(f"  Bledy scraperow: {', '.join(errors.keys())}")

    # Statystyki bazy
    print(f"\n{'='*62}")
    print("BAZA DANYCH:")
    db.print_stats()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Wyszukiwarka mieszkan Berlin")
    parser.add_argument(
        "min_rooms",
        nargs="?",
        type=float,
        default=MIN_ROOMS,
        help=f"Minimalna liczba pokoi (domyslnie {MIN_ROOMS})",
    )
    parser.add_argument(
        "--daily-summary",
        action="store_true",
        help="Wyslij dzienny raport zamiast uruchamiac scrapery",
    )
    args = parser.parse_args()

    if args.daily_summary:
        db.init_db()
        rows = db.query_today_new()
        stale = db.query_stale_sources(days=3)
        print(f"[daily-summary] Znaleziono {len(rows)} ofert dodanych dzisiaj.")
        if stale:
            print(f"[daily-summary] Ostrzezenie: {len(stale)} portal(e) bez nowych ofert od >3 dni: "
                  f"{', '.join(w['source'] for w in stale)}")
        notify.send_daily_summary(rows, stale_warnings=stale)
    else:
        main(min_rooms=args.min_rooms)
