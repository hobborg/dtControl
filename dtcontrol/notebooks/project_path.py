import sys
import os

"""
This adds the parent folder to the python path in order to be able to import modules from other folders 
(e.g. smarter_splits).
"""

module_path = os.path.abspath(os.path.join(os.pardir))
if module_path not in sys.path:
    sys.path.append(module_path)