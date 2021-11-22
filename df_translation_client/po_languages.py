from pathlib import Path
from typing import List, Mapping, Set, Iterable, Optional, Tuple

from df_gettext_toolkit import parse_po
from df_gettext_toolkit.fix_translated_strings import cleanup_string, fix_spaces
from dfrus.patch_charmap import get_supported_codepages, get_encoder


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


def filter_codepages(encodings: Iterable[str], strings: List[str]):
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
            pass


def get_suitable_codepages_for_directory(directory: Path, language: str):
    files = filter_files_by_language(directory, language)
    codepages = get_supported_codepages().keys()

    for file in files:
        with open(directory / file, "r", encoding="utf-8") as fn:
            po_file = parse_po.PoReader(fn)
            strings = [cleanup_string(entry["msgstr"]) for entry in po_file]
        codepages = filter_codepages(codepages, strings)

    return codepages


def get_suitable_codepages_for_file(translation_file: Path):
    codepages = get_supported_codepages().keys()

    with open(translation_file, "r", encoding="utf-8") as fn:
        po_file = parse_po.PoReader(fn)
        translation_file_language = po_file.meta["Language"]
        strings = [cleanup_string(entry["msgstr"]) for entry in po_file]

    return filter_codepages(codepages, strings), translation_file_language


def cleanup_translations_string(original: str, translation: str,
                                exclusions_leading: Optional[Set[str]],
                                exclusions_trailing: Optional[Set[str]]) -> str:
    return fix_spaces(original, cleanup_string(translation), exclusions_leading, exclusions_trailing)


def cleanup_dictionary(raw_dict: Mapping[str, str],
                       exclusions_leading: Optional[Set[str]],
                       exclusions_trailing: Optional[Set[str]]) -> Mapping[str, str]:
    return {
        original: cleanup_translations_string(original, translation, exclusions_leading, exclusions_trailing)
        for original, translation in raw_dict.items()
    }


def load_dictionary_raw(translation_file) -> Tuple[Mapping[str, str], str]:
    with open(translation_file, "r", encoding="utf-8") as fn:
        po_file = parse_po.PoReader(fn)
        language = po_file.meta["Language"]
        dictionary = {entry["msgid"]: entry["msgstr"] for entry in po_file}
        return dictionary, language


def load_dictionary_with_cleanup(translation_file: Path, exclusions_by_language: Mapping[str, Set[str]]):
    dictionary, language = load_dictionary_raw(translation_file)
    exclusions = exclusions_by_language.get(language, None)
    return cleanup_dictionary(dictionary, exclusions, exclusions)
