import traceback
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Set, TextIO, Tuple

from babel.messages.pofile import Catalog, read_po
from df_gettext_toolkit.utils.fix_translated_strings import cleanup_string, fix_spaces
from dfrus.patch_charmap import get_encoder, get_supported_codepages


def get_language(catalog: Catalog) -> Optional[str]:
    for key, value in catalog.mime_headers:
        if key == "Language":
            return value
    else:
        return None


def get_languages(directory: Path):
    languages = set()
    for filename in directory.glob("*.po"):
        try:
            with open(directory / filename, encoding="utf-8") as file:
                catalog = read_po(file)
                languages.add(get_language(catalog))
        except Exception as ex:
            traceback.print_exception(ex)

    return sorted(languages)


def filter_files_by_language(directory: Path, language):
    for filename in directory.glob("*.po"):
        with open(filename, encoding="utf-8") as file:
            try:
                catalog = read_po(file)
                if get_language(catalog) == language:
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
            catalog = read_po(fn)
            strings = [cleanup_string(entry.string) for entry in catalog]
        codepages = filter_codepages(codepages, strings)

    return codepages


def get_suitable_codepages_for_file(translation_file: Path):  # FIXME: make async
    codepages = get_supported_codepages().keys()

    with open(translation_file, "r", encoding="utf-8") as fn:
        catalog = read_po(fn)
        translation_file_language = get_language(catalog)
        strings = [cleanup_string(entry.string) for entry in catalog]

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
    catalog = read_po(translation_file)
    language = get_language(catalog)
    dictionary = ((entry.id, entry.string) for entry in catalog)
    return dictionary, language


def load_dictionary_with_cleanup(translation_file: TextIO, exclusions_by_language: Mapping[str, Set[str]]):
    dictionary, language = load_dictionary_raw(translation_file)
    exclusions = exclusions_by_language.get(language, None)
    return cleanup_dictionary(dictionary, exclusions, exclusions)
