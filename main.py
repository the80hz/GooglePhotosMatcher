from helpers import search_media, create_folders, set_exif, set_file_times, copy_folder, delete_dir, copy_files_only, set_video_metadata
import json
from PIL import Image, ImageOps
import os
from typing import List
from os import DirEntry
from pathlib import Path
import logging

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

        time_stamp = int(data['photoTakenTime']['timestamp'])
        logging.info(f"Processing file: {filepath}")

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
