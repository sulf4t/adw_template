import os
import sys

ADWS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ADWS, "adw_modules"))
sys.path.insert(0, ADWS)
