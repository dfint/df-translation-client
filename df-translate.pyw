import multiprocessing as mp
import sys

from df_translation_client.app import App

if __name__ == '__main__':
    mp.freeze_support()
    App(ignore_config_file='--noconfig' in sys.argv, debug='--debug' in sys.argv).run()
