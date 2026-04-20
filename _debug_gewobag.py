import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/wohnung/"

async def inspect():
    all_req = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(locale="de-DE")

        def on_request(req):
            if req.resource_type in ("xhr", "fetch"):
                all_req.append(f"{req.method} {req.url[:120]}")

        async def on_response(response):
            if response.request.resource_type in ("xhr", "fetch") and response.status == 200:
                try:
                    body = await response.text()
                    if len(body) > 300:
                        all_req.append(f"  RESP({len(body)}b): {body[:300]}")
                except Exception:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)

        await page.goto(SEARCH_URL, wait_until="networkidle", timeout=30000)
        try:
            await page.click("button:has-text('Alle akzeptieren')", timeout=6000)
            await page.wait_for_timeout(3000)
        except Exception:
            pass

        print("=== XHR/Fetch po zaladowaniu strony ===")
        for r in all_req:
            print(r)

        # Sprawdz tez HTML - moze sa osadzone dane w script[type=application/json]
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", type="application/json")
        print(f"\nScript[type=application/json]: {len(scripts)}")
        for s in scripts[:3]:
            print(s.string[:300] if s.string else "(brak)")

        # Inline JSON w script
        all_scripts = soup.find_all("script")
        for s in all_scripts:
            if s.string and ("zimmer" in s.string.lower() or "wbs" in s.string.lower() or "miete" in s.string.lower()):
                print(f"\nSkrypt z danymi mieszkan: {s.string[:400]}")
                break

        await browser.close()

asyncio.run(inspect())
