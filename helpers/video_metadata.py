import subprocess
import logging
from datetime import datetime
import os
import shutil
from pathlib import Path

def set_video_metadata(filepath: str, lat: float, lng: float, timestamp: int):
    try:
        # Verify the file path
        if not os.path.exists(filepath):
            logging.error(f"File not found: {filepath}")
            return

        # Format the location string according to ISO 6709
        location = f"{lat:+8.4f}{lng:+09.4f}"

        # Format the date and time
        date_time = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S+0000")

        # Create a temporary file path
        temp_filepath = filepath + ".temp.mp4"

        # Construct the ffmpeg command
        command = [
            'ffmpeg',
            '-i', filepath,
            '-movflags', 'use_metadata_tags',
            '-map_metadata', '0',
            '-metadata', f'Performer=ReplayKitRecording',
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
    except Exception as e:
        logging.error(f"Unexpected error setting video metadata for {filepath}: {e}")
