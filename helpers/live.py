# this script under alpha test

import os
import shutil
from pathlib import Path
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_and_move_files(source_dir, dest_dir):
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    if not source_path.exists():
        logging.error(f"Source directory does not exist: {source_dir}")
        return

    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created destination directory: {dest_dir}")

    # Define regex patterns to match groups of files
    patterns = [
        (re.compile(r'(.*)\.MP(~?\d*)\.jpg\.json$'), [r'\1.MP\2.jpg.json', r'\1.MP\2.jpg', r'\1.MP\2']),
        (re.compile(r'(.*)\.MP(~?\d*)\.jpg\.json$'), [r'\1.MP\2.jpg.json', r'\1.MP\2.jpg', r'\1.MP-измененный\2.jpg', r'\1.MP\2']),
        (re.compile(r'(.*)\.MP.*\.jpg\.json$'), [r'\1.MP*.jpg.json', r'\1.MP*.jpg', r'\1.MP*'])
    ]

    moved_files = []

    for pattern, group_patterns in patterns:
        for file in source_path.glob('*'):
            match = pattern.match(file.name)
            if match:
                base_name = match.group(1)
                suffix = match.group(2)
                group_files = [source_path / Path(base_name + pattern.replace('*', suffix)) for pattern in group_patterns]

                if all(f.exists() for f in group_files):
                    logging.info(f"Found complete group: {group_files}")
                    for src_file in group_files:
                        dst_file = dest_path / src_file.relative_to(source_path)
                        if not dst_file.parent.exists():
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(src_file), str(dst_file))
                        logging.info(f"Moved file from {src_file} to {dst_file}")
                        moved_files.append(str(dst_file))
                else:
                    logging.warning(f"Incomplete group, not moving: {group_files}")

    logging.info(f"Moved files: {moved_files}")


# Example usage
source_directory = "E:\\test src"
destination_directory = "E:\\test dest"

#source_directory = input("input source directory:\n")
#destination_directory = input("input destination directory:\n")

find_and_move_files(source_directory, destination_directory)
