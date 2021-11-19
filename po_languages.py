import codecs
from collections import OrderedDict
from pathlib import Path
from typing import List, Mapping, Set

from df_gettext_toolkit import parse_po
from df_gettext_toolkit.fix_translated_strings import cleanup_string, fix_spaces
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
            po_file = parse_po.PoReader(fn)
            strings = [cleanup_string(entry["msgstr"]) for entry in po_file]
        codepages = filter_codepages(codepages, strings)

    return codepages


def get_suitable_codepages_for_file(translation_file: Path):
    codepages = get_codepages().keys()

    with open(translation_file, "r", encoding="utf-8") as fn:
        po_file = parse_po.PoReader(fn)
        translation_file_language = po_file.meta["Language"]
        strings = [cleanup_string(entry["msgstr"]) for entry in po_file]

    return filter_codepages(codepages, strings), translation_file_language


def load_dictionary_with_cleanup(translation_file: Path, exclusions_by_language: Mapping[str, Set[str]]):
    with open(translation_file, "r", encoding="utf-8") as fn:
        po_file = parse_po.PoReader(fn)
        meta = po_file.meta
        exclusions = exclusions_by_language.get(meta["Language"], None)
        dictionary = OrderedDict(
            (entry["msgid"],
             fix_spaces(entry["msgid"], cleanup_string(entry["msgstr"]), exclusions, exclusions))
            for entry in po_file
        )
    return dictionary


def load_dictionary_raw(translation_file):
    with open(translation_file, "r", encoding="utf-8") as fn:
        po_file = parse_po.PoReader(fn)
        language = po_file.meta["Language"]
        dictionary = {entry["msgid"]: entry["msgstr"] for entry in po_file}
    return dictionary, language
