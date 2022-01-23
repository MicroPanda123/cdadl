import sys
from cx_Freeze import setup, Executable

build_exe_options = {"build_exe": "build", "packages": ["anyio"], "include_files": [("geckodriver.exe", "./windows_build/geckodriver.exe")]}

base = "Win32GUI"

setup(
    name = "cdadl",
    description = "CDA downloader",
    options = {"build_exe": build_exe_options},
    executables = [Executable("../cdadl.py", base=base), Executable("../cdacli.py", base=base)]
)

