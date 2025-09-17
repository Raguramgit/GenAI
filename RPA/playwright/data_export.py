# assignment.py
"""
Async Playwright script to search Google with improved robustness.
- Uses a persistent profile (keeps cookies/session)
- Injects a small stealth script
- Tries multiple selectors for the search box
- Detects CAPTCHA/consent pages and saves diagnostics
- Pauses for manual CAPTCHA solving if needed
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

# ----------------- CONFIG -----------------
PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profile")
CAPTCHA_SCREENSHOT = "google_captcha_or_block.png"
NO_SEARCHBOX_SCREENSHOT = "google_no_searchbox.png"
NO_RESULTS_SCREENSHOT = "google_no_results.png"
BODY_DUMP = "google_body_text.txt"

# Small stealth script to reduce obvious automation flags
STEALTH_JS = """
() => {
  try { Object.defineProperty(navigator, 'webdriver', {get: () => undefined}); } catch(e) {}
  try { Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']}); } catch(e) {}
  try { Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]}); } catch(e) {}
  try { window.chrome = { runtime: {} }; } catch(e) {}
}
"""

# Possible selectors for the Google search input (covers locales / versions)
SEARCH_SELECTORS = [
    'input[name="q"]',
    'input[aria-label="Search"]',
    'input[aria-label="Search Google"]',
    'input[type="search"]',
    'xpath=//*[@id="APjFqb"]',
    'xpath=//input[contains(@class,"gLFyf")]'
]

# ------------------------------------------

async def find_search_box(page, timeout=30000):
    """
    Try multiple selectors to find the search input. Returns the element handle or None.
    """
    for selector in SEARCH_SELECTORS:
        try:
            handle = await page.wait_for_selector(selector, timeout=timeout, state="visible")
            if handle:
                return handle
        except PWTimeoutError:
            continue
    return None

async def solve_flow(page):
    """
    Detect common blocking pages (CAPTCHA or consent).
    If CAPTCHA detected, screenshot and pause for manual solving.
    If consent dialog found, attempt to click common accept buttons.
    """
    body = await page.content()
    lowered = body.lower()

    # Detect captcha/blocking content
    if "unusual traffic" in lowered or "i'm not a robot" in lowered or "recaptcha" in lowered:
        print("⚠️ Google CAPTCHA or block detected.")
        await page.screenshot(path=CAPTCHA_SCREENSHOT, full_page=True)
        print(f"Saved screenshot -> {CAPTCHA_SCREENSHOT}")
        print("Please solve the CAPTCHA manually in the opened browser window.")
        input("After solving, press Enter here to continue...")
        return True

    # Try to accept cookie/consent dialogs (common button texts)
    for text in ("i agree", "accept all", "accept", "agree"):
        try:
            btn = await page.query_selector(f"button:has-text('{text}')")
            if btn:
                await btn.click()
                print(f"Clicked consent button: '{text}'")
                # small wait for any navigation triggered by consent
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                return False
        except Exception:
            pass

    return False

async def main():
    os.makedirs(PROFILE_DIR, exist_ok=True)

    async with async_playwright() as p:
        # Persistent context: preserves cookies, localStorage, etc.
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/116.0.0.0 Safari/537.36"
            ),
        )

        try:
            page = await browser.new_page()
            # Add stealth script to run before any page scripts
            await page.add_init_script(STEALTH_JS)

            print("Navigating to https://www.google.com ...")
            try:
                await page.goto("https://www.google.com", wait_until="networkidle", timeout=60000)
            except PWTimeoutError:
                # still continue to attempt detection/screenshot
                print("⚠️ Navigation timeout, continuing to inspect page content...")

            # short pause for dynamic UI
            await page.wait_for_timeout(1000)

            # handle captcha/consent if present
            blocked_or_consent = await solve_flow(page)
            if blocked_or_consent:
                # If captcha was found and (hopefully) solved manually, continue
                pass

            # Try to find search box with multiple selectors
            search_box = await find_search_box(page, timeout=30000)
            if not search_box:
                print("❌ Could not find the search box. Saving diagnostic files...")
                await page.screenshot(path=NO_SEARCHBOX_SCREENSHOT, full_page=True)
                try:
                    body_text = await page.inner_text("body")
                except Exception:
                    body_text = await page.content()
                with open(BODY_DUMP, "w", encoding="utf-8") as f:
                    f.write(body_text)
                print("Saved:", NO_SEARCHBOX_SCREENSHOT, "and", BODY_DUMP)
                raise SystemExit("Search box not found. Inspect saved files for troubleshooting.")

            # Type search query in a human-like manner
            query = "Gen AI update latest news"
            await search_box.click()
            # simple human-like typing (character delay)
            for ch in query:
                await page.keyboard.type(ch, delay=80)
            await page.keyboard.press("Enter")

            # wait for results
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except PWTimeoutError:
                print("⚠️ Results load timeout, but continuing to inspect page...")

            await page.wait_for_timeout(1500)

            # If page blocked after search, screenshot and exit
            body_low = (await page.inner_text("body")).lower()
            if "unusual traffic" in body_low or "recaptcha" in body_low:
                print("⚠️ Block detected after search. Saving screenshot.")
                await page.screenshot(path=CAPTCHA_SCREENSHOT, full_page=True)
                print("Saved ->", CAPTCHA_SCREENSHOT)
                return

            # Extract top result titles
            results = await page.query_selector_all("h3")
            if not results:
                print("No result titles found - possibly blocked or different page layout.")
                await page.screenshot(path=NO_RESULTS_SCREENSHOT, full_page=True)
                print("Saved ->", NO_RESULTS_SCREENSHOT)
            else:
                print("\nTop results:")
                for i, r in enumerate(results[:10], start=1):
                    try:
                        txt = await r.inner_text()
                        print(f"{i}. {txt}")
                    except Exception:
                        pass

            print("\n✅ Done. Profile directory:", PROFILE_DIR)
            print("If CAPTCHA was shown, solve it once in the opened browser; session will be saved for next runs.")
        finally:
            # Keep browser open so you can inspect; to auto-close, uncomment the next line:
            await browser.close()
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting.")
        try:
            sys.exit(0)
        except SystemExit:
            pass
