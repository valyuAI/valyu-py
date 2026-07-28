# setup.py

import pathlib
import re

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def read_version() -> str:
    """
    Single-source the version from valyu/__init__.py.

    __version__ is sent on every request as User-Agent and X-Valyu-SDK-Version,
    so a version declared in two places will eventually disagree and misreport
    which SDK build a request came from. Read it, don't repeat it.
    """
    init = pathlib.Path(__file__).parent / "valyu" / "__init__.py"
    match = re.search(
        r'^__version__\s*=\s*["\']([^"\']+)["\']',
        init.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError("Could not find __version__ in valyu/__init__.py")
    return match.group(1)


setup(
    name="valyu",
    version=read_version(),
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
        "requests>=2.31.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
