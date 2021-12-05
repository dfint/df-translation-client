import platform
import sys
from subprocess import run

try:
    from subprocess import CREATE_NO_WINDOW
except ImportError:
    CREATE_NO_WINDOW = 0

if __name__ == '__main__':
    if platform.system() == "Windows":
        python = "python"
    else:
        python = "python3"

    run([python] + "-m pip install poetry".split(), stdout=None)
    run("poetry install --no-dev".split())
    run("poetry run df-translate".split() + sys.argv[1:], creationflags=CREATE_NO_WINDOW)
