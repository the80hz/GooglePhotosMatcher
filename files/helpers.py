import os
import shutil
from datetime import datetime
import piexif
from fractions import Fraction
import filedate
from pymediainfo import MediaInfo
from mutagen.mp4 import MP4, MP4Tags
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def create_folders(*args):
    for f in args:
        if not os.path.exists(f):
            os.mkdir(f)
            logging.info(f"Created folder: {f}")

def copy_folder(source, dest):
    shutil.copytree(source, dest, dirs_exist_ok=True)
    logging.info(f"Copied folder from {source} to {dest}")

def delete_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
        logging.info(f"Deleted directory: {path}")

def copy_files_only(source, dest):
    for entity in os.scandir(source):
        if entity.is_file():
            shutil.move(entity, dest / entity.name)
            logging.info(f"Moved file {entity.name} to {dest}")

def set_file_times(filepath, timestamp):
    f = filedate.File(filepath)
    f.set(created=timestamp, modified=timestamp)
    logging.info(f"Set file times for {filepath} to {timestamp}")

def to_deg(value, loc):
    """Convert decimal coordinates into degrees, minutes, and seconds tuple."""
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
    """Convert a number to rational."""
    f = Fraction(str(number))
    return f.numerator, f.denominator

def set_exif(filepath: str, lat, lng, altitude, timestamp):
    try:
        exif_dict = piexif.load(filepath)

        # Update date and time information
        date_time = datetime.fromtimestamp(timestamp).strftime("%Y:%m:%d %H:%M:%S")
        exif_dict['0th'][piexif.ImageIFD.DateTime] = date_time
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_time
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_time

        # GPS information
        lat_deg = to_deg(lat, ["S", "N"])
        lng_deg = to_deg(lng, ["W", "E"])

        exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
        exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
            piexif.GPSIFD.GPSLatitude: exiv_lat,
            piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
            piexif.GPSIFD.GPSLongitude: exiv_lng,
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude, 2))
        }

        exif_dict['GPS'] = gps_ifd

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filepath)
        logging.info(f"Set EXIF data for {filepath}")
    except Exception as e:
        logging.error(f"Error setting EXIF data for {filepath}: {e}")

def set_video_metadata(filepath: str, lat, lng, timestamp):
    try:
        tags = MP4(filepath)
        
        # Update GPS information (latitude and longitude)
        tags["©xyz"] = [f"+{lat}/{lng}/"]
        
        # Update creation date/time
        date_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S")
        tags["©day"] = [date_time]
        
        tags.save()
        logging.info(f"Set video metadata for {filepath}")
    except Exception as e:
        logging.error(f"Error setting video metadata for {filepath}: {e}")
