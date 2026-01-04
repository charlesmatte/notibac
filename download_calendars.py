#!/usr/bin/env python3
"""
Script to download calendar PDFs from Rouyn-Noranda's waste collection page.
Uses Playwright to navigate to the page and download all PDF files for a given year.

Usage:
    python download_calendars.py 2026
    python download_calendars.py 2025
"""

import argparse
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "https://www.rouyn-noranda.ca"
PAGE_URL = f"{BASE_URL}/citoyens/environnement/calendriers-des-collectes"
ROOT_DIR = Path("calendars")


async def download_calendars(year: str):
    """Navigate to the calendar page and download all PDFs for the given year."""

    output_dir = ROOT_DIR / year

    # Create output directory structure (calendars/<year>/)
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print(f"Navigating to {PAGE_URL}...")
        await page.goto(PAGE_URL, wait_until="networkidle")

        # Find all links containing the year in the URL path (e.g., Calendriers-2026)
        links = await page.query_selector_all(f'a[href*="Calendriers-{year}"]')

        print(f"Found {len(links)} PDF links for {year} calendars")

        if len(links) == 0:
            print(f"No calendars found for year {year}")
            await browser.close()
            return []

        downloaded = []
        for link in links:
            href = await link.get_attribute("href")
            if not href:
                continue

            # Build full URL if relative
            if href.startswith("/"):
                full_url = BASE_URL + href
            else:
                full_url = href

            # Extract filename from URL
            filename = href.split("/")[-1]
            output_path = output_dir / filename

            print(f"Downloading: {filename}")

            try:
                # Download the PDF
                response = await page.request.get(full_url)

                if response.ok:
                    content = await response.body()
                    with open(output_path, "wb") as f:
                        f.write(content)
                    downloaded.append(filename)
                    print(f"  -> Saved to {output_path}")
                else:
                    print(f"  -> Failed to download: HTTP {response.status}")
            except Exception as e:
                print(f"  -> Error downloading: {e}")

        await browser.close()

        print(f"\nDownload complete!")
        print(f"Successfully downloaded {len(downloaded)} files to {output_dir}/")

        return downloaded


def main():
    parser = argparse.ArgumentParser(
        description="Download waste collection calendar PDFs from Rouyn-Noranda"
    )
    parser.add_argument(
        "year",
        type=str,
        help="The year to download calendars for (e.g., 2026)",
    )
    args = parser.parse_args()

    asyncio.run(download_calendars(args.year))


if __name__ == "__main__":
    main()
