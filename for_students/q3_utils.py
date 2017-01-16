"""A variety of methods used to aid parsing and testing in question 3

_IMPORTANT_ You are responsible for making sure that your submission
meets submission standards! This script is presented as-is and comes
with no guarantees! If you find bugs, please email me.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from os.path import isfile
from re import escape
from re import match
from string import punctuation
from sys import stderr
from sys import version_info

__author__ = "Sean Robertson"

def _sanitize_with_pattern(path, pattern):
    # "private" function. Boilerplate for file sanitization functions
    if not isfile(path):
        raise ValueError('"{}" is not a file'.format(path))
    sanitized = []
    # this pattern isn't a perfect match for a lexicon parse, but should
    # cover the average case. Let me know if you need a special rule.
    with open(path) as file_obj:
        for line_num, line in enumerate(file_obj):
            # remove comments and whitespace
            commentless = line.split('%')[0].strip()
            if not commentless:
                continue # blank line
            if not match(pattern, commentless):
                raise ValueError('Failed to parse line {} in "{}"'.format(
                    line_num + 1, path))
            sanitized.append(commentless)
    return '\n'.join(sanitized)

def sanitize_lexicon(path):
    """Read lexicon file into string, removing comments

    Args:
        path(str): path to lexicon file

    Returns:
        string of lexicon file content without comments

    Raises:
        ValueError if `path` is not a file, or a line of the file is not
        syntacticallly correct
    """
    return _sanitize_with_pattern(
        path,
        r'^[^\'"]+\s+->\s+(?P<quote>[\'"])[^\'"]+(?P=quote)'
        r'(\s*\|\s*(?P=quote)[^\'"]+(?P=quote))*\s*\|?$'
    )

def sanitize_grammar(path):
    """Read grammar file into string, removing comments

    Args:
        path(str): path to grammar file

    Returns:
        string of grammar file content without comments

    Raises:
        ValueError if `path` is not a file, or a line of the file is not
        syntacticallly correct
    """
    return _sanitize_with_pattern(
        path, r'^[^\'"]+\s+->\s+[^\'"]+((\s*\|)|\s+[^\'"]+)*\s*\|?$')

def sanitize_sentences(path):
    """Read test sentences file into string, removing comments

    Args:
        path(str): path to test sentence file

    Returns:
        string of test sentences file content without comments

    Raises:
        ValueError if `path` is not a file, or a line of the file is not
            syntacticallly correct
    """
    return _sanitize_with_pattern(
        path, r'^[^' + escape(punctuation) + r']+$')

def sanitize_predictions(path):
    """Read predictions file into string, removing comments

    Args:
        path(str): path to test sentence file

    Returns:
        string of test sentences file content without comments

    Raises:
        ValueError if `path` is not a file, or a line of the file is not
            syntacticallly correct
    """
    return _sanitize_with_pattern(path, r'^(Parses|No parses)$')

def build_parse_tree_dictionary(path):
    """Read parse tree file into dictionary, removing comments

    The file is parsed as follows:
    - The first non-empty, non-comment line is a sentence
    - The next such line is either a pretty print parse tree, or
      "No parses"
    - If the above line was a parse tree, any number of parse trees may
      follow before the next sentence
    - Look for the next sentence

    Args:
        path(str): path to parse tree (output) file

    Returns:
        a dictionary where keys are sentences and values are sets of
        strings, each string being one of the parse trees (if any), but
        _not_ in pretty print

    Raises:
        ValueError if `path` is not a file, or if the file is not
            syntactically correct
    """
    if not isfile(path):
        raise ValueError('"{}" is not a file'.format(path))
    ret = dict()
    cur_key = None
    cur_val = set()
    cur_tree = ''
    num_open = 0
    with open(path) as file_obj:
        for line_num, line in enumerate(file_obj):
            line = line.split('%')[0]
            if not line.startswith(' ' * num_open):
                raise ValueError(
                    '{}:{}: line does not start with expected indent ({})'
                    ''.format(path, line_num + 1, num_open)
                )
            line = line.strip()
            if not line:
                continue
            if line.startswith('('): # starting or inside a tree
                if not cur_key:
                    raise ValueError(
                        '{}:{}: no sentence associated with tree'
                        ''.format(path, line_num + 1)
                    )
                cur_tree += line
                num_open += line.count('(') - line.count(')')
                if num_open < 0:
                    raise ValueError('{}:{}: too many right braces ({})'.format(
                        path, line_num + 1, -num_open
                    ))
                elif num_open:
                    cur_tree += ' '
                else:
                    cur_val.add(cur_tree)
                    cur_tree = ''
            else: # sentence or "No Parses"
                if cur_tree:
                    raise ValueError('{}:{}: previous tree incomplete'.format(
                        path, line_num + 1
                    ))
                if cur_key is None:
                    cur_key = line
                    if cur_key in ret:
                        raise ValueError(
                            '{}:{}: second occurrence of sentence ("{}")'
                            ''.format(path, line_num + 1, cur_key)
                        )
                elif len(cur_val):
                    ret[cur_key] = cur_val
                    cur_key = line
                    cur_val = set()
                elif line == 'No parses':
                    ret[cur_key] = set()
                    cur_key = None
                else:
                    raise ValueError(
                        '{}:{}: expected parse tree or "No parses". Got '
                        'sentence'.format(path, line_num)
                    )
    if cur_key:
        if cur_tree:
            raise ValueError('{}: Incomplete tree by end of file'.format(path))
        if not len(cur_val):
            raise ValueError(
                '{}: No results for sentence "{}" by end of file'
                ''.format(path, cur_key)
            )
        ret[cur_key] = set(cur_val)
    return ret

def get_info_tuple(path, should_equal=None):
    '''Get info from file as triple: (name, login_id, student_id)

    Args:
        path(str): path to file
        should_equal(tuple): an optional triplet that, if set, the
            return value should match

    Returns:
        Triple (tuple) of (name(str), login_id(str), student_id(int))

    Raises:
        ValueError if `path` is not a file, first line isn't an info
            line, or info does not match should_equal
    '''
    if not isfile(path):
        raise ValueError('"{}" is not a file'.format(path))
    first_line = None
    with open(path) as file_obj:
        first_line = file_obj.readline()
    match_obj = match(
        r'^\s*%\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*(\d+)\s*\n$', first_line)
    if match_obj is None:
        raise ValueError(
            '"{}" does not begin with info line! (e.g. "% My Name, '
            'myloginid, student_number")'.format(path))
    name, login_id, student_id = match_obj.groups()
    student_id = int(student_id)
    if should_equal and (name, login_id, student_id) != should_equal:
        raise ValueError(
            'File "{}" has an info line ({}) which does not match {}'
            .format(path, (name, login_id, student_id), should_equal))
    return name, login_id, student_id

def check_correct_python_version():
    '''Make sure you're running the correct version of python, else exit'''
    if version_info.major != 3 or version_info.minor != 5:
        print("You're not running python 3.5!", file=stderr)
        exit(1)
