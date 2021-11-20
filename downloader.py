from tqdm import tqdm
import asyncio
import httpx
import os

async def downfile(url, path=''):
    try:
        split = url.split(':')
        f = path + split[-1]
        url = split[0] + ':' + split[1]
        client = httpx.AsyncClient()
        download_file = open(f, 'wb')
        async with client.stream("GET", url) as response:
            total = int(response.headers["Content-Length"])
            with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as pbar:
                status_code = response.status_code
                num_bytes_downloaded = response.num_bytes_downloaded
                async for chunk in response.aiter_bytes():
                    download_file.write(chunk)
                    pbar.update(response.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = response.num_bytes_downloaded
        await client.aclose()
        return status_code
    except Exception as e:
        print(e)
        await client.aclose()

def split(list, chunk_size):
    for i in range(0, len(list), chunk_size):
        yield list[i:i + chunk_size]

async def better_download_file(urls, path=''):
    tasks = [downfile(url, path) for url in urls]
    return [await f
                for f in asyncio.as_completed(tasks)]

def download(file, folder = '', parallel_downloads = 5):
    if folder != '':
        try:
            os.mkdir(folder)
        except FileExistsError:
            pass
    with open(file, 'r') as f:
        urls = f.readlines()
    try:
        urlsSplited = list(split(urls, int(parallel_downloads)))
    except ValueError:
        urlsSplited = [urls]
    for urls in tqdm(urlsSplited):
        responses = asyncio.run(better_download_file(urls, folder))
        while None in responses:
            print("Download failed, retrying")
            responses = asyncio.run(better_download_file(urls, folder))
