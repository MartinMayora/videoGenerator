#!/usr/bin/env python3
import os
import sys

# Ensure relative paths (./build, ./src) resolve from this file's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from gui import App

if __name__ == "__main__":
    app = App(
        client_id=os.getenv("twitch_client_id"),
        client_secret=os.getenv("twitch_client_secret"),
    )
    app.mainloop()
