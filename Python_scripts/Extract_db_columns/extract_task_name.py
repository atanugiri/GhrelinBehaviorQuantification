import os

def extract_task_name(filename):
    # Remove file extension
    filename = os.path.splitext(filename)[0]
    # Split and join first two words as task
    parts = filename.split('_')
    if len(parts) >= 2:
        return f"{parts[0].lower()}_{parts[1].lower()}"
    return None