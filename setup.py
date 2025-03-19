# setup.py

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="valyu",
    version="1.0.8",
    author="Valyu",
    author_email="contact@valyu.network",
    maintainer="Harvey Yorke",
    maintainer_email="harvey@valyu.network",
    description="We handle the data. You handle the AI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://valyu.network",
    packages=find_packages(exclude=["tests*", "*.downloads*"]),
    package_data={
        "valyu": ["py.typed"],
    },
    exclude_package_data={
        "": ["*.pyc", "*.pyo", "*.pyd", "__pycache__", "*.so"],
    },
    install_requires=[
        "requests>=2.31.0",
        "pydantic>=2.5.2",
        "tqdm>=4.65.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
