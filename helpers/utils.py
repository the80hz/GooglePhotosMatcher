import json
from PIL import Image, ImageOps
import os
from typing import List
from os import DirEntry
from pathlib import Path
import logging
from .file_operations import create_folders, copy_folder, delete_dir, copy_files_only
from .photo_metadata import set_exif
from .video_metadata import set_video_metadata

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def set_file_times(filepath, timestamp):
    import filedate
    f = filedate.File(filepath)
    f.set(created=timestamp, modified=timestamp)
    logging.info(f"Set file times for {filepath} to {timestamp}")

def search_media(path, title, media_moved, non_edited, edited_word):
    title = fix_title(title)
    real_title = str(title.rsplit('.', 1)[0] + "-" + edited_word + "." + title.rsplit('.', 1)[1])
    filepath = os.path.join(path, real_title)

    if not os.path.exists(filepath):
        real_title = str(title.rsplit('.', 1)[0] + "(1)." + title.rsplit('.', 1)[1])
        filepath = os.path.join(path, real_title)
        if not os.path.exists(filepath) or os.path.exists(os.path.join(path, title) + "(1).json"):
            real_title = title
            filepath = os.path.join(path, real_title)
            if not os.path.exists(filepath):
                real_title = check_if_same_name(title, title, media_moved, 1)
                filepath = str(os.path.join(path, real_title))
                if not os.path.exists(filepath):
                    title = (title.rsplit('.', 1)[0])[:47] + "." + title.rsplit('.', 1)[1]
                    real_title = str(title.rsplit('.', 1)[0] + "-" + edited_word + "." + title.rsplit('.', 1)[1])
                    filepath = os.path.join(path, real_title)
                    if not os.path.exists(filepath):
                        real_title = str(title.rsplit('.', 1)[0] + "(1)." + title.rsplit('.', 1)[1])
                        filepath = os.path.join(path, real_title)
                        if not os.path.exists(filepath):
                            real_title = title
                            filepath = os.path.join(path, real_title)
                            if not os.path.exists(filepath):
                                real_title = check_if_same_name(title, title, media_moved, 1)
                                filepath = os.path.join(path, real_title)
                                if not os.path.exists(filepath):
                                    real_title = None
                        else:
                            move_file_to_folder(filepath, os.path.join(non_edited, title))
                    else:
                        move_file_to_folder(filepath, os.path.join(non_edited, title))
        else:
            move_file_to_folder(filepath, os.path.join(non_edited, title))
    else:
        move_file_to_folder(filepath, os.path.join(non_edited, title))

    return str(real_title)

def move_file_to_folder(source, dest):
    try:
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        os.replace(source, dest)
        logging.info(f"Moved file from {source} to {dest}")
    except Exception as e:
        logging.error(f"Error moving file {source} to {dest}: {e}")

def fix_title(title):
    replace_chars = ["%", "<", ">", "=", ":", "?", "¿", "*", "#", "&", "{", "}", "\\", "@", "!", "¿", "+", "|", "\"", "'"]
    replaced = title
    for c in replace_chars:
        replaced = replaced.replace(c, "_")
    if replaced != title:
        logging.info(f"Funky image title name found: {title}")
    return replaced

def check_if_same_name(title, title_fixed, media_moved, recursion_time):
    if title_fixed in media_moved:
        title_fixed = title.rsplit('.', 1)[0] + "(" + str(recursion_time) + ")" + "." + title.rsplit('.', 1)[1]
        return check_if_same_name(title, title_fixed, media_moved, recursion_time + 1)
    else:
        return title_fixed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def merge_folder(browser_path: str, window, edited_word):
    piexif_codecs = [k.casefold() for k in ['TIF', 'TIFF', 'JPEG', 'JPG']]
    video_codecs = [k.casefold() for k in ['MP4', 'MOV']]

    media_moved = []
    original_folder = Path(browser_path)
    output_folder = original_folder.parent / (original_folder.name + " - merged")
    matched_output_folder = output_folder / "matched"
    edited_output_folder = output_folder / "edited_raw"
    unmatched_output_folder = output_folder / "unmatched"

    error_counter = 0
    success_counter = 0
    edited_word = edited_word or "edited"

    try:
        delete_dir(output_folder)
        create_folders(output_folder, matched_output_folder, unmatched_output_folder, edited_output_folder)
        copy_folder(original_folder, output_folder)

        files_in_dir: List[DirEntry] = list(os.scandir(output_folder))
        files_in_dir.sort(key=lambda s: len(s.name))
    except FileNotFoundError:
        window['-PROGRESS_LABEL-'].update("Choose a valid directory", visible=True, text_color='red')
        logging.error("Choose a valid directory.")
        return

    json_files = list(filter(lambda x: x.is_file() and x.name.endswith(".json"), files_in_dir))
    for entry in json_files:
        if entry.name == "metadata.json":
            continue

        with open(entry, encoding="utf8") as f:
            data = json.load(f)

        progress = round(json_files.index(entry) / len(json_files) * 100, 2)
        window['-PROGRESS_LABEL-'].update(str(progress) + "%", visible=True)
        window['-PROGRESS_BAR-'].update(progress, visible=True)

        original_title = data['title']

        try:
            title = search_media(output_folder, original_title, media_moved, edited_output_folder, edited_word)
        except Exception as e:
            logging.error(f"Error on search_media() with file {original_title}: {e}")
            error_counter += 1
            continue

        filepath = output_folder / title
        if title == "None":
            logging.warning(f"{original_title} not found")
            error_counter += 1
            continue

        logging.info(f"Processing file: {filepath}")
        if not os.path.exists(filepath):
            logging.error(f"File does not exist: {filepath}")
            error_counter += 1
            continue

        time_stamp = int(data['photoTakenTime']['timestamp'])

        file_extension = title.rsplit('.', 1)[1].casefold()
        if file_extension in piexif_codecs:
            try:
                set_exif(str(filepath), data['geoData']['latitude'], data['geoData']['longitude'],
                         data['geoData']['altitude'], time_stamp)
            except Exception as e:
                logging.error(f"Error setting EXIF data for {filepath}: {e}")
                error_counter += 1
                continue
        elif file_extension in video_codecs:
            try:
                set_video_metadata(str(filepath), data['geoData']['latitude'], data['geoData']['longitude'], time_stamp)
            except Exception as e:
                logging.error(f"Error setting video metadata for {filepath}: {e}")
                error_counter += 1
                continue

        set_file_times(filepath, time_stamp)

        os.replace(filepath, matched_output_folder / title)
        os.remove(output_folder / entry.name)
        media_moved.append(title)
        success_counter += 1

    success_message = " successes"
    error_message = " errors"

    if success_counter == 1:
        success_message = " success"

    if error_counter == 1:
        error_message = " error"

    copy_files_only(output_folder, unmatched_output_folder)

    window['-PROGRESS_BAR-'].update(100, visible=True)
    window['-PROGRESS_LABEL-'].update(
        "Matching process finished with " + str(success_counter) + success_message + " and " + str(
            error_counter) + error_message + ".", visible=True, text_color='#c0ffb3')
    logging.info(f"Matching process finished with {success_counter} {success_message} and {error_counter} {error_message}.")
