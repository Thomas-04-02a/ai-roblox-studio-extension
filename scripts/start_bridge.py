import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bridge.main import serve

if __name__ == "__main__":
    serve()
