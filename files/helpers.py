import os
import shutil
from datetime import datetime
import piexif
from fractions import Fraction
import filedate


# Function to search media associated to the JSON
def search_media(path, title, media_moved, non_edited, edited_word):
    title = fix_title(title)
    real_title = str(title.rsplit('.', 1)[0] + "-" + edited_word + "." + title.rsplit('.', 1)[1])
    filepath = os.path.join(path, real_title)  # First we check if exists an edited version of the image
    if not os.path.exists(filepath):
        real_title = str(title.rsplit('.', 1)[0] + "(1)." + title.rsplit('.', 1)[1])
        filepath = os.path.join(path, real_title)  # First we check if exists an edited version of the image
        if not os.path.exists(filepath) or os.path.exists(os.path.join(path, title) + "(1).json"):
            real_title = title
            filepath = os.path.join(path, real_title)  # If not, check if exists the path with the same name
            if not os.path.exists(filepath):
                # If not, check if exists the path to the same name adding (1), (2), etc
                real_title = check_if_same_name(title, title, media_moved, 1)
                filepath = str(os.path.join(path, real_title))
                if not os.path.exists(filepath):
                    title = (title.rsplit('.', 1)[0])[:47] + "." + title.rsplit('.', 1)[
                        1]  # Sometimes title is limited to 47 characters, check also that
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
                                if not os.path.exists(filepath):  # If path not found, return null
                                    real_title = None
                        else:
                            filepath = os.path.join(path, title)  # Move original media to another folder
                            os.replace(filepath, os.path.join(non_edited, title))
                    else:
                        filepath = os.path.join(path, title)  # Move original media to another folder
                        os.replace(filepath, os.path.join(non_edited, title))
        else:
            filepath = os.path.join(path, title)  # Move original media to another folder
            os.replace(filepath, os.path.join(non_edited, title))
    else:
        filepath = os.path.join(path, title)  # Move original media to another folder
        os.replace(filepath, os.path.join(non_edited, title))

    return str(real_title)


# Supress incompatible characters
def fix_title(title):
    replace_chars = ["%", "<", ">", "=", ":", "?", "¿", "*", "#", "&", "{", "}", "\\", "@", "!", "¿", "+", "|", "\"",
                     "'"]
    replaced = title
    for c in replace_chars:
        replaced = replaced.replace(c, "_")
    if replaced != title:
        print(f"funky image title name found: {title}")
    return replaced


# Recursive function to search name if its repeated
def check_if_same_name(title, title_fixed, media_moved, recursion_time):
    if title_fixed in media_moved:
        title_fixed = title.rsplit('.', 1)[0] + "(" + str(recursion_time) + ")" + "." + title.rsplit('.', 1)[1]
        return check_if_same_name(title, title_fixed, media_moved, recursion_time + 1)
    else:
        return title_fixed


def create_folders(*args):
    for f in args:
        if not os.path.exists(f):
            os.mkdir(f)


def copy_folder(source, dest):
    shutil.copytree(source, dest, dirs_exist_ok=True)


def delete_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def copy_files_only(source, dest):
    for entity in os.scandir(source):
        if entity.is_file():
            shutil.move(entity, dest / entity.name)


def set_file_times(filepath, timestamp):
    f = filedate.File(filepath)
    f.set(created=timestamp, modified=timestamp)


def to_deg(value, loc):
    """convert decimal coordinates into degrees, minutes and seconds tuple
    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)
    return deg, min, sec, loc_value


def change_to_rational(number):
    """convert a number to rational
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return f.numerator, f.denominator


def set_exif(filepath: str, lat, lng, altitude, timestamp):
    exif_dict = piexif.load(filepath)

    date_time = datetime.fromtimestamp(timestamp).strftime("%Y:%m:%d %H:%M:%S")  # Create date object
    exif_dict['0th'][piexif.ImageIFD.DateTime] = date_time
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_time
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_time

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)

    try:
        exif_dict = piexif.load(filepath)
        lat_deg = to_deg(lat, ["S", "N"])
        lng_deg = to_deg(lng, ["W", "E"])

        exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
        exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude, 2)),
            piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
            piexif.GPSIFD.GPSLatitude: exiv_lat,
            piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
            piexif.GPSIFD.GPSLongitude: exiv_lng,
        }

        exif_dict['GPS'] = gps_ifd

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filepath)

    except Exception as e:
        print("Coordinates not settled")
        pass
