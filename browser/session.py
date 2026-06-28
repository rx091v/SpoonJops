from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import BrowserContext, async_playwright

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


@asynccontextmanager
async def persistent_browser_context(
    storage_path: Path,
    headless: bool = True,
) -> AsyncIterator[BrowserContext]:
    storage_path.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(storage_path),
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            user_agent=DEFAULT_USER_AGENT,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        try:
            yield context
        finally:
            await context.close()
