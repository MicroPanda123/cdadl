from tqdm import tqdm
import asyncio
import httpx
import os

async def downfile(url, path=''):
    try:
        og_url = url
        split = url.split(':')
        f = path + split[-1]
        f = os.path.abspath(f)
        f = f.strip('\n')
        url = split[0] + ':' + split[1]
        client = httpx.AsyncClient()
        download_file = open(f, 'wb')
        async with client.stream("GET", url) as response:
            try:
                total = int(response.headers["Content-Length"])
            except Exception:
                total = 0
            with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as pbar:
                status_code = response.status_code
                num_bytes_downloaded = response.num_bytes_downloaded
                async for chunk in response.aiter_bytes():
                    download_file.write(chunk)
                    pbar.update(response.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = response.num_bytes_downloaded
        await client.aclose()
        return og_url, True
    except Exception as e:
        print(e)
        await client.aclose()
        return og_url, False

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
    parallel_downloads = min(len(urls), parallel_downloads)
    responses = []
    for urls in tqdm(urlsSplited):
         responses = [*responses, *(asyncio.run(better_download_file(urls, folder)))]
    return responses
