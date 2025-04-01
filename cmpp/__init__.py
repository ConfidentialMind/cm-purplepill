"""
ConfidentialMind Container GPU Monitor (CM PurplePill)
Package initialization

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

name = "cmpp"
__version__ = '0.0.2'
__logo__ = """
.
      ░░       __      __                            __
           ░░ |  \    /  |  C O N F I D E N T I A L |  |
        ░░    |   \  /   |   __    __  ____     ____|  |
            ░░|    \/    |  |  |  |  |/_   |   /  __   |
          ░░  |  |\  /|  |  |  |  |   / |  |  |  |  |  |
            ░░|  | \/ |  |  |  |  |  |  |  |  |  |__|  |
             ░|__|    |__|  |__|  |__|  |__|   \_______|
      
    Container GPU Monitor "CM PurplePill" (c) 2025 ConfidentialMind Oy https://confidentialmind.com
.
"""

# Simplify imports for external users
from cmpp.collector import MetricsCollector
from cmpp.server import MetricsServer
