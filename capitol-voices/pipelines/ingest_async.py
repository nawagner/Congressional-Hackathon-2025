import asyncio, aiohttp, aiofiles
from pathlib import Path

async def fetch_to_file(url: str, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            resp.raise_for_status()
            async with aiofiles.open(dst, "wb") as f:
                async for chunk in resp.content.iter_chunked(1<<20):
                    await f.write(chunk)

# Example usage:
# asyncio.run(fetch_to_file(signed_url, Path("data/hearing.mp4")))
