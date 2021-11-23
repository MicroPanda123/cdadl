from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import downloader
import PySimpleGUI as sg

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
    import time
    bro.get(url)
    assert 'CDA' in bro.title
    if max_quality:
        #time.sleep(5)
        bro.find_element(By.CLASS_NAME, 'pb-play').click()
        time.sleep(1)
        ad = bro.find_element(By.CLASS_NAME, 'pb-ad-premium-click')
        while ad.value_of_css_property('display') != "none":
            time.sleep(1)
        settings = bro.find_element(By.CLASS_NAME, 'pb-settings-click')
        settings.click()
        try:
            quality = bro.find_element(By.CSS_SELECTOR, '[data-quality="1080p"]')
        except NoSuchElementException:
            quality = bro.find_element(By.CSS_SELECTOR, '[data-quality="720p"]')
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
    with open(file, 'w') as f:
        for url in urls:
            f.write("{} ::: {}\n".format(url, urls[url]))

def download(urls: dict, folder: str, parallel_downloads: int):
    with open("TempDownFile.txt", "w") as file:
        for name, link in urls.items():
            file.write("{}:{}.{}\n".format(link, name, link.split('.')[-1]))
        file.flush()
        downloader.download("TempDownFile.txt", folder + "/", parallel_downloads)
    os.remove("TempDownFile.txt")
    return "finished"

if __name__ == "__main__":
    sg.theme("Dark Brown 1")
    layout = [[sg.Text("Cda Downloader", font="Any 15")],
            [sg.Text("Link do filmy/folderu CDA"), sg.Input(key="link")],
            [sg.Radio("Pobierz", "dfp", key="Down", default=True, enable_events=True), sg.Radio("Zapisz do pliku", "dfp", key="File", enable_events=True)],
            [sg.Text("Folder do pobrania"), sg.InputText(key="DownFolder", default_text=os.path.dirname(os.path.realpath(__file__))), sg.FolderBrowse(target="DownFolder"), [sg.Spin([i for i in range(1,16)], initial_value=4, key="parallel_downloads"), sg.Text('Jednoczesne pobieranie.')]],
            [sg.Text("Plik do zapisania"), sg.InputText(key="FileFile", default_text=os.path.dirname(os.path.realpath(__file__))+"/cda.txt"), sg.SaveAs()],
            [sg.Checkbox("Maksymalna jakosc (Eksperymentalne, wydluza czas zbierania linkow)", key="max_quality")],
            [sg.Button("Start"), sg.CloseButton("Close"), sg.Text("Zbieranie linkow, nie klikaj nic, program dziala w tle.", visible=False, key="Info")],
            [sg.ProgressBar(100, size=(47, 20), visible=False, key="progress")]]

    window = sg.Window("CdaDl", layout, finalize=True)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == "Start":
            window["Info"].Update(visible=True)
            window["progress"].Update(visible=True)
            if 'folder' in values["link"]:
                links = get_links_from_folder(values["link"])
            else:
                links = [values["link"]]
            ready_links = get_cda_videos(links, False, window["progress"], values["max_quality"])
            if values["Down"]:
                if download(ready_links, values["DownFolder"], values["parallel_downloads"]) == "finished":
                    sg.popup("Pobieranie zakonczone.")
            elif values["File"]:
                generate_file(values["FileFile"], ready_links)
    window.close()