from logging import debug
from requests.models import Response
import asyncio
import httpx
import os
import PySimpleGUI as sg
from time import time
from datetime import timedelta

async def downfile(url, id, window, path='', debug = False):
    try:
        og_url = url
        filetext = window[id + "file"]
        bar_progress = window[id + "bar"]
        additional = window[id + "add"]
        split = url.split(':')
        f = path + split[-1]
        f = os.path.abspath(f)
        f = f.strip('\n')
        url = split[0] + ':' + split[1]
        client = httpx.AsyncClient()
        download_file = open(f, 'wb')
        f = f.split("/")[-1].split("\\")[-1]
        filetext.Update(f.split("/")[-1])
        filetext.Update(f.split("\\")[-1])
        failed = False
        async with client.stream("GET", url) as response:
            total = int(response.headers["Content-Length"])
            status_code = response.status_code
            num_bytes_downloaded = response.num_bytes_downloaded
            downloaded = num_bytes_downloaded
            start_time = time()
            async for chunk in response.aiter_bytes():
                event, values = window.read(timeout=10)
                if event == sg.WIN_CLOSED or debug:
                    failed = True
                    break
                downloaded += response.num_bytes_downloaded - num_bytes_downloaded
                downloaded_per = (downloaded / total) * 100
                bar_progress.UpdateBar(downloaded_per)
                elapsed_time = time() - start_time
                eta_time = elapsed_time * (total / downloaded) - elapsed_time
                eta_time_delta = timedelta(seconds=eta_time)
                additional.Update(f"{downloaded_per:.2f}% ETA:{eta_time_delta}")
                download_file.write(chunk)
                num_bytes_downloaded = response.num_bytes_downloaded
        await client.aclose()
        return og_url, not failed
    except Exception as e:
        print(e)
        await client.aclose()
        return og_url, False

def split(list, chunk_size):
    for i in range(0, len(list), chunk_size):
        yield list[i:i + chunk_size]

async def better_download_file(urls, window, path='', debug = False):
    tasks = [downfile(url, str(num), window, path, debug) for num, url in enumerate(urls)]
    return [await f
                for f in asyncio.as_completed(tasks)]

def download(file, folder = '', parallel_downloads = 5, progress = True, debug = False, ignore_portions = False):
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
    [sg.Text("Sekcje"), sg.ProgressBar(100, size=(47, 20), orientation="h", key="portions"), sg.Text("SekcjeETA", key="portionsETA") if not ignore_portions else None],
    [[sg.Text("def", key=str(i) + "file"), sg.ProgressBar(100, size=(47,20), orientation="H", key=str(i) + "bar"), sg.Text("add", key=str(i) + "add"), ] for i in range(parallel_downloads)],
    [sg.CloseButton("Anuluj")]]
    window = sg.Window("Downloader", layout, finalize=True)
    responses = []
    start_time = time()
    for num, urls in enumerate(urlsSplited):
        portions_per = ((num + 1) / len(urlsSplited)) * 100
        elapsed_time = time() - start_time
        eta_time = elapsed_time * (portions_per) - elapsed_time
        eta_time_delta = timedelta(seconds=eta_time)
        window.read(timeout=10)
        window["portions"].UpdateBar(portions_per)
        window["portionsETA"].Update(f"ETA:{eta_time_delta}" if portions_per != 100 else "")
        responses = [*responses, *(asyncio.run(better_download_file(urls, window, folder, debug = False)))]
    window.close()
    return responses