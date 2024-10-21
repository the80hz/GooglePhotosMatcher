import os
import subprocess

def apply_xmp_to_image(image_path, xmp_path):
    # Используем exiftool для применения XMP метаданных к изображению
    subprocess.run(['exiftool', '-tagsfromfile', xmp_path, image_path])

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

if __name__ == '__main__':
    folder_path = input('input path: ')
    process_folder(folder_path)
