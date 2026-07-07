"""
Modul wysylania powiadomien email o nowych ofertach mieszkan.

Konfiguracja przez zmienne srodowiskowe (plik .env):
  NOTIFY_SMTP_HOST     - serwer SMTP (domyslnie smtp.gmail.com)
  NOTIFY_SMTP_PORT     - port SMTP (domyslnie 587)
  NOTIFY_SMTP_USER     - login/adres nadawcy
  NOTIFY_SMTP_PASSWORD - haslo / App Password (Gmail)
  NOTIFY_TO            - adres(y) odbiorcy, przecinek-oddzielone
"""

import os
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from models import Apartment

SMTP_HOST = os.environ.get("NOTIFY_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("NOTIFY_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("NOTIFY_SMTP_USER", "")
SMTP_PASS = os.environ.get("NOTIFY_SMTP_PASSWORD", "")
NOTIFY_TO = os.environ.get("NOTIFY_TO", "")


def _is_configured() -> bool:
    return bool(SMTP_USER and SMTP_PASS and NOTIFY_TO)


def _apt_row(apt: Apartment, idx: int) -> str:
    wbs_label = f"WBS: {apt.wbs_type}" if apt.wbs_type else "WBS"
    wbs_badge = (
        f'<span style="background:#e74c3c;color:#fff;padding:2px 6px;'
        f'border-radius:3px;font-size:11px;">{wbs_label}</span>'
        if apt.wbs_required
        else '<span style="background:#27ae60;color:#fff;padding:2px 6px;'
        'border-radius:3px;font-size:11px;">bez WBS</span>'
    )
    rent = f"{apt.warm_rent:.0f} EUR" if apt.warm_rent else "?"
    area = f"{apt.area_m2:.0f} m&sup2;" if apt.area_m2 else "?"
    rooms = f"{apt.rooms:.0f}" if apt.rooms else "?"
    avail = apt.available_from or ""
    source_color = {
        "degewo": "#2980b9", "gewobag": "#8e44ad",
        "wbm": "#16a085", "howoge": "#d35400",
    }.get(apt.source, "#555")
    bg = "#fafafa" if idx % 2 == 0 else "#fff"

    return f"""
        <tr style="background:{bg};">
          <td style="padding:8px;border-bottom:1px solid #eee;">
            <span style="background:{source_color};color:#fff;padding:2px 5px;
              border-radius:3px;font-size:10px;font-weight:bold;">
              {apt.source.upper()}
            </span>
          </td>
          <td style="padding:8px;border-bottom:1px solid #eee;">
            <a href="{apt.url}" style="color:#2c3e50;font-weight:bold;
              text-decoration:none;">{apt.title or apt.address}</a>
            <br><small style="color:#777;">{apt.address}</small>
          </td>
          <td style="padding:8px;border-bottom:1px solid #eee;color:#555;font-size:12px;">
            {apt.district or "&mdash;"}
          </td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{rooms}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{area}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;
            font-weight:bold;">{rent}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{wbs_badge}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;font-size:12px;
            color:#888;">{avail}</td>
        </tr>"""


def _section_table(apts: list[Apartment], title: str, header_color: str) -> str:
    if not apts:
        return ""
    sorted_apts = sorted(apts, key=lambda a: (a.rooms is not None, -(a.rooms or 0)))
    rows = "".join(_apt_row(apt, i) for i, apt in enumerate(sorted_apts))
    return f"""
      <h2 style="margin:24px 0 8px;font-size:15px;color:{header_color};
        border-left:4px solid {header_color};padding-left:10px;">
        {title} &nbsp;<span style="font-size:12px;font-weight:normal;
          color:#888;">({len(apts)} ofert)</span>
      </h2>
      <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px;">
        <thead>
          <tr style="background:#ecf0f1;">
            <th style="padding:8px;text-align:left;">Zrodlo</th>
            <th style="padding:8px;text-align:left;">Oferta</th>
            <th style="padding:8px;text-align:left;">Dzielnica</th>
            <th style="padding:8px;text-align:center;">Pok.</th>
            <th style="padding:8px;text-align:center;">Metraz</th>
            <th style="padding:8px;text-align:center;">Czynsz</th>
            <th style="padding:8px;text-align:left;">WBS</th>
            <th style="padding:8px;text-align:left;">Wolne od</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>"""


def _build_html(new_apts: list[Apartment]) -> str:
    without_wbs = [a for a in new_apts if not a.wbs_required]
    with_wbs    = [a for a in new_apts if a.wbs_required]

    sections = ""
    if without_wbs:
        sections += _section_table(without_wbs, "Bez WBS", "#27ae60")
    if with_wbs:
        sections += _section_table(with_wbs, "Wymagany WBS", "#e74c3c")

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px;">
  <div style="max-width:900px;margin:auto;background:#fff;border-radius:8px;
    box-shadow:0 2px 8px rgba(0,0,0,.1);overflow:hidden;">
    <div style="background:#2c3e50;color:#fff;padding:20px 30px;">
      <h1 style="margin:0;font-size:20px;">Nowe oferty mieszkan w Berlinie</h1>
      <p style="margin:8px 0 0;opacity:.8;font-size:13px;">
        Znaleziono {len(new_apts)} nowych ofert &mdash; degewo / gewobag / wbm / howoge
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span style="color:#2ecc71;">bez WBS: {len(without_wbs)}</span>
        &nbsp;&nbsp;
        <span style="color:#e74c3c;">z WBS: {len(with_wbs)}</span>
      </p>
    </div>
    <div style="padding:20px 30px;">
      {sections}
    </div>
    <div style="background:#ecf0f1;padding:12px 30px;font-size:11px;color:#999;">
      Wiadomosc wygenerowana automatycznie przez wyszukiwarke mieszkan Berlin.
    </div>
  </div>
</body>
</html>"""


def send(new_apts: list[Apartment]) -> bool:
    """
    Wysyla email z nowymi ofertami.
    Zwraca True jesli wyslano, False jesli brak konfiguracji lub blad.
    """
    if not new_apts:
        return False

    if not _is_configured():
        print("  [notify] Pominieto - brak konfiguracji SMTP (NOTIFY_SMTP_USER/PASSWORD/TO)")
        return False

    recipients = [r.strip() for r in NOTIFY_TO.split(",") if r.strip()]
    count = len(new_apts)
    subject = f"Berlin: {count} nowa oferta mieszkania" if count == 1 else f"Berlin: {count} nowe oferty mieszkan"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(recipients)

    # Wersja tekstowa (fallback)
    without_wbs = [a for a in new_apts if not a.wbs_required]
    with_wbs    = [a for a in new_apts if a.wbs_required]

    text_lines = [f"Nowe oferty mieszkan w Berlinie ({count})\n"]

    if without_wbs:
        text_lines.append(f"== BEZ WBS ({len(without_wbs)}) ==\n")
        for apt in sorted(without_wbs, key=lambda a: (a.source, -(a.rooms or 0))):
            rent = f"{apt.warm_rent:.0f} EUR" if apt.warm_rent else "?"
            text_lines.append(
                f"[{apt.source.upper()}] {apt.rooms or '?'} pok. | {apt.area_m2 or '?'} m2 | {rent}\n"
                f"{apt.title or apt.address}\n{apt.url}\n"
            )

    if with_wbs:
        text_lines.append(f"\n== WYMAGANY WBS ({len(with_wbs)}) ==\n")
        for apt in sorted(with_wbs, key=lambda a: (a.source, -(a.rooms or 0))):
            rent = f"{apt.warm_rent:.0f} EUR" if apt.warm_rent else "?"
            wbs = f"WBS: {apt.wbs_type}" if apt.wbs_type else "WBS"
            text_lines.append(
                f"[{apt.source.upper()}] {apt.rooms or '?'} pok. | {apt.area_m2 or '?'} m2 | {rent} | {wbs}\n"
                f"{apt.title or apt.address}\n{apt.url}\n"
            )
    msg.attach(MIMEText("\n".join(text_lines), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(new_apts), "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipients, msg.as_string())
        print(f"  [notify] Email wyslany do: {', '.join(recipients)} ({count} ofert)")
        return True
    except Exception as exc:
        print(f"  [notify] BLAD wysylania emaila: {exc}")
        return False


def _stale_warnings_html(warnings: list[dict]) -> str:
    """Buduje blok HTML z ostrzezeniami o portalach bez nowych ofert od >3 dni."""
    if not warnings:
        return ""
    rows_html = "".join(
        f"""<tr>
          <td style="padding:6px 8px;border-bottom:1px solid #f5c6c6;
            font-weight:bold;">{w['source'].upper()}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #f5c6c6;">{w['last_new']}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #f5c6c6;
            text-align:center;">{w['days_ago']}</td>
        </tr>"""
        for w in warnings
    )
    return f"""
      <div style="background:#fdecea;border:1px solid #f5c6c6;border-radius:6px;
        padding:14px 20px;margin-bottom:20px;">
        <h3 style="margin:0 0 10px;color:#c0392b;font-size:14px;">
          &#9888;&nbsp;Ostrzezenie: brak nowych ofert od ponad 3 dni
        </h3>
        <p style="margin:0 0 10px;font-size:12px;color:#555;">
          Ponizsze portale nie dodaly zadnych nowych ofert od ponad 3 dni.
          Moze to oznaczac problem ze scraperem lub chwilowy brak ofert na portalu.
        </p>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead>
            <tr style="background:#f5c6c6;">
              <th style="padding:6px 8px;text-align:left;">Portal</th>
              <th style="padding:6px 8px;text-align:left;">Ostatnia nowa oferta</th>
              <th style="padding:6px 8px;text-align:center;">Dni temu</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>"""


def send_daily_summary(
    rows: list[sqlite3.Row],
    stale_warnings: list[dict] | None = None,
) -> bool:
    """
    Wysyla dzienny raport z WSZYSTKIMI ofertami dodanymi dzisiaj.

    Args:
        rows:            Lista sqlite3.Row z tabeli apartments (wynik query_today_new()).
        stale_warnings:  Lista slownikow z query_stale_sources() – portale bez nowych ofert
                         od wiecej niz 3 dni. Jesli podana i niepusta, raport zawiera
                         blok ostrzegawczy informujacy o mozliwym problemie ze scraperem.
    """
    stale_warnings = stale_warnings or []
    if not rows and not stale_warnings:
        print("  [notify] Dzienny raport: brak nowych ofert i brak ostrzezen.")
        return False

    if not _is_configured():
        print("  [notify] Pominieto - brak konfiguracji SMTP")
        return False

    # Konwertuj Row -> Apartment
    apts: list[Apartment] = []
    for r in rows:
        apts.append(Apartment(
            url=r["url"],
            source=r["source"],
            title=r["title"],
            address=r["address"] or "",
            district=r["district"],
            rooms=r["rooms"],
            area_m2=r["area_m2"],
            warm_rent=r["warm_rent"],
            cold_rent=r["cold_rent"],
            available_from=r["available_from"],
            wbs_required=bool(r["wbs_required"]),
            wbs_type=r["wbs_type"],
        ))

    recipients = [r.strip() for r in NOTIFY_TO.split(",") if r.strip()]
    count = len(apts)
    if apts:
        subject = f"Berlin dzienny raport: {count} nowych ofert mieszkan"
    else:
        subject = f"Berlin dzienny raport: ostrzezenia scraperow ({len(stale_warnings)})"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(recipients)

    without_wbs = [a for a in apts if not a.wbs_required]
    with_wbs    = [a for a in apts if a.wbs_required]

    text_lines = [f"Dzienny raport mieszkan Berlin ({count} nowych dzisiaj)\n"]
    if stale_warnings:
        text_lines.append("== OSTRZEZENIE: BRAK NOWYCH OFERT OD PONAD 3 DNI ==\n")
        for w in stale_warnings:
            text_lines.append(f"  {w['source'].upper():15} ostatnia nowa oferta: {w['last_new']} ({w['days_ago']} dni temu)\n")
        text_lines.append("Sprawdz, czy scraper dziala poprawnie!\n")
    if without_wbs:
        text_lines.append(f"== BEZ WBS ({len(without_wbs)}) ==\n")
        for apt in without_wbs:
            rent = f"{apt.warm_rent:.0f} EUR" if apt.warm_rent else "?"
            text_lines.append(
                f"[{apt.source.upper()}] {apt.rooms or '?'} pok. | {apt.area_m2 or '?'} m2 | {rent}\n"
                f"{apt.title or apt.address}\n{apt.url}\n"
            )
    if with_wbs:
        text_lines.append(f"\n== WYMAGANY WBS ({len(with_wbs)}) ==\n")
        for apt in with_wbs:
            rent = f"{apt.warm_rent:.0f} EUR" if apt.warm_rent else "?"
            wbs = f"WBS: {apt.wbs_type}" if apt.wbs_type else "WBS"
            text_lines.append(
                f"[{apt.source.upper()}] {apt.rooms or '?'} pok. | {apt.area_m2 or '?'} m2 | {rent} | {wbs}\n"
                f"{apt.title or apt.address}\n{apt.url}\n"
            )

    # Buduj HTML z naglowkiem 'Dzienny raport'
    warnings_block = _stale_warnings_html(stale_warnings)
    sections = ""
    if without_wbs:
        sections += _section_table(without_wbs, "Bez WBS", "#27ae60")
    if with_wbs:
        sections += _section_table(with_wbs, "Wymagany WBS", "#e74c3c")

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px;">
  <div style="max-width:900px;margin:auto;background:#fff;border-radius:8px;
    box-shadow:0 2px 8px rgba(0,0,0,.1);overflow:hidden;">
    <div style="background:#1a252f;color:#fff;padding:20px 30px;">
      <h1 style="margin:0;font-size:20px;">Dzienny raport mieszkan Berlin</h1>
      <p style="margin:8px 0 0;opacity:.8;font-size:13px;">
        Dzisiaj dodano {count} nowych ofert
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span style="color:#2ecc71;">bez WBS: {len(without_wbs)}</span>
        &nbsp;&nbsp;
        <span style="color:#e74c3c;">z WBS: {len(with_wbs)}</span>
      </p>
    </div>
    <div style="padding:20px 30px;">
      {warnings_block}
      {sections}
    </div>
    <div style="background:#ecf0f1;padding:12px 30px;font-size:11px;color:#999;">
      Wiadomosc wygenerowana automatycznie &mdash; raport dzienny 20:00 CEST.
    </div>
  </div>
</body>
</html>"""

    msg.attach(MIMEText("\n".join(text_lines), "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipients, msg.as_string())
        print(f"  [notify] Dzienny raport wyslany do: {', '.join(recipients)} ({count} ofert)")
        return True
    except Exception as exc:
        print(f"  [notify] BLAD wysylania dziennego raportu: {exc}")
        return False
