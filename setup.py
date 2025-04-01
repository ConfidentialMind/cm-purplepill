"""
ConfidentialMind PurplePill
CM PurplePill is a GPU metrics exporter, with Kubernetes pod-level GPU usage tracking.

Copyright 2025 ConfidentialMind Oy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
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