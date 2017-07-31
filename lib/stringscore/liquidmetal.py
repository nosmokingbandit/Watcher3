# Ported from LiquidMetal
# https://github.com/rmm5t/liquidmetal

SCORE_NO_MATCH = 0.0
SCORE_MATCH = 1.0
SCORE_TRAILING = 0.8
SCORE_TRAILING_BUT_STARTED = 0.9
SCORE_BUFFER = 0.85
WORD_SEPARATORS = ' \t_-'


def score(string, abbrev):
    # short circuits
    if len(string) < len(abbrev):
        # string, abbrev = abbrev, string
        return SCORE_NO_MATCH

    if len(abbrev) == 0:
        return SCORE_TRAILING

    # match & score all
    all_scores = []
    _score_all(string, string.lower(), abbrev.lower(), -1, 0, [None] * len(string), all_scores)

    # complete miss
    if len(all_scores) == 0:
        return SCORE_NO_MATCH

    # sum per-character scores into overall scores,
    # selecting the maximum score
    max_score = 0.0
    for i in range(len(all_scores)):
        scores = all_scores[i]
        score_sum = sum(scores)
        if score_sum > max_score:
            max_score = score_sum

    # normalize max score by string length
    # s. t. the perfect match score = 1
    max_score /= len(string)

    # record maximum score & score array, return
    return max_score


def _score_all(string, search, abbrev, search_index, abbr_index, scores, all_scores):
    # save completed match scores at end of search
    if abbr_index == len(abbrev):
        # add trailing score for the remainder of the match
        started = search[0] == abbrev[0]
        trail_score = SCORE_TRAILING_BUT_STARTED if started else SCORE_TRAILING
        if None in scores:
            begin = scores.index(None)
            end = len(scores) - scores[::-1].index(None)
            fill_array(scores, trail_score, begin, end)
        # save score clone (since reference is persisted in scores)
        all_scores.append(scores[:])
        return

    # consume current char to match
    c = abbrev[abbr_index]
    abbr_index += 1

    # cancel match if a character is missing
    try:
        index = search.index(c, search_index + 1)
    except ValueError:
        return

    # match all instances of the abbreviaton char
    score_index = search_index  # score section to update
    while True:
        try:
            index = search.index(c, search_index + 1)
        except ValueError:
            break

        # score this match according to context
        if is_new_word(string, index):
            if index > 0:
                scores[index - 1] = SCORE_MATCH
                fill_array(scores, SCORE_BUFFER, score_index + 1, index - 1)
        elif is_upper_case(string, index):
            fill_array(scores, SCORE_BUFFER, score_index + 1, index)
        else:
            fill_array(scores, SCORE_NO_MATCH, score_index + 1, index)

        scores[index] = SCORE_MATCH

        # consume matched string and continue search
        search_index = index
        _score_all(string, search, abbrev, search_index, abbr_index, scores, all_scores)


def is_upper_case(string, index):
    c = string[index]
    return 'A' <= c <= 'Z'


def is_new_word(string, index):
    c = string[index - 1] if index > 0 else ''
    return c in WORD_SEPARATORS


def fill_array(array, value, begin, end):
    if end > begin:
        array[begin:end] = [value] * (end - begin)


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
