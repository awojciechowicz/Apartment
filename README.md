# 🏠 Berlin Apartment Scraper

Automated rental apartment scraper for Berlin – monitors the portals of 6 Berlin municipal housing companies (LWU), detects new listings, and sends HTML email notifications split into **no WBS required** and **WBS required** sections.

---

## ✨ Features

- 🔍 **5 scrapers** running in parallel – degewo, gewobag, wbm, howoge, inberlinwohnen.de (GESOBAU + STADT UND LAND + Berlinovo)
- 🏷️ **WBS detection** – distinguishes the type of certificate required (WBS 100/140/160/180/220, besonderer Wohnbedarf)
- 💾 **SQLite persistence** – listing history, upsert, detection of removed listings
- 📧 **HTML email** – two-section table (no WBS / WBS required) with columns: source, address, district, rooms, area, rent, availability
- ⏱️ **GitHub Actions** – cron every 30 minutes, database persisted in the repository via `git commit`
- 🎛️ **Configurable threshold** – defaults to ≥ 5 rooms, adjustable via the `MIN_ROOMS` environment variable

---

## 🗺️ Covered sources

| Source | Housing company | Method | WBS |
|--------|----------------|--------|-----|
| [degewo.de](https://www.degewo.de) | DEGEWO | Playwright + BeautifulSoup4 | ✅ |
| [gewobag.de](https://www.gewobag.de) | GEWOBAG | WP REST API + Playwright | ✅ |
| [wbm.de](https://www.wbm.de) | WBM | requests + BeautifulSoup4 | ✅ |
| [howoge.de](https://www.howoge.de) | HOWOGE | POST JSON API | ✅ |
| [inberlinwohnen.de](https://www.inberlinwohnen.de) | GESOBAU | requests + BS4 (Livewire) | ✅ |
| [inberlinwohnen.de](https://www.inberlinwohnen.de) | STADT UND LAND | requests + BS4 (Livewire) | ✅ |
| [inberlinwohnen.de](https://www.inberlinwohnen.de) | Berlinovo | requests + BS4 (Livewire) | ✅ |

---

## 📁 Project structure

```
Wyszukiwanie/
├── models.py                  # Apartment dataclass (shared data model)
├── scrapers/
│   ├── __init__.py
│   ├── degewo.py              # Playwright + BS4
│   ├── gewobag.py             # WP REST API + Playwright
│   ├── wbm.py                 # requests + BS4 / TYPO3+OpenImmo
│   ├── howoge.py              # POST JSON API
│   └── inberlinwohnen.py      # requests + BS4 / Laravel Livewire snapshots
├── main.py                    # Orchestrator – ThreadPoolExecutor, 5 scrapers
├── db.py                      # SQLite – upsert, history, migrations
├── notify.py                  # HTML email via SMTP (Gmail App Password)
├── mieszkania.db              # SQLite database (tracked by git)
├── .env.example               # Environment variable template
├── requirements.txt           # Python dependencies
├── generate_docs.py           # PDF documentation generator (dev)
├── dokumentacja.pdf           # Generated technical documentation
└── .github/
    └── workflows/
        └── scrape.yml         # GitHub Actions – cron every 30 min
```

---

## 🚀 Local setup

### Requirements

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<user>/<repo>.git
cd <repo>

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.\.venv\Scripts\Activate.ps1    # Windows (PowerShell)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the Playwright browser
playwright install chromium

# 5. Configure environment variables
cp .env.example .env
# Edit .env and fill in your SMTP credentials
```

### `.env` configuration

```dotenv
# Email (SMTP)
NOTIFY_SMTP_HOST=smtp.gmail.com
NOTIFY_SMTP_PORT=587
NOTIFY_SMTP_USER=your.email@gmail.com
NOTIFY_SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # Gmail App Password
NOTIFY_TO=recipient@gmail.com              # comma-separated for multiple addresses

# Scraper
MIN_ROOMS=5                                # minimum number of rooms (default: 5)
```

> **Gmail App Password:** Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), create an app password, and paste the 16-character code into `NOTIFY_SMTP_PASSWORD`.

### Running

```bash
# Default: ≥ 5 rooms
python main.py

# Custom room threshold
python main.py 4
```

---

## ⚙️ GitHub Actions (automated scheduling)

The scraper runs automatically **every 30 minutes** via GitHub Actions. The database `mieszkania.db` is persisted in the repository via a `chore: update DB [skip ci]` commit.

### Required Secrets (Settings → Secrets → Actions)

| Secret | Description |
|--------|-------------|
| `NOTIFY_SMTP_HOST` | SMTP server (e.g. `smtp.gmail.com`) |
| `NOTIFY_SMTP_PORT` | SMTP port (e.g. `587`) |
| `NOTIFY_SMTP_USER` | SMTP login / sender address |
| `NOTIFY_SMTP_PASSWORD` | SMTP password / Gmail App Password |
| `NOTIFY_TO` | Recipient address(es), comma-separated |

### Manual trigger

GitHub UI → **Actions** → `Scraper mieszkan Berlin` → **Run workflow** → optionally specify the minimum number of rooms.

---

## 📧 Email format

The HTML email is split into two colour-coded sections:

**🟢 No WBS required** – listings available to everyone  
**🔴 WBS required** – listings requiring a housing entitlement certificate

Each section contains a table with the following columns:

| Source | Listing / Address | District | Rooms | Area | Rent | WBS | Available from |
|--------|------------------|----------|-------|------|------|-----|----------------|

---

## 🧱 Data model

Every listing is an `Apartment` dataclass instance:

| Field | Type | Description |
|-------|------|-------------|
| `source` | `str` | Origin: `degewo` / `gewobag` / `wbm` / `howoge` / `gesobau` / `stadtundland` / `berlinovo` |
| `title` | `str` | Listing title |
| `address` | `str` | Street address |
| `district` | `str` | Berlin district (Bezirk) |
| `rooms` | `float \| None` | Number of rooms |
| `area_m2` | `float \| None` | Floor area in m² |
| `warm_rent` | `float \| None` | Total rent (Gesamtmiete) in EUR |
| `cold_rent` | `float \| None` | Net cold rent (Kaltmiete) in EUR |
| `available_from` | `str \| None` | Availability date (`dd.mm.yyyy` or `sofort`) |
| `wbs_required` | `bool` | Whether a WBS certificate is required |
| `wbs_type` | `str \| None` | WBS category: `WBS 160`, `WBS 220`, `besonderer Wohnbedarf`, etc. |
| `url` | `str` | Direct link to the listing |
| `extra` | `dict` | Additional metadata (uid, features, objektnummer, …) |

---

## 🛠️ Tech stack

| Package | Version | Purpose |
|---------|---------|---------|
| `playwright` | 1.58.0 | Chromium browser automation (JS rendering, AJAX tables) |
| `beautifulsoup4` | 4.14.3 | HTML parsing |
| `requests` | 2.33.1 | HTTP GET/POST to REST APIs |
| `sqlite3` | built-in | Database – listing history |
| `smtplib` | built-in | Sending HTML emails via SMTP |
| `fpdf2` | 2.8.7 | PDF documentation generation *(dev only)* |

---

## 📄 Technical documentation

Full technical documentation in PDF format: [`dokumentacja.pdf`](./dokumentacja.pdf)

Contains a detailed description of each scraper, flow diagrams, database schema, SMTP configuration, and a sample email preview.

To regenerate the PDF:

```bash
pip install fpdf2
python generate_docs.py
```

---

## 📝 License

Private project – for personal use only.
# Apartment
