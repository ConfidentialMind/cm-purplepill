"""
ConfidentialMind Container GPU Monitor (CM PurplePill)
Package initialization
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
      
    ConfidentialMind Container GPU Monitor "CM PurplePill" (c)   https://confidentialmind.com
.
"""

# Simplify imports for external users
from cmpp.collector import MetricsCollector
from cmpp.server import MetricsServer
