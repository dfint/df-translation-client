import sys
import multiprocessing as mp

from .app import App


def main():
    mp.freeze_support()
    App(ignore_config_file='--noconfig' in sys.argv, debug='--debug' in sys.argv).run()


main()
