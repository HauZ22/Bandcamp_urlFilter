import asyncio

import aiohttp

from logic.metadata_scraper import scrape_bandcamp_metadata
from logic.qobuz_matcher import match_album


async def process_single_entry(session: aiohttp.ClientSession, entry):
    bc_data = await scrape_bandcamp_metadata(entry.url, session)
    if bc_data.get("status") != "success":
        return {
            "Artist": entry.artist,
            "Album": entry.title,
            "Bandcamp Link": entry.url,
            "Qobuz Link": "",
            "Status": "⚠️ Error scraping Bandcamp",
        }

    match_data = await match_album(session, bc_data)
    if match_data.get("status") == "matched":
        return {
            "Artist": bc_data.get("artist"),
            "Album": bc_data.get("album"),
            "Bandcamp Link": bc_data.get("url"),
            "Qobuz Link": match_data.get("qobuz_url"),
            "Status": "✅ Matched",
        }

    return {
        "Artist": bc_data.get("artist"),
        "Album": bc_data.get("album"),
        "Bandcamp Link": bc_data.get("url"),
        "Qobuz Link": "",
        "Status": "❌ No Match on Qobuz",
    }


async def process_batch(entries):
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(process_single_entry(session, entry)) for entry in entries]
        rows = []
        for task in asyncio.as_completed(tasks):
            rows.append(await task)
        return rows
