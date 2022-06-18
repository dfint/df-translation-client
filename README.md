# DF Translation Client
[![Test](https://github.com/dfint/df-translation-client/actions/workflows/test.yml/badge.svg)](https://github.com/dfint/df-translation-client/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/dfint/df-translation-client/badge.svg?branch=master)](https://coveralls.io/github/dfint/df-translation-client?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/0c3352a199ffdc026390/maintainability)](https://codeclimate.com/github/dfint/df-translation-client/maintainability)

A GUI client intended to simplify usage of all the utils of the localization project (https://github.com/dfint/).

## Installation

* [Python 3](https://www.python.org) must be installed (version 3.7 or higher).  
    Also, on Linux tkinter library must be installed (e.g. run `sudo apt install python3-tk` on Ubuntu).
* Download project as zip archive and unpack it (or just clone with git if you know how to use it)


### For usage

* Double click `df-translate.pyw` file. It will take a moment before the main window appears when you run it for the first time, because it downloads required modules.

### For development

* Install `poetry`, then install the package with the following commands from the command line:
    ```bash
    pip install poetry
    ```
    (use `pip3` instead of `pip` on Linux)
    
    Other possible ways of installation of poetry see [here](https://python-poetry.org/docs/#installation).

* Install the application with poetry and run it from the command line:
    ```
    poetry install
    poetry run df-translate
    ```
    If you need to run the application from an activated virtual environment (eg. when you are using PyCharm), then use the following command:
    ```
    # poetry install
    # poetry shell
    python -m df_translation_client
    ```
    I don't recommend running with `df-translate.pyw`, cause it will remove development requirements (like `pytest`, `flake8`, etc.) from the virtual environment.

![screenshot](screenshot.png)
