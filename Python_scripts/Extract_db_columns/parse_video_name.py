import re
from datetime import datetime

def parse_video_name(video_name):
    """
    Parse a standardized video filename to extract task, date, animal name, and health group.

    The expected filename format is:
        Task_MM_DD_YY_HealthCode_Name.ext

    - Task: A string with letters (e.g., 'FoodOnly', 'FoodOnlyInhibitory', 'FoodLight').
    - Date: Month_Day_Year as integers (e.g., '2_13_25' → '2025-02-13').
    - HealthCode: One of the following:
        - 'P' or 'Y'
        - 'S#P' or 'S#Y' (e.g., 'S4P', 'S2Y')
        Health is inferred as:
            - 'saline' if code ends with 'Y'
            - 'ghrelin' if code ends with 'P'
    - Name: Animal name, word, or number (e.g., 'Paris', '5').

    Parameters:
        video_name (str): The filename of the video (with or without extension).

    Returns:
        tuple: (task, date_str, name, health), or (None, None, None, None) if parsing fails.
    """
    # Strip extension if present
    base_name = video_name.rsplit('.', 1)[0]

    # Match the pattern
    pattern = re.match(
        r'^(?P<task>[A-Za-z]+)_(?P<month>\d{1,2})_(?P<day>\d{1,2})_(?P<year>\d{2})_(?P<healthcode>(S\d+[PY]|[PY]))_(?P<name>[\w]+)$',
        base_name
    )

    if pattern:
        task = pattern.group("task")
        month = int(pattern.group("month"))
        day = int(pattern.group("day"))
        year = int("20" + pattern.group("year"))
        date_str = datetime(year, month, day).strftime("%Y-%m-%d")

        healthcode = pattern.group("healthcode")
        health = "saline" if healthcode.endswith("Y") else "ghrelin"

        name = pattern.group("name")

        return task, date_str, name, health

    # Fallback if not matched
    return None, None, None, None
