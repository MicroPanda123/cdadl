from requests.models import Response
import asyncio
import httpx
import os
import PySimpleGUI as sg

async def downfile(url, id, window, path=''):
    try:
        filetext = window[id + "file"]
        bar_progress = window[id + "bar"]
        perc_progress = window[id + "perc"]
        split = url.split(':')
        f = path + split[-1]
        f = os.path.abspath(f)
        f = f.strip('\n')
        print(f)
        url = split[0] + ':' + split[1]
        client = httpx.AsyncClient()
        download_file = open(f, 'wb')
        f = f.split("/")[-1].split("\\")[-1]
        filetext.update(f.split("/")[-1])
        filetext.update(f.split("\\")[-1])
        async with client.stream("GET", url) as response:
            total = int(response.headers["Content-Length"])
            status_code = response.status_code
            num_bytes_downloaded = response.num_bytes_downloaded
            downloaded = num_bytes_downloaded
            async for chunk in response.aiter_bytes():
                event, values = window.read(timeout=10)
                if event == sg.WIN_CLOSED:
                    break
                downloaded += response.num_bytes_downloaded - num_bytes_downloaded
                downloaded_per = (downloaded / total) * 100
                bar_progress.UpdateBar(downloaded_per)
                perc_progress.update(f"{downloaded_per:.2f}%")
                download_file.write(chunk)
                num_bytes_downloaded = response.num_bytes_downloaded
        await client.aclose()
        return status_code
    except Exception as e:
        print(e)
        await client.aclose()

def split(list, chunk_size):
    for i in range(0, len(list), chunk_size):
        yield list[i:i + chunk_size]

async def better_download_file(urls, window, path=''):
    tasks = [downfile(url, str(num), window, path) for num, url in enumerate(urls)]
    return [await f
                for f in asyncio.as_completed(tasks)]

def download(file, folder = '', parallel_downloads = 5, progress = True):
    sg.theme("Dark Brown 1")
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

    layout = [[sg.Text("Downloading...")],
    [sg.Text("Sekcje"), sg.ProgressBar(len(urlsSplited), size=(47, 20), orientation="h", key="portions")],
    [[sg.Text("def", key=str(i) + "file"), sg.ProgressBar(100, size=(47,20), orientation="H", key=str(i) + "bar"), sg.Text("perc", key=str(i) + "perc"), ] for i in range(parallel_downloads)]]
    window = sg.Window("Downloader", layout, finalize=True)
    for num, urls in enumerate(urlsSplited):
        window.read(timeout=10)
        window["portions"].UpdateBar(num+1)
        responses = asyncio.run(better_download_file(urls, window, folder))
        print(responses)
        while None in responses:
            print("Download failed, retrying")
            responses = asyncio.run(better_download_file(urls, window, folder))
            return False
    window.close()
    return responses