# AC-icons

Asheron's Call Icon Database Editor

![AC-icons Screenshot](https://i.imgur.com/dHPdJ5N.png)

I exported all of the icons from the AC Icon Viewer that has been floating around for years. Then I matched those icons with their names from the database. I then did a few passes with mistral and llava to try and get decent keywords.

This python application is designed for content creators to be able to reference the 10,000 icons present in the portal.dat file.

There are 2 applications. The editor (`icon_editor.py`) and the viewer (`icon_viewer.py`). The viewer is just a lightweight viewer of the database with searching .

## Version 2.0 Changes

I went and found all the mismatched icons of various sizes and added them. Mostly UI icons. I then added in categories of the icons, but let me tell you... they suck. I'm going to have to do some more work on that. I also tweaked some bugs that were in dark mode. Enjoy.

## Features

1. Paginated Search looks in all fields for matches.
2. Double click to edit any field, changes are saved to local database
3. `export_changes.py` is a simple script to export the changes from the database to a json file that can be sent to me to include in the main database. This script relies on the original `source/acicons_orginal.db` file to be untouched.
4. Configurable 
```
DB_PATH = "acicons.db"
ICON_SIZE = 32
WINDOW_TITLE = "Asheron's Call Icon Database Editor"
BG_COLOR = "#f0f0f0"
FONT_COLOR = "#000000"
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 9
COLUMN_WIDTHS = {
    'icon': 50,
    'icon_id': 80,
    'name': 150,
    'keywords': 300,
    'metadata': 300
}
PAGE_SIZE = 100

KEYWORDS_POPUP_WIDTH = 60
KEYWORDS_POPUP_HEIGHT = 20
```

## Installation

1. requirements.txt is included, so you can just run `pip install -r requirements.txt` to get all the dependencies (only `pillow` is the requirement).
2. `python icon_editor.py` will start the application.
3. I've included `source\weenies_all_icons_hex_latest.csv` which is the master list I used building the database of weenie ids, names, icon values, etc. Good for searching.

![Editing screenshot](https://i.imgur.com/hr3ohyH.png)

## Icon Viewer

You can right click in the middle of the item to get the metadata edit.

![Icon Viewer](https://i.imgur.com/DdNV7f3.png)

![Icon Viewer](https://i.imgur.com/bH4jcdE.png)