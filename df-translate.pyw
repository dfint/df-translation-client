import sys
from subprocess import Popen


if __name__ == '__main__':
    Popen("poetry run df-translate".split() + sys.argv[1:])
