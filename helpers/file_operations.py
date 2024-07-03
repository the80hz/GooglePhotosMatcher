import os
import shutil
import logging
from pathlib import Path

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
