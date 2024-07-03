import subprocess
import logging
from datetime import datetime
import os
from pathlib import Path
import shutil

def set_video_metadata(filepath: str, lat, lng, timestamp):
    try:
        # Format the location string according to ISO 6709
        location = f"{lat:+.6f}{lng:+.6f}/"

        # Format the date and time
        date_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S")

        # Create a temporary file path
        temp_filepath = filepath + ".temp.mp4"

        # Construct the ffmpeg command
        command = [
            'ffmpeg',
            '-i', filepath,
            '-metadata', f'gps_location={location}',
            '-metadata', f'com.apple.quicktime.location.ISO6709={location}',
            '-metadata', f'creation_time={date_time}',
            '-codec', 'copy',
            temp_filepath
        ]

        # Run the command
        subprocess.run(command, check=True)

        # Replace the original file with the temporary file
        shutil.move(temp_filepath, filepath)

        logging.info(f"Set video metadata for {filepath}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error setting video metadata for {filepath}: {e}")
