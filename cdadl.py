from __future__ import unicode_literals
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import downloader
import PySimpleGUI as sg
import time
from sys import argv

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

def get_cda_videos(urls: list, no_headless, progress, max_quality):
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
        if num == 0:
            progress.UpdateBar(0)
        else:
            progress.UpdateBar((num/len(urls))*100)
    progress.UpdateBar(100)
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
        responses = downloader.download("TempDownFile.txt", folder + "/", parallel_downloads, debug)
    os.remove("TempDownFile.txt")
    failed = []
    for response in responses:
        url, status = response
        if not status:
            failed.append(url)
    return failed

def update():
    res = requests.get('https://api.github.com/repos/MicroPanda123/cdadl/releases/latest')
    latest_version = res.json()['html_url'].split("/")[-1]
    if _VERSION >= latest_version:
        return "Uzywasz najnowszej wersji"
    release_link = f'https://github.com/MicroPanda123/cdadl/releases/download/{latest_version}/release.zip'
    sg.popup("Pobieranie nowej wersji w tle")
    release = requests.get(res.json()['assets'][0]['browser_download_url'])
    with open('release.zip', 'wb') as f:
        f.write(release.content)
    return "Pobrano nowa wersje do release.zip"

if __name__ == "__main__":
    _VERSION = "v1.3"
    sg.theme("Dark Brown 1")
    debug = False
    try: 
        debug = argv[1] == "debug"
    except IndexError:
        debug = False
    layout = [
        [sg.Text(f"Cda Downloader - {_VERSION}", font="Any 15"), sg.Button('Sprawdz wersje')],
        [
            sg.Text("Link do filmy/folderu CDA"),
            sg.Input(key="link"),
            sg.Text("Musisz cos tutaj dac.", visible=False, key="LinkWarning"),
        ],
        [
            sg.Radio(
                "Pobierz", "dfp", key="Down", default=True, enable_events=True
            ),
            sg.Radio("Zapisz do pliku", "dfp", key="File", enable_events=True),
        ],
        [
            sg.Text("Folder do pobrania"),
            sg.InputText(
                key="DownFolder",
                default_text=os.path.dirname(os.path.realpath(__file__)),
            ),
            sg.FolderBrowse(target="DownFolder"),
            [
                sg.Spin(
                    list(range(1, 16)),
                    initial_value=4,
                    key="parallel_downloads",
                ),
                sg.Text('Jednoczesne pobieranie.'),
            ],
        ],
        [
            sg.Text("Plik do zapisania"),
            sg.InputText(
                key="FileFile",
                default_text=os.path.dirname(os.path.realpath(__file__))
                + "/cda.txt",
            ),
            sg.SaveAs(),
        ],
        [
            sg.Checkbox(
                "Maksymalna jakosc (Eksperymentalne, wydluza czas zbierania linkow)",
                key="max_quality",
            )
        ],
        [
            sg.Button("Start"),
            sg.CloseButton("Zamknij"),
            sg.Text(
                "Zbieranie linkow, nie klikaj nic, program dziala w tle.",
                visible=False,
                key="Info",
            ),
        ],
        [sg.ProgressBar(100, size=(47, 20), visible=False, key="progress")],
    ]

    window = sg.Window("CdaDl", layout, finalize=True)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == "Sprawdz wersje":
            sg.popup(update())
        if event == "Start":
            if values["link"] != "" and "cda.pl" in values["link"]:
                window["LinkWarning"].Update(visible=False)
                window["Info"].Update(visible=True)
                window["progress"].UpdateBar(0)
                window["progress"].Update(visible=True)

                ### Get links from folder, ignore if link doesn't appear to be folder
                if 'folder' in values["link"]: 
                    links = get_links_from_folder(values["link"])
                else:
                    links = [values["link"]]

                ### Get cda links
                ready_links = get_cda_videos(links, False, window["progress"], values["max_quality"])

                window["Info"].Update(visible=False)
                window["progress"].Update(visible=False)
                if values["Down"]:
                    pd = max(values["parallel_downloads"], 1)
                    failed = download(ready_links, values["DownFolder"], pd, debug)
                    if len(failed) == 0:
                        sg.popup("Pobieranie zakonczone pomyslnie.", )
                    else:
                        show = "Nie pobrano: \n"
                        failed_dict = {}
                        for link in failed:
                            print(link)
                            show = show + link + '\n'
                            protocol, link, name = link.split(":")
                            link = protocol + ":" + link
                            failed_dict[name.strip('\n')[:-4]] = link
                        choice, _ = sg.Window('Pobieranie nieudane', [[sg.T(show + "Czy chcesz spróbować pobrać pliki których nie udało się pobrać?")], [sg.Yes(s=10, button_text="Tak"), sg.No(s=10, button_text="Nie")]], disable_close=True).read(close=True)
                        print(choice)
                        if choice == "Tak":
                            # with open("log.txt", 'w', encoding="utf-8") as log:
                            #     log.write(f"---Original:\n {ready_links}\n\n")
                            #     log.write(f"---Failed:\n {failed_dict}")
                            download(failed_dict, values["DownFolder"], pd)
                elif values["File"]:
                    generate_file(values["FileFile"], ready_links)
                    sg.popup("Linki zapisano do pliku")
            elif values["link"] == "":
                window["LinkWarning"].Update(visible=True)
            else:
                window["LinkWarning"].Update(visible=True)
                window["LinkWarning"].Update(value="Link powinien prowadzić do cda.pl")
    window.close()
