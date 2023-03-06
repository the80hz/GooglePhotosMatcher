from helpers import search_media, create_folders, set_exif, set_file_times, copy_folder, delete_dir, copy_files_only
import json
from PIL import Image, ImageOps
import os
from typing import List
from os import DirEntry
from pathlib import Path


def merge_folder(browser_path: str, window, edited_word):
    piexif_codecs = [k.casefold() for k in ['TIF', 'TIFF', 'JPEG', 'JPG']]

    media_moved = []  # array with names of all the media already matched
    original_folder = Path(browser_path)  # source path
    # create output directories for merged and unmerged files
    output_folder = original_folder.parent / (original_folder.name + " - merged")
    matched_output_folder = output_folder / "matched"
    edited_output_folder = output_folder / "edited_raw"
    unmatched_output_folder = output_folder / "unmatched"

    error_counter = 0
    success_counter = 0
    edited_word = edited_word or "edited"

    try:
        # clear output folder
        delete_dir(output_folder)
        create_folders(output_folder, matched_output_folder, unmatched_output_folder, edited_output_folder)
        # copy all files to the output folder to leave the original intact
        copy_folder(original_folder, output_folder)

        files_in_dir: List[DirEntry] = list(os.scandir(output_folder))  # Convert iterator into a list to sort it
        files_in_dir.sort(key=lambda s: len(s.name))  # Sort by length to avoid name(1).jpg be processed before name.jpg
    except FileNotFoundError:
        window['-PROGRESS_LABEL-'].update("Choose a valid directory", visible=True, text_color='red')
        return

    # Get JSON files
    json_files = list(filter(lambda x: x.is_file() and x.name.endswith(".json"), files_in_dir))
    for entry in json_files:
        if entry.name == "metadata.json":
            # skip album metadata files
            continue

        with open(entry, encoding="utf8") as f:  # Load JSON into a var
            data = json.load(f)

        progress = round(json_files.index(entry) / len(json_files) * 100, 2)
        window['-PROGRESS_LABEL-'].update(str(progress) + "%", visible=True)
        window['-PROGRESS_BAR-'].update(progress, visible=True)

        # SEARCH MEDIA ASSOCIATED TO JSON
        original_title = data['title']  # Store metadata into vars

        try:
            title = search_media(output_folder, original_title, media_moved, edited_output_folder, edited_word)

        except Exception as e:
            print(f"Error on search_media() with file {original_title}: {e}")
            error_counter += 1
            continue

        filepath = output_folder / title
        if title == "None":
            print(original_title + " not found")
            error_counter += 1
            continue

        # METADATA EDITION
        time_stamp = int(data['photoTakenTime']['timestamp'])  # Get creation time
        print(filepath)

        if title.rsplit('.', 1)[1].casefold() in piexif_codecs:  # If EXIF is supported
            try:
                im = Image.open(filepath)
                # if images have a rotation specified, rewrite it rotated appropriately
                # https://github.com/python-pillow/Pillow/issues/4703
                im = ImageOps.exif_transpose(im)
                rgb_im = im.convert('RGB')
                rgb_im.save(filepath)

            except ValueError as e:
                print("Error converting to JPG in " + title)
                error_counter += 1
                continue

            try:
                set_exif(str(filepath), data['geoData']['latitude'], data['geoData']['longitude'],
                         data['geoData']['altitude'], time_stamp)

            except Exception as e:  # Error handler
                print(f"Error setting EXIF data for {filepath}")
                print(str(e))
                error_counter += 1
                continue

        # creation and modification time
        set_file_times(filepath, time_stamp)

        # MOVE FILE AND DELETE JSON
        os.replace(filepath, matched_output_folder / title)
        os.remove(output_folder / entry.name)
        media_moved.append(title)
        success_counter += 1

    success_message = " successes"
    error_message = " errors"

    # UPDATE INTERFACE
    if success_counter == 1:
        success_message = " success"

    if error_counter == 1:
        error_message = " error"

    # move any files left to the unmerged folder
    copy_files_only(output_folder, unmatched_output_folder)

    window['-PROGRESS_BAR-'].update(100, visible=True)
    window['-PROGRESS_LABEL-'].update(
        "Matching process finished with " + str(success_counter) + success_message + " and " + str(
            error_counter) + error_message + ".", visible=True, text_color='#c0ffb3')
