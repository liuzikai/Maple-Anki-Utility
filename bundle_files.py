import os
import sys

# Determine if application is a script file or frozen exe
# Note: when using these path, remember they may contain spaces in path
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    lame_filename = os.path.join(application_path, "lame")
elif __file__:
    application_path = os.path.dirname(__file__)
    lame_filename = "lame"