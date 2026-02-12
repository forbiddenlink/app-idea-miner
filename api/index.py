import os
import sys

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from apps.api.app.main import app
