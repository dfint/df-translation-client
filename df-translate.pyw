import sys
from subprocess import run, CREATE_NO_WINDOW


if __name__ == '__main__':
    run("poetry install --no-dev".split())
    run("poetry run df-translate".split() + sys.argv[1:], creationflags=CREATE_NO_WINDOW)
