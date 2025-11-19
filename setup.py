from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="ckb-textify",
    version="3.0.0",
    author="Razwan",
    description="A comprehensive Text Normalization library for Central Kurdish (Sorani).",
    long_description=long_description,
    long_description_content_type="text/markdown",

    # Main URL (usually the repo)
    url="https://github.com/RazwanSiktany/ckb_textify",

    project_urls={
        "Live Demo": "https://ckbt-extify.streamlit.app/",
        "Source Code": "https://github.com/RazwanSiktany/ckb_textify",
        "Issue Tracker": "https://github.com/RazwanSiktany/ckb_textify/issues",
    },

    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "eng-to-ipa",
        "anyascii",
    ],
)