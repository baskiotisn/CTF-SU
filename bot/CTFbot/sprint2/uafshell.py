import threading
import subprocess
from queue import Queue
from time import time, sleep



import os
from pathlib import Path
EXEC_FILE = Path(__file__).resolve().parents[0] / "af.out"


