import codecs
from pathlib import Path
from typing import List

from df_gettext_toolkit import parse_po
from df_gettext_toolkit.fix_translated_strings import cleanup_string
from dfrus.patch_charmap import get_codepages, get_encoder


def get_languages(directory: Path):
    languages = set()
    for filename in directory.glob("*.po"):
        with open(directory / filename, encoding="utf-8") as file:
            languages.add(parse_po.PoReader(file).meta["Language"])

    return sorted(languages)


def filter_files_by_language(directory: Path, language):
    for filename in directory.glob("*.po"):
        with open(filename, encoding="utf-8") as file:
            if parse_po.PoReader(file).meta["Language"] == language:
                yield filename.name


def filter_codepages(encodings: List[str], strings: List[str]):
    for encoding in encodings:
        try:
            encoder_function = codecs.getencoder(encoding)
        except LookupError:
            encoder_function = get_encoder(encoding)

        try:
            for text in strings:
                encoded_text = encoder_function(text)[0]
                # Only one-byte encodings are supported (but shorter result is allowed)
                if len(encoded_text) > len(text):
                    raise ValueError
            yield encoding
        except (UnicodeEncodeError, ValueError, LookupError):
            pass


def get_suitable_codepages_for_directory(directory: Path, language: str):
    files = filter_files_by_language(directory, language)
    codepages = get_codepages().keys()
    for file in files:
        with open(directory / file, "r", encoding="utf-8") as fn:
            pofile = parse_po.PoReader(fn)
            strings = [cleanup_string(entry["msgstr"]) for entry in pofile]
        codepages = filter_codepages(codepages, strings)
    return codepages


def get_suitable_codepages_for_file(translation_file: Path):
    codepages = get_codepages().keys()
    translation_file_language = None
    if translation_file.exists():
        with open(translation_file, "r", encoding="utf-8") as fn:
            pofile = parse_po.PoReader(fn)
            translation_file_language = pofile.meta["Language"]
            strings = [cleanup_string(entry["msgstr"]) for entry in pofile]
        codepages = filter_codepages(codepages, strings)
    return codepages, translation_file_language
