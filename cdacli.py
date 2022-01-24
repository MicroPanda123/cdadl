from __future__ import unicode_literals
from random import choice
from bs4 import BeautifulSoup
from click import argument
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import downloader_cli as downloader
import time
from typing import Optional
import typer
from halo import Halo
import requests

app = typer.Typer()

def get_links_from_folder(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.text, "html.parser")
    links = []
    for i in soup.find_all("a"):
        link = i.get("href")
        if "video" in link and link not in links:
            links.append(link)
    numerated_links = {
        num: link for num, link in enumerate(links) if "cda" not in link
    }

    return ["https://cda.pl" + value for link, value in numerated_links.items()]

def get_cda_link(bro, url: str, max_quality):
    quality_list = '[data-quality="1080p"] [data-quality="720p"] [data-quality="480p"] [data-quality="360p"]'.split(" ")
    bro.get(url)
    assert 'CDA' in bro.title
    if max_quality:
        #time.sleep(5)
        try:
            bro.find_element(By.CLASS_NAME, 'pb-play').click()
        except Exception:
            bro.find_element(By.ID, "onetrust-accept-btn-handler").click()
            time.sleep(2)
            bro.find_element(By.CLASS_NAME, 'pb-play').click()
        time.sleep(1)
        ad = bro.find_element(By.CLASS_NAME, 'pb-ad-premium-click')
        while ad.value_of_css_property('display') != "none":
            time.sleep(1)
        try:
            bro.find_element(By.CLASS_NAME, 'pb-settings-click').click()
        except Exception:
            bro.find_element(By.ID, "onetrust-accept-btn-handler").click()
            time.sleep(2)
            bro.find_element(By.CLASS_NAME, 'pb-settings-click').click()
        for quality in quality_list:
            try:
                quality = bro.find_element(By.CSS_SELECTOR, quality)
            except NoSuchElementException:
                continue
            break
        quality.click()
    element = bro.find_element(By.CLASS_NAME, 'pb-video-player')
    name = bro.find_element(By.ID, "naglowek")
    name = name.text
    src = element.get_attribute('src')
    return name, src

def get_cda_videos(urls: list, no_headless, max_quality):
    bros = webdriver.FirefoxOptions()
    if not(no_headless):
        bros.headless = True
    bros.set_preference("media.volume_scale", "0.0")
    bro = webdriver.Firefox(options=bros)
    links = {}
    for num, url in enumerate(urls):
        name, src = get_cda_link(bro, url, max_quality)
        if name == False and src == False:
            name, src = get_cda_link(bro, url, max_quality)
        links[name] = src
    bro.close()
    return links
    
def generate_file(file: str, urls: dict):
    with open(file, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write("{} ::: {}\n".format(url, urls[url]))

def download(urls: dict, folder: str, parallel_downloads: int, debug = False):
    with open("TempDownFile.txt", 'w', encoding='utf-8') as file:
        for name, link in urls.items():
            file.write("{}:{}.{}\n".format(link, name, link.split('.')[-1]))
        file.flush()
        responses = downloader.download("TempDownFile.txt", folder + "/", parallel_downloads)
    os.remove("TempDownFile.txt")
    failed = []
    for response in responses:
        url, status = response
        if not status:
            failed.append(url)
    return failed

def gather(link: str, max_quality: Optional[bool] = False, no_headless: Optional[bool] = False):
    with Halo(text = "Zbieranie linku/ów"):
        ### Get folder links
        links = get_links_from_folder(link) if 'folder' in link else [link]
        ### Get cda links
        ready_links = get_cda_videos(links, no_headless, max_quality)
    return ready_links

@app.command("pobierz-film")
def download_movie(link: str, max_quality: Optional[bool] = False, parallel_downloads: Optional[int] = 4, download_folder: Optional[str] = "./"):
    """
    Pobierz film z CDA / Download movie from CDA
    """
    ready_links = gather(link, max_quality)

    pd = max(parallel_downloads, 1)
    failed = download(ready_links, download_folder, pd)
    if len(failed) == 0:
        print("Pobieranie zakonczone pomyslnie.")
    else:
        show = "Nie pobrano: \n"
        failed_dict = {}
        for link in failed:
            show = show + link + '\n'
            protocol, link, name = link.split(":")
            link = protocol + ":" + link
            failed_dict[name.strip('\n')[:-4]] = link
        print(f"Pobieranie nieudane:\n {show}")
        choice = input("y/N: ")
        print(choice)
        if choice in "y Y Yes YES yes".split(" "):
            download(failed_dict, download_folder, pd)

@app.command("zapisz-do-pliku")
def write_to_file(link: str, max_quality: Optional[bool] = False, file_to_save: Optional[str] = "./save.txt"):
    """
    Zapisz linki bezposrednie z CDA do pliku / Save direct links from CDA to file
    """
    ready_link = gather(link, max_quality)

    generate_file(file_to_save, ready_link)

@app.command("pobierz-link")
def get_url(link: str, max_quality: Optional[bool] = False):
    """
    Wyswietl z konsoli linki bezposrednie z CDA / Print out direct links from CDA to console
    """
    ready_links = gather(link, max_quality)

    if len(ready_links) == 1:
        for link in ready_links:
            print(ready_links[link])
    else:
        print(ready_links)

@app.command()
def version():
    """
    Wyswietl numer wersji / Print out version number
    """
    print(_VERSION)

@app.command()
def update():
    """
    Sprawdz i pobierz najnowsza wersje programu / Check for and download new version of software
    """
    with Halo(text="Sprawdzanie wersji..."):
        res = requests.get('https://api.github.com/repos/MicroPanda123/cdadl/releases/latest')
        latest_version = res.json()['html_url'].split("/")[-1]
    print("Installed version: ", _VERSION)
    print("Latest version: ", latest_version)
    if _VERSION >= latest_version:
        print("Używasz najnowszej wersji")
        return None
    print("Używasz przedawnionej wersji. Pobrać najnowszą?")
    choice = input("y/N: ")
    release_link = f'https://github.com/MicroPanda123/cdadl/releases/download/{latest_version}/release.zip'
    if choice in "y Y Yes YES yes".split(" "):
        with Halo(text="Pobieranie nowej wersji"):
            release = requests.get(res.json()['assets'][0]['browser_download_url'])
            with open('release.zip', 'wb') as f:
                f.write(release.content)
    print("Pobrano nowa wersje do release.zip")

if __name__ == "__main__":
    _VERSION = "v1.3.4"
    app()
    #update()