import setuptools
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ExMAS_Revised",
    version="0.0.7",
    author="Michal Bujak",
    author_email="",
    description="My first Python Package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    package_dir={'':"src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    entry_points={
                        'console_scripts': [
                                'hwpypcmd=hwpyp.mypy:sayHello',
                        ]
                }
)