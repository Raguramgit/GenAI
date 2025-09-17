from playwright.async_api import async_playwright
import asyncio

# Function to demonstrate key functions using Playwright
async def playwright_function():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        #navigate to a website
        await page.goto("https://google.com")
        await page.wait_for_timeout(50000)
        await browser.close()

# To run the function, use an async event loop in your main script
if __name__ == "__main__":
    asyncio.run(playwright_function())
