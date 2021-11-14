# CDAdl - CDA downloader
This is CDA downloader, it allows user to easly get access to source of any (currently only public) video on cda.pl, it allows you to save link to file (along with it's name), download it directly (requires aria2c) and also allows you to download/list whole folder.

# Requirements
It was written in python 3.9.5 so I strongly encourage you to use this version, it also (at least for now) requires firefox and geckodriver in PATH. 
Python libraries are included in requirements.txt file, you can install them using `pip install -r requirements.txt`.

# Usage
`python cdadl.py <cda link to video/folder>` will by default get source video/s from link and save it to a file.

To download video or folder you can use `-d` flag, after it finished gathering links it saves them to temporary txt file and starts downloading them using aria2c (I plan on adding another downloaders but currently it was only one I wanted to implement)

You can get more info about it by using `-h` or `--help`flag.