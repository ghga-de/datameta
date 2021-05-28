"""Module containing utility functions and classes for
use in the test framework.
"""

import os

base_dir = os.path.dirname(__file__)

def get_auth_header(apikey:str) -> dict:
    return {
            "Authorization": f"Bearer {apikey}"
            }

def get_file_path(name:str) -> str:
    """Returns the absolute path to the test file given its name"""
    return os.path.join(base_dir, "fixtures", "files", name)
