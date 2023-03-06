from helpers import search_media, create_folders, set_exif, set_file_times, copy_folder, delete_dir
import json
from PIL import Image
import os
from typing import List
from os import DirEntry
from pathlib import Path


# TODO don't make destructive
# TODO fix image rotations

def merge_folder(browser_path: str, window, edited_word):
    piexif_codecs = [k.casefold() for k in ['TIF', 'TIFF', 'JPEG', 'JPG']]

    media_moved = []  # array with names of all the media already matched
    original_folder = Path(browser_path)  # source path
    # create output directories for merged and unmerged files
    output_folder = original_folder.parent / (original_folder.name + " - merged")
    matched_output_folder = output_folder / "matched"
    unmatched_output_folder = output_folder / "unmatched"
    edited_output_folder = output_folder / "edited_raw"

    error_counter = 0
    success_counter = 0
    edited_word = edited_word or "edited"

    try:
        # clear output folder
        delete_dir(output_folder)
        create_folders(output_folder, matched_output_folder, unmatched_output_folder, edited_output_folder)
        # copy all files to the output folder to leave the original intact
        copy_folder(original_folder, output_folder)

        obj: List[DirEntry] = list(os.scandir(output_folder))  # Convert iterator into a list to sort it
        obj.sort(key=lambda s: len(s.name))  # Sort by length to avoid name(1).jpg be processed before name.jpg
    except FileNotFoundError:
        window['-PROGRESS_LABEL-'].update("Choose a valid directory", visible=True, text_color='red')
        return

    for entry in obj:
        if entry.is_file() and entry.name.endswith(".json"):  # Check if file is a JSON
            with open(entry, encoding="utf8") as f:  # Load JSON into a var
                data = json.load(f)

            progress = round(obj.index(entry) / len(obj) * 100, 2)
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
                    rgb_im = im.convert('RGB')
                    os.replace(filepath, filepath.rsplit('.', 1)[0] + ".jpg")
                    filepath = filepath.rsplit('.', 1)[0] + ".jpg"
                    rgb_im.save(filepath)

                except ValueError as e:
                    print("Error converting to JPG in " + title)
                    error_counter += 1
                    continue

                try:
                    set_exif(filepath, data['geoData']['latitude'], data['geoData']['longitude'],
                             data['geoData']['altitude'], time_stamp)

                except Exception as e:  # Error handler
                    print("Inexistent EXIF data for " + filepath)
                    print(str(e))
                    error_counter += 1
                    continue

            set_file_times(filepath, time_stamp)  # Windows creation and modification time

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

    window['-PROGRESS_BAR-'].update(100, visible=True)
    window['-PROGRESS_LABEL-'].update(
        "Matching process finished with " + str(success_counter) + success_message + " and " + str(
            error_counter) + error_message + ".", visible=True, text_color='#c0ffb3')
