import os
import pyexiv2
import subprocess

def apply_xmp_to_image(image_path, xmp_path):
    image = pyexiv2.Image(image_path)
    image.readMetadata()
    
    with open(xmp_path, 'r') as xmp_file:
        xmp_data = xmp_file.read()
    
    image.modify_xmp(xmp_data)
    image.writeMetadata()

def import_photo_to_apple_photos(image_path, album_name):
    applescript_code = f"""
    on importPhoto(photoPath, albumName)
        tell application "Photos"
            if not (exists album albumName) then
                make new album with properties {{name:albumName}}
            end if
            import POSIX file photoPath into album albumName
        end tell
    end importPhoto
    
    importPhoto("{image_path}", "{album_name}")
    """
    
    subprocess.run(['osascript', '-e', applescript_code])

def process_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                image_path = os.path.join(root, file)
                xmp_path = image_path + ".xmp"
                
                if os.path.exists(xmp_path):
                    apply_xmp_to_image(image_path, xmp_path)
                    import_photo_to_apple_photos(image_path, "Photo XMP")
                else:
                    import_photo_to_apple_photos(image_path, "Photo non-XMP")

# Пример использования
folder_path = '/path/to/your/photo/folder'
process_folder(folder_path)
