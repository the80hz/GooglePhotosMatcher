from auxFunctions import search_media, create_folders, set_exif, set_file_times
import json
from PIL import Image
import os
from typing import List
from os import DirEntry


# TODO don't make destructive
# TODO fix image rotations

def merge_folder(browser_path: str, window, edited_word):
    piexif_codecs = [k.casefold() for k in ['TIF', 'TIFF', 'JPEG', 'JPG']]

    media_moved = []  # array with names of all the media already matched
    path = browser_path  # source path
    fixed_media_path = os.path.join(path, "MatchedMedia")  # destination path
    non_edited_media_path = os.path.join(path, "EditedRaw")
    error_counter = 0
    success_counter = 0
    edited_word = edited_word or "edited"
    print(edited_word)

    try:
        obj: List[DirEntry] = list(os.scandir(path))  # Convert iterator into a list to sort it
        obj.sort(key=lambda s: len(s.name))  # Sort by length to avoid name(1).jpg be processed before name.jpg
        create_folders(fixed_media_path, non_edited_media_path)
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
                title = search_media(path, original_title, media_moved, non_edited_media_path, edited_word)

            except Exception:
                print("Error on searchMedia() with file " + original_title)
                error_counter += 1
                continue

            filepath = os.path.join(path, title)
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

            os.replace(filepath, os.path.join(fixed_media_path, title))
            os.remove(os.path.join(path, entry.name))
            media_moved.append(title)
            success_counter += 1

    sucessMessage = " successes"
    errorMessage = " errors"

    # UPDATE INTERFACE
    if success_counter == 1:
        sucessMessage = " success"

    if error_counter == 1:
        errorMessage = " error"

    window['-PROGRESS_BAR-'].update(100, visible=True)
    window['-PROGRESS_LABEL-'].update(
        "Matching process finished with " + str(success_counter) + sucessMessage + " and " + str(
            error_counter) + errorMessage + ".", visible=True, text_color='#c0ffb3')
