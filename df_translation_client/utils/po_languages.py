import traceback
from pathlib import Path
from typing import List, Mapping, Set, Iterable, Optional, Tuple, TextIO

from df_gettext_toolkit import parse_po
from df_gettext_toolkit.fix_translated_strings import cleanup_string, fix_spaces
from dfrus.patch_charmap import get_supported_codepages, get_encoder


def get_languages(directory: Path):
    languages = set()
    for filename in directory.glob("*.po"):
        try:
            with open(directory / filename, encoding="utf-8") as file:
                languages.add(parse_po.PoReader(file).meta["Language"])
        except Exception as ex:
            traceback.print_exception(ex)

    return sorted(languages)


def filter_files_by_language(directory: Path, language):
    for filename in directory.glob("*.po"):
        with open(filename, encoding="utf-8") as file:
            try:
                if parse_po.PoReader(file).meta["Language"] == language:
                    yield filename.name
            except Exception as ex:
                traceback.print_exception(ex)


def filter_codepages(encodings: Iterable[str], strings: List[str]):  # FIXME: make async
    for encoding in encodings:
        encoder_function = get_encoder(encoding)

        try:
            for text in strings:
                encoded_text = encoder_function(text)[0]
                # Only one-byte encodings are supported (but shorter result is allowed)
                if len(encoded_text) > len(text):
                    raise ValueError
            yield encoding
        except (UnicodeEncodeError, ValueError, LookupError):
            pass  # These exceptions mean that the chosen encoding is not suitable for the file


def get_suitable_codepages_for_directory(directory: Path, language: str):  # FIXME: make async
    files = filter_files_by_language(directory, language)
    codepages = get_supported_codepages().keys()

    for file in files:
        with open(directory / file, "r", encoding="utf-8") as fn:
            po_file = parse_po.PoReader(fn)
            strings = [cleanup_string(entry.translation) for entry in po_file]
        codepages = filter_codepages(codepages, strings)

    return codepages


def get_suitable_codepages_for_file(translation_file: Path):  # FIXME: make async
    codepages = get_supported_codepages().keys()

    with open(translation_file, "r", encoding="utf-8") as fn:
        po_file = parse_po.PoReader(fn)
        translation_file_language = po_file.meta["Language"]
        strings = [cleanup_string(entry.translation) for entry in po_file]

    return filter_codepages(codepages, strings), translation_file_language


def cleanup_translations_string(
    original: str, translation: str, exclusions_leading: Optional[Set[str]], exclusions_trailing: Optional[Set[str]]
) -> str:
    return fix_spaces(original, cleanup_string(translation), exclusions_leading, exclusions_trailing)


def cleanup_dictionary(  # FIXME: make async
    raw_dict: Iterable[Tuple[str, str]], exclusions_leading: Optional[Set[str]], exclusions_trailing: Optional[Set[str]]
) -> Iterable[Tuple[str, str]]:
    return {
        (original, cleanup_translations_string(original, translation, exclusions_leading, exclusions_trailing))
        for original, translation in raw_dict
    }


def load_dictionary_raw(translation_file: TextIO) -> Tuple[Iterable[Tuple[str, str]], str]:  # FIXME: make async
    po_file = parse_po.PoReader(translation_file)
    language = po_file.meta["Language"]
    dictionary = ((entry.text, entry.translation) for entry in po_file)
    return dictionary, language


def load_dictionary_with_cleanup(translation_file: TextIO, exclusions_by_language: Mapping[str, Set[str]]):
    dictionary, language = load_dictionary_raw(translation_file)
    exclusions = exclusions_by_language.get(language, None)
    return cleanup_dictionary(dictionary, exclusions, exclusions)
