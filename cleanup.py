def cleanup_spaces(d: iter, exclusions=None):
    exclusions = set(exclusions) if exclusions else set()

    for original_string, translation in d:
        if original_string and translation and original_string != translation:
            if original_string not in exclusions:
                if original_string[0] == ' ' and translation[0] not in {' ', ','}:
                    translation = ' ' + translation

                if original_string[-1] == ' ' and translation[-1] != ' ':
                    translation += ' '

            yield original_string, translation


def cleanup_special_symbols(s):
    # TODO: Make this mapping customizable
    return s.translate({0xfeff: None, 0x2019: "'", 0x201d: '"', 0x2014: '-'})