"""
ConfidentialMind PurplePill
CM PurplePill is a GPU metrics exporter, with Kubernetes pod-level GPU usage tracking.
"""

from setuptools import setup, find_packages
import os
from cmpp import __version__

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define package data (non-Python files to include)
package_data = {
    "cmpp": ["systemd/*"]
}

# Define scripts or entry points
entry_points = {
    "console_scripts": [
        "cmpp=cmpp.main:main",
    ],
}

setup(
    name="cm-purplepill",
    version=__version__,
    author="ConfidentialMind",
    author_email="your.email@example.com",  # Replace with your email
    description="ConfidentialMind Container GPU Monitor (CM PurplePill)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ConfidentialMind/cm-purplepill",
    packages=find_packages(),
    package_data=package_data,
    include_package_data=True,
    entry_points=entry_points,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Update with your actual license
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
)