"""
Modul obslugi bazy danych SQLite dla wynikow scrapowania mieszkan.

Schemat:
  apartments  - wszystkie oferty (upsert po url)
  scrape_runs - historia uruchomien scrapera
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from models import Apartment

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).parent / "mieszkania.db")))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Tworzy tabele jesli nie istnieja, wykonuje migracje."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at      TEXT NOT NULL,
                finished_at     TEXT,
                source          TEXT NOT NULL,
                found_total     INTEGER,
                found_new       INTEGER,
                found_updated   INTEGER,
                found_removed   INTEGER,
                error           TEXT
            );

            CREATE TABLE IF NOT EXISTS apartments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                url             TEXT NOT NULL UNIQUE,
                source          TEXT NOT NULL,
                first_seen_at   TEXT NOT NULL,
                last_seen_at    TEXT NOT NULL,
                last_updated_at TEXT NOT NULL,
                title           TEXT,
                address         TEXT,
                district        TEXT,
                rooms           REAL,
                area_m2         REAL,
                warm_rent       REAL,
                cold_rent       REAL,
                available_from  TEXT,
                wbs_required    INTEGER NOT NULL DEFAULT 0,
                wbs_type        TEXT,
                extra_json      TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_apartments_source
                ON apartments(source);
            CREATE INDEX IF NOT EXISTS idx_apartments_rooms
                ON apartments(rooms);
            CREATE INDEX IF NOT EXISTS idx_apartments_wbs
                ON apartments(wbs_required);
        """)
        # Migracja: dodaj found_removed jesli kolumna nie istnieje
        try:
            conn.execute("ALTER TABLE scrape_runs ADD COLUMN found_removed INTEGER")
        except sqlite3.OperationalError:
            pass  # Kolumna juz istnieje


def save_apartments(
    apartments: list[Apartment],
    run_id: int | None = None,
) -> tuple[list[Apartment], int]:
    """
    Zapisuje liste mieszkan do bazy (upsert po url).

    Returns:
        (new_apartments, updated_count)
    """
    now = datetime.now(timezone.utc).isoformat()
    new_apts: list[Apartment] = []
    updated_count = 0

    with _connect() as conn:
        for apt in apartments:
            existing = conn.execute(
                "SELECT id, warm_rent, rooms, area_m2 FROM apartments WHERE url = ?",
                (apt.url,),
            ).fetchone()

            extra = json.dumps(apt.extra, ensure_ascii=False) if apt.extra else None

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO apartments (
                        url, source, first_seen_at, last_seen_at, last_updated_at,
                        title, address, district, rooms, area_m2,
                        warm_rent, cold_rent, available_from,
                        wbs_required, wbs_type, extra_json
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        apt.url, apt.source, now, now, now,
                        apt.title, apt.address, apt.district,
                        apt.rooms, apt.area_m2,
                        apt.warm_rent, apt.cold_rent, apt.available_from,
                        int(apt.wbs_required), apt.wbs_type, extra,
                    ),
                )
                new_apts.append(apt)
            else:
                # Aktualizuj jesli zmienily sie kluczowe dane
                changed = (
                    existing["warm_rent"] != apt.warm_rent
                    or existing["rooms"] != apt.rooms
                    or existing["area_m2"] != apt.area_m2
                )
                if changed:
                    conn.execute(
                        """
                        UPDATE apartments SET
                            last_seen_at = ?, last_updated_at = ?,
                            title = ?, address = ?, district = ?,
                            rooms = ?, area_m2 = ?,
                            warm_rent = ?, cold_rent = ?, available_from = ?,
                            wbs_required = ?, wbs_type = ?, extra_json = ?
                        WHERE url = ?
                        """,
                        (
                            now, now,
                            apt.title, apt.address, apt.district,
                            apt.rooms, apt.area_m2,
                            apt.warm_rent, apt.cold_rent, apt.available_from,
                            int(apt.wbs_required), apt.wbs_type, extra,
                            apt.url,
                        ),
                    )
                    updated_count += 1
                else:
                    # Tylko zaktualizuj last_seen_at
                    conn.execute(
                        "UPDATE apartments SET last_seen_at = ? WHERE url = ?",
                        (now, apt.url),
                    )

    return new_apts, updated_count


def start_run(source: str) -> int:
    """Rejestruje poczatek uruchomienia scrapera. Zwraca run_id."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO scrape_runs (started_at, source) VALUES (?, ?)",
            (now, source),
        )
        return cur.lastrowid


def remove_inactive(source: str, active_urls: list[str]) -> int:
    """
    Usuwa z bazy oferty danego zrodla, ktorych URL nie ma w active_urls.
    Zwraca liczbe usunietych rekordow.
    """
    if not active_urls:
        # Zabezpieczenie: jesli scraper nie zwrocil nic (np. blad sieci),
        # nie usuwamy calej bazy danego zrodla
        return 0
    placeholders = ",".join("?" * len(active_urls))
    with _connect() as conn:
        cur = conn.execute(
            f"DELETE FROM apartments WHERE source = ? AND url NOT IN ({placeholders})",
            [source] + active_urls,
        )
        return cur.rowcount


def finish_run(
    run_id: int,
    found_total: int,
    found_new: int,
    found_updated: int,
    found_removed: int = 0,
    error: str | None = None,
) -> None:
    """Aktualizuje rekord uruchomienia po zakonczeniu."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE scrape_runs SET
                finished_at = ?, found_total = ?,
                found_new = ?, found_updated = ?, found_removed = ?, error = ?
            WHERE id = ?
            """,
            (now, found_total, found_new, found_updated, found_removed, error, run_id),
        )


def query_apartments(
    min_rooms: float = 5.0,
    wbs: bool | None = None,
    source: str | None = None,
) -> list[sqlite3.Row]:
    """Zwraca oferty spelniajace kryteria, posortowane: zrodlo, WBS, pokoje malejaco."""
    sql = "SELECT * FROM apartments WHERE rooms >= ?"
    params: list = [min_rooms]
    if wbs is not None:
        sql += " AND wbs_required = ?"
        params.append(int(wbs))
    if source:
        sql += " AND source = ?"
        params.append(source)
    sql += " ORDER BY source, wbs_required, rooms DESC, warm_rent"

    with _connect() as conn:
        return conn.execute(sql, params).fetchall()


def print_stats() -> None:
    """Wyswietla statystyki bazy."""
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM apartments").fetchone()[0]
        print(f"Lacznie w bazie: {total} ofert")

        print("\nWg zrodla:")
        for row in conn.execute(
            "SELECT source, COUNT(*) as cnt FROM apartments GROUP BY source ORDER BY source"
        ):
            print(f"  {row['source']:12} {row['cnt']:4} ofert")

        print("\nOstatnie uruchomienia:")
        for row in conn.execute(
            """SELECT source, started_at, found_total, found_new, found_updated, found_removed, error
               FROM scrape_runs ORDER BY id DESC LIMIT 8"""
        ):
            if row['error']:
                status = f"ERR: {row['error'][:40]}"
            else:
                status = (f"+{row['found_new'] or 0} nowych, "
                          f"~{row['found_updated'] or 0} zmian, "
                          f"-{row['found_removed'] or 0} usunietych")
            print(f"  {row['source']:12} {row['started_at'][:16]}  {row['found_total'] or 0:3} znaleziono  {status}")


if __name__ == "__main__":
    init_db()
    print(f"Baza zainicjalizowana: {DB_PATH}")
    print_stats()
