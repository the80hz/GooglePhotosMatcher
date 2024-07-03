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

    # Patterns to search for
    patterns = [
        (".MP.jpg.json", ".MP.jpg", ".MP"),
        (".MP.jpg.json", ".MP.jpg", ".MP-измененный.jpg", ".MP"),
        (".MP*.jpg.json", ".MP*.jpg", ".MP*")
    ]

    moved_files = []

    for pattern_group in patterns:
        for file in source_path.glob('*.MP*'):
            if any(re.search(pattern.replace('*', '.*'), file.name) for pattern in pattern_group):
                base_name = re.sub(r'\.MP.*$', '', file.name)
                group_files = [base_name + pattern for pattern in pattern_group]

                if all((source_path / Path(f)).exists() for f in group_files):
                    logging.info(f"Found complete group: {group_files}")
                    for f in group_files:
                        src_file = source_path / Path(f)
                        dst_file = dest_path / Path(f)
                        shutil.move(str(src_file), str(dst_file))
                        logging.info(f"Moved file from {src_file} to {dst_file}")
                        moved_files.append(f)
                else:
                    logging.warning(f"Incomplete group, not moving: {group_files}")

    logging.info(f"Moved files: {moved_files}")

# Example usage
source_directory = "E:\\test src"
destination_directory = "E:\\test dest"

#source_directory = input("input source directory:\n")
#destination_directory = input("input destination directory:\n")

find_and_move_files(source_directory, destination_directory)
