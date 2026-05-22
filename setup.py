from setuptools import setup

APP = ['run.py']

DATA_FILES = [
    ('data', ['data']),
    ('models', ['models']),
]

OPTIONS = {
    'argv_emulation': True,
    'packages': ['streamlit'],
    'includes': ['streamlit.web.cli'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)