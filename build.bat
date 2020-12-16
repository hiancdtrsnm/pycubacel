poetry run pyinstaller --onefile --log-level DEBUG --win-private-assemblies --nowindow .\pycubacel.spec && poetry run pyi-set_version .\version.rc .\dist\pycubacel.exe
