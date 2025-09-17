# assignment.py
import asyncio
import os
import sys
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profile")
CAPTCHA_SCREENSHOT = "google_captcha_or_block.png"

STEALTH_JS = """
() => {
  try { Object.defineProperty(navigator, 'webdriver', {get: () => undefined}); } catch(e) {}
  try { Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']}); } catch(e) {}
  try { Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]}); } catch(e) {}
  try { window.chrome = { runtime: {} }; } catch(e) {}
}
"""

# list of possible selectors for Google search input across locales/versions
SEARCH_SELECTORS = [
    'input[name="q"]',
    'input[aria-label="Search"]',
    'input[aria-label="Search Google"]',
    'input[type="search"]',
    'xpath=//*[@id="APjFqb"]',       # your original
    'xpath=//input[contains(@class,"gLFyf")]'
]

async def find_search_box(page, timeout=30000):
    """
    Try multiple selectors to find the search box. Returns the element handle.
    """
    for selector in SEARCH_SELECTORS:
        try:
            # Wait for it to be visible (longer timeout)
            return await page.wait_for_selector(selector, timeout=timeout, state="visible")
        except PWTimeoutError:
            # Try next selector
            continue
    # None found
    return None

async def solve_flow(page):
    # Detect common blocking text
    body = await page.content()
    lowered = body.lower()
    if "unusual traffic" in lowered or "i'm not a robot" in lowered or "recaptcha" in lowered:
        print("⚠️ Google CAPTCHA or block detected.")
        await page.screenshot(path=CAPTCHA_SCREENSHOT, full_page=True)
        print(f"Saved screenshot -> {CAPTCHA_SCREENSHOT}")
        print("Please solve the CAPTCHA manually in the opened browser, then press Enter here to continue.")
        input()
        return True
    # If cookie consent dialog appears, try to accept common buttons
    for text in ("i agree", "accept all", "accept", "agree"):
        btn = await page.query_selector(f"button:has-text('{text}')")
        if btn:
            try:
                await btn.click()
                print(f"Clicked consent button: {text}")
                await page.wait_for_load_state("networkidle", timeout=5000)
                return False
            except Exception:
                pass
    return False

async def main():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    async with async_playwright() as p:
        # Use persistent context so cookies/cached signals persist
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
            viewport={"width": 1366, "height": 768},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/116.0.0.0 Safari/537.36"),
        )

        try:
            page = await browser.new_page()
            await page.add_init_script(STEALTH_JS)

            print("Navigating to https://www.google.com ...")
            await page.goto("https://www.google.com", wait_until="networkidle", timeout=60000)

            # Give the page a short pause for any dynamic UI
            await page.wait_for_timeout(1000)

            # handle possible consent/captcha first
            blocked_or_consent = await solve_flow(page)
            if blocked_or_consent:
                # If blocked (captcha) we rely on manual solving above
                pass

            # Try to find the search box with higher timeout and multiple selectors
            search_box = await find_search_box(page, timeout=30000)
            if not search_box:
                # final diagnostic screenshot + dump
                print("❌ Could not find the search box. Saving diagnostic screenshot and page text.")
                await page.screenshot(path="google_no_searchbox.png", full_page=True)
                body_text = await page.inner_text("body")
                with open("google_body_text.txt", "w", encoding="utf-8") as f:
                    f.write(body_text)
                print("Screenshots/text saved: google_no_searchbox.png, google_body_text.txt")
                raise SystemExit("Search box not found. See saved files for troubleshooting.")

            # type the query in a human-like manner (simple)
            query = "Gen AI update latest news"
            await search_box.click()
            await page.keyboard.type(query, delay=80)
            await page.keyboard.press("Enter")

            # wait for results
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # detect if the search results page was blocked after the search
            if "unusual traffic" in (await page.inner_text("body")).lower():
                print("⚠️ Block detected after search. Saved screenshot.")
                await page.screenshot(path=CAPTCHA_SCREENSHOT, full_page=True)
                print(f"Saved -> {CAPTCHA_SCREENSHOT}")
                return

            # Grab top result titles
            results = await page.query_selector_all("h3")
            if not results:
                print("No result titles found - possibly a blocked page. Screenshotting.")
                await page.screenshot(path="google_no_results.png", full_page=True)
            else:
                print("Top results:")
                for i, r in enumerate(results[:10], start=1):
                    try:
                        txt = await r.inner_text()
                        print(f"{i}. {txt}")
                    except Exception:
                        pass

            print("✅ Done. Profile directory:", PROFILE_DIR)
        finally:
            # Keep browser open for inspection. If you want to close automatically, uncomment:
            # await browser.close()
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
