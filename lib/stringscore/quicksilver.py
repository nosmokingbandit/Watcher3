# Ported from Quicksilver's scoreForAbbreviation algorithm
# https://github.com/quicksilver/Quicksilver/

SCORE_NO_MATCH = 0.0
SCORE_MATCH = 1.0
SCORE_TRAILING = 0.9
SCORE_BUFFER = 0.15
WHITESPACE_CHARACTERS = ' \t'


def score(string, abbrev):
    abbrev = abbrev.lower()
    abbrev_len = len(abbrev)
    string_len = len(string)

    # deduct some points for all remaining letters
    if abbrev_len == 0:
        return SCORE_TRAILING
    if abbrev_len > string_len:
        return SCORE_NO_MATCH

    # Search for steadily smaller portions of the abbreviation
    for i in range(abbrev_len, 0, -1):
        try:
            index = string.lower().index(abbrev[:i])
        except ValueError:
            continue  # Not found

        if index + abbrev_len > string_len:
            continue

        next_string = string[index + i:]
        next_abbrev = abbrev[i:]

        # Search what is left of the string with the rest of the abbreviation
        remaining_score = score(next_string, next_abbrev)

        if remaining_score > 0:
            result_score = index + i

            # ignore skipped characters if is first letter of a word
            if index > 0:  # if some letters were skipped
                if string[index - 1] in WHITESPACE_CHARACTERS:
                    for j in range(index - 1):
                        c = string[j]
                        result_score -= SCORE_MATCH \
                                        if c in WHITESPACE_CHARACTERS \
                                        else SCORE_BUFFER
                elif 'A' <= string[index] <= 'Z':
                    for j in range(index):
                        c = string[j]
                        result_score -= SCORE_MATCH \
                                        if 'A' <= c <= 'Z' \
                                        else SCORE_BUFFER
                else:
                    result_score -= index

            result_score += remaining_score * len(next_string)
            result_score /= string_len
            return result_score

    return SCORE_NO_MATCH


if __name__ == '__main__':
    from time import clock
    t0 = clock()
    test_string = 'a'
    for string in open('tests/words'):
        abbrev = test_string
        test_string = string
        if len(abbrev) > len(string):
            string, abbrev = abbrev, string
        score(string, abbrev)
    print('Benchmark: %ss' % (clock() - t0))
