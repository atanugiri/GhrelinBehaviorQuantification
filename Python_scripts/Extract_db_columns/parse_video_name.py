import re
from datetime import datetime

def parse_video_name(video_name):
    task, date_str, name, health = None, None, None, None

    # Case 1: Standard format — e.g. FoodLight_9_10_24_Indigo_Y.avi
    match1 = re.match(
        r'^(?P<task>[A-Za-z]+)_(?P<month>\d{1,2})_(?P<day>\d{1,2})_(?P<year>\d{2})_(?P<name>[\w]+)_(?P<code>[YP])',
        video_name
    )
    if match1:
        task = match1.group("task")
        month = int(match1.group("month"))
        day = int(match1.group("day"))
        year = int("20" + match1.group("year"))
        date_str = datetime(year, month, day).strftime("%Y-%m-%d")
        name = match1.group("name")
        health = "saline" if match1.group("code") == "Y" else "ghrelin"
        return task, date_str, name, health

    # Case 2: e.g. FoodOnly_8_28_24_S3P_Cyan_Trial1.mp4
    match2 = re.match(
        r'^(?P<task>[A-Za-z]+)_(?P<month>\d{1,2})_(?P<day>\d{1,2})_(?P<year>\d{2})_(S\d+[PY])_(?P<name>[\w]+)',
        video_name
    )
    if match2:
        task = match2.group("task")
        month = int(match2.group("month"))
        day = int(match2.group("day"))
        year = int("20" + match2.group("year"))
        date_str = datetime(year, month, day).strftime("%Y-%m-%d")
        name = match2.group("name")
        session_code = match2.group(5)
        health = "saline" if session_code.endswith("Y") else "ghrelin"
        return task, date_str, name, health

    # Case 3: e.g. ToyLight_12_3_24_S3Y_Lilac.mp4
    match3 = re.match(
        r'^(?P<task>[A-Za-z]+)_(?P<month>\d{1,2})_(?P<day>\d{1,2})_(?P<year>\d{2})_(?P<session>S\d+[PY])_(?P<name>[\w]+)',
        video_name
    )
    if match3:
        task = match3.group("task")
        month = int(match3.group("month"))
        day = int(match3.group("day"))
        year = int("20" + match3.group("year"))
        date_str = datetime(year, month, day).strftime("%Y-%m-%d")
        name = match3.group("name")
        session_code = match3.group("session")
        health = "saline" if session_code.endswith("Y") else "ghrelin"
        return task, date_str, name, health

    # Case 4: e.g. FoodLight_9_25_24_P_Cat.avi
    match4 = re.match(
        r'^(?P<task>[A-Za-z]+)_(?P<month>\d{1,2})_(?P<day>\d{1,2})_(?P<year>\d{2})_(?P<code>[YP])_(?P<name>[\w]+)',
        video_name
    )
    if match4:
        task = match4.group("task")
        month = int(match4.group("month"))
        day = int(match4.group("day"))
        year = int("20" + match4.group("year"))
        date_str = datetime(year, month, day).strftime("%Y-%m-%d")
        name = match4.group("name")
        health = "saline" if match4.group("code") == "Y" else "ghrelin"
        return task, date_str, name, health

    return task, date_str, name, health
