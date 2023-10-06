'''
@file hook_mtcnn.py
Pyinstaller dependacies for exe compilation
'''
from PyInstaller.utils.hooks import collect_data_files

def collect_mtcnn_data_files():
    """
    Collect data files required by the 'mtcnn' library for packaging with PyInstaller.

    Returns:
    - list: A list of tuples. Each tuple contains the file's source path and the destination path.
    """
    return collect_data_files('mtcnn')

# Collect data files for the 'mtcnn' library
datas = collect_mtcnn_data_files()

print(datas)