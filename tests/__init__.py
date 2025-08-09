# __init__.py

import os
import sys


# Add the root directory to the path so that the package can be imported
root_directory = os.path.abspath(os.path.dirname(__file__))
print(root_directory)
sys.path.insert(0, root_directory)

# Removed problematic logger import that was breaking tests
# from .logger import setup_logger
# setup_logger()
