from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from tqdm import tqdm
import argparse
import os
import sys

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

def get_cda_link(bro, url: str):
    bro.get(url)
    assert 'CDA' in bro.title
    element = bro.find_element(By.CLASS_NAME, 'pb-video-player')
    name = bro.find_element(By.ID, "naglowek")
    name = name.text
    src = element.get_attribute('src')
    return name, src

def get_cda_videos(urls: list, no_headless):
    bros = webdriver.FirefoxOptions()
    if not(no_headless):
        bros.headless = True
    bro = webdriver.Firefox(options=bros)
    links = {}
    with tqdm(total=len(urls), desc="Gathering links") as pbar:
        for url in urls:
            name, src = get_cda_link(bro, url)
            links[name] = src
            pbar.update(1)
    bro.close()
    return links
    
def generate_file(file: str, urls: dict):
    with open(file, 'w') as f:
        for url in urls:
            f.write("{} ::: {}\n".format(url, urls[url]))

def download(urls: dict, folder: str, parallel_downloads: int):
    file = open("TempDownFile.txt", "w")
    for url, value in urls.items():
        file.write("{}\n out={}.{}\n".format(value, url, value.split('.')[-1]))
    file.flush()
    os.system('aria2c -i {} -d {} -j {}'.format("TempDownFile.txt", folder, parallel_downloads))
    os.remove("TempDownFile.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help="CDA link to folder of video.", type=str)
    parser.add_argument('--file', help="Where to save download links. Ignored when downloading.", default="cda.txt")
    parser.add_argument('--download', '-d', action="store_true", help="Set this flag to download, instead of just generating file with links. (Currently uses only aria2)")
    parser.add_argument('--folder', '-f', action="store_true", help="Force program to treat link as folder.")
    parser.add_argument('--download_folder', '-F', help="Folder to save downloaded files.", default="downloaded")
    parser.add_argument('--no_headless', '-NH', action="store_true", help="Display webdriver while scrapping download links.")
    parser.add_argument('--parallel_downloads', help="Set amount of files downloaded at once by aria.", default=4)
    args = parser.parse_args()
    if 'folder' in args.url or args.folder:
        links = get_links_from_folder(args.url)
    else:
        links = [args.url]
    ready_links = get_cda_videos(links, args.no_headless)
    if args.download:
        download(ready_links, args.download_folder, args.parallel_downloads)
    else:
        generate_file(args.file, ready_links)