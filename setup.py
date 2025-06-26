from setuptools import setup

APP = ['pdf_diff_gui_tool.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',  # 可选图标（放在同目录下）
    'packages': ['fitz', 'PIL', 'imagehash'],
    'includes': ['tkinter']
}

setup(
    app=APP,
    name='PDFDiffTool',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
