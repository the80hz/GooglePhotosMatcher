import logging
from datetime import datetime
import os
from pathlib import Path
from mutagen.mp4 import MP4, MP4Tags

def set_video_metadata(filepath: str, lat: float, lng: float, timestamp: int):
    try:
        # Verify the file path
        if not os.path.exists(filepath):
            logging.error(f"File not found: {filepath}")
            return
        
        # Ensure the filepath is properly formatted
        filepath_resolved = str(Path(filepath).resolve())
        
        # Load the file using mutagen
        video = MP4(filepath_resolved)
        
        # Ensure the tags attribute is initialized
        if video.tags is None:
            video.add_tags()
        
        # Format the location string according to ISO 6709
        location = f"{lat:+.6f}{lng:+.6f}/"
        
        # Format the date and time
        date_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S")
        
        # Set metadata using Apple-specific tags
        video.tags["\xa9xyz"] = location
        video.tags["\xa9day"] = date_time
        video.tags["----:com.apple.quicktime.location.ISO6709"] = location
        video.tags["----:com.apple.quicktime.creationdate"] = date_time
        
        # Save the changes
        video.save()
        
        logging.info(f"Set video metadata for {filepath_resolved}")
    except Exception as e:
        logging.error(f"Error setting video metadata for {filepath_resolved}: {e}")

# Example usage
# set_video_metadata(r"E:\Google\123 - merged\2014-07-21 17-17-46.MP4", 37.7749, -122.4194, 1625833442)
