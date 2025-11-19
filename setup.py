from setuptools import setup, find_packages

# Read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="ckb-textify",
    version="2.1.1",  # Increment version for the update
    author="Razwan",
    description="A comprehensive Text Normalization library for Central Kurdish (Sorani).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RazwanSiktany/ckb_textify",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "eng-to-ipa",
    ],
)