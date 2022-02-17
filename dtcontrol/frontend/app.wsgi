import sys
sys.path.insert(0, 'var/www/dtcontrol/dtcontrol/frontend')

storedVenv = "/home/weinhuber/.local/share/virtualenvs/frontend-RWjeeMLl/bin/activate_this.py"
with open(storedVenv) as file_:
    exec(file_.read(), dict(__file__=storedVenv))

from app import app as application
