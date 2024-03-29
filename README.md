# CDAdl - CDA downloader 
This is a CDA downloader that allows you to easily download any (public) video on cda.pl and save the link to a file (along with its name) or download it directly and download/list the whole folder.

# Notice
Currently I switched focus to [cdadl port in rust](https://codeberg.org/MicroPanda123/cdadl_rust), this means currently no more updates. 

This one is still more than enough tbh. 

And still works which is most important.

# Requirements
It was written in python 3.9.5 so I strongly encourage you to use this version, it also (at least for now) requires firefox and [geckodriver](https://github.com/mozilla/geckodriver) in PATH. 

The required python libraries are included in the requirements.txt file, you can install them using `pip install -r requirements.txt`.

Also requires you to install tkinter, this [stack overflow answer](https://stackoverflow.com/a/74607246) will tell you how to install it.

# Usage
~~`python cdadl.py <cda link to video/folder>` will by default get source video/s link/s from a link and save it to a file.~~

~~To download a video or folder you can use the `-d` flag. After it finishes gathering links it saves them to temporary txt file and starts downloading them using the internal downloader (it's very basic, I have a plan to add support for external downloaders like aria2c or wget. Also I removed aria2c just for convenience)~~

~~You can get more info about it by using the `-h` or `--help` flag.~~

The new version has a functional GUI, but it lacks a couple of features from the CLI version. It's the first version though and I will keep updating it. I made a binary for windows in the releases tab (the default folder/file path is bugged). I haven't made a binary for linux yet because I didn't think it was necessary, y'all can use python alright, I know because I use it myself.

Windows build: <a href=https://github.com/MicroPanda123/cdadl/releases> <img src="https://img.shields.io/github/workflow/status/MicroPanda123/cdadl/windows-build"> </a>

# Build your own windows version
If you want to compile your own version into windows exe, setup.py is for that, you can simply install cx-freeze using `pip install cx_Freeze` and `python setup.py build`. You can change compile settings in setup.py, for reference see <a href=https://cx-freeze.readthedocs.io/en/latest/setup_script.html>cx-freeze documentation</a>

# Changelog

## v0.1.5
EN: Now downloader shows links that weren't downloaded.
PL: Teraz pobieracz pokazuje linki ktore nie zostaly pobrane.
