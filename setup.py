# setup.py

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="valyu",
    version="2.9.7",
    author="Valyu",
    author_email="contact@valyu.ai",
    maintainer="Harvey Yorke",
    maintainer_email="harvey@valyu.ai",
    description="Deepsearch API for AI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://valyu.ai",
    packages=find_packages(exclude=["tests*", "*.downloads*"]),
    package_data={
        "valyu": ["py.typed"],
    },
    exclude_package_data={
        "": ["*.pyc", "*.pyo", "*.pyd", "__pycache__", "*.so"],
    },
    install_requires=[
        "requests==2.33.1",
        "httpx==0.28.1",
        "pydantic==2.12.5",
        "openai==2.30.0",
        "anthropic==0.86.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
