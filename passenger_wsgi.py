import os
import sys

# ==============================
# PROJECT ROOT
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ==============================
# VIRTUALENV SITE-PACKAGES
# ==============================
VENV_SITE_PACKAGES = "/home/miuenecd/virtualenv/theology/DigitalCampus/3.12/lib/python3.12/site-packages"

if VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

# ==============================
# DJANGO SETTINGS
# ==============================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DigitalCampus.settings")

# ==============================
# WSGI APPLICATION
# ==============================
from DigitalCampus.wsgi import application