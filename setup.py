#!/usr/bin/env python3

"""
This is the setup configuration file for the virtual-router-test-kit package.
It uses setuptools to package the project, specify dependencies, and provide metadata.
"""

from setuptools import setup, find_packages


# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the needed requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read().splitlines()

setup(
    name="router-test-kit",
    version="0.1.2",
    author="Alexandros Anastasiou, alex-anast",
    author_email="anastasioyaa@gmail.com",
    description="A framework for remotely testing routers, physical or virtual.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alex-anast/router-test-kit",
    packages=find_packages(where="src"),  # Use 'src' as the package directory
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
)
