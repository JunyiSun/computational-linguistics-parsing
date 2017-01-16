#! /usr/bin/env python3.5
'''Test that your submission files work as intended.

This script makes a bunch of sanity checks. You can also generate the
`ParseTrees` file for output. Check arguments for more details.

Testing that will cause this script to error out on failure:
    - You're running on an older version of python than 3.5
    - File-specific syntax is wrong
    - The first production rule in the `Grammar` file does not have 'S'
      on the LHS.
    - A file doesn't start with an info line, or it doesn't match that
      of other files
    - You provided a `ParseTrees` file to check, but its contents don't
      match the what we generated right now.
    - You provided a predictions file to check, but it doesn't have the
      same number of lines as the `Sentences` file

Testing that will warn you on failure:
    - File names do not match submission names

This script _should_ run on a CDF machine. Run it there!

_IMPORTANT_ 'S' will always be treated as the start state when automated
testing is run. It is not required for submission that the first listed
rule's lhs is 'S', but to make sure you're not trying to use a different
start state (which will mean near complete failure for automated
testing), this script errors out unless the first rule starts with 'S
->'.

_IMPORTANT_ You are responsible for making sure that your submission
meets submission standards! This script is presented as-is and comes
with no guarantees! If you find any bugs, please email me.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from io import StringIO
from itertools import repeat
from os.path import abspath
from os.path import basename
from re import match
from sys import stderr

import nltk

try:
    from q3_utils import build_parse_tree_dictionary
    from q3_utils import check_correct_python_version
    from q3_utils import get_info_tuple
    from q3_utils import sanitize_grammar
    from q3_utils import sanitize_lexicon
    from q3_utils import sanitize_predictions
    from q3_utils import sanitize_sentences
except ImportError:
    raise ImportError(
        'Need q3_utils.py to be in the same directory as this script ({})'
        ''.format(__file__)
    )

__author__ = "Sean Robertson"

def _errcol(string):
    return '\033[91m' + string + '\033[0m'

def _warncol(string):
    return '\033[93m' + string + '\033[0m'

def _okcol(string):
    return '\033[94m' + string + '\033[0m'

def main(args=None):
    '''Main function

    See module doc for description of task

    Args:
        args(list): arguments to parse. Default (None) means take from
            command line
    '''
    arg_parser = ArgumentParser(
        description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    arg_parser.add_argument('lexicon_path', help='Path to Lexicon file')
    arg_parser.add_argument('grammar_path', help='Path to Grammar file')
    arg_parser.add_argument('sentences_path', help='Path to Sentences file')
    arg_parser.add_argument(
        'parse_trees_path', nargs='?', default=None,
        help='Path to ParseTrees file. Provide this argument to check '
             'that output aligns with current Grammar, Lexicon, and '
             'Sentences files.'
    )
    arg_parser.add_argument(
        '-p', '--predictions-path', metavar='PATH', default=None,
        help='Path to "predictions" file. This file should have the '
             'same number of non-empty, non-comment lines as Sentences.'
             ' Each such line should contain only the text "Parses" or '
             '"No parses". We check whether each corresponding '
             'sentence matches that prediction'
    )
    arg_parser.add_argument(
        '-o', '--output-parse-trees-path', metavar='PATH', default=None,
        help='Path to output ParseTrees file. Puts the result of '
             'parsing Sentences into the file.'
    )
    namespace = arg_parser.parse_args(args)
    check_correct_python_version()
    # parsing/validating the various files
    info_tuple, lexicon_text, grammar_text = None, None, None
    sentences, predictions, parse_trees_to_check = None, None, None
    try:
        info_tuple = get_info_tuple(namespace.lexicon_path)
        lexicon_text = sanitize_lexicon(namespace.lexicon_path)
        get_info_tuple(namespace.grammar_path, info_tuple)
        grammar_text = sanitize_grammar(namespace.grammar_path)
        get_info_tuple(namespace.sentences_path, info_tuple)
        sentences_text = sanitize_sentences(namespace.sentences_path)
        sentences = sentences_text.split('\n')
        if namespace.parse_trees_path:
            get_info_tuple(namespace.parse_trees_path, info_tuple)
            parse_trees_to_check = build_parse_tree_dictionary(
                namespace.parse_trees_path)
        if namespace.predictions_path:
            predictions_text = sanitize_predictions(namespace.predictions_path)
            predictions = predictions_text.split('\n')
            if len(sentences) != len(predictions):
                raise ValueError(
                    'Number of sentences ({}) does not match the '
                    'number of predictions ({})'
                    ''.format(len(sentences), len(predictions))
                )
        else:
            predictions = repeat('N/A')
    except ValueError as error:
        print(_errcol('ERROR: ') + error.args[0], file=stderr)
        exit(1)
    # make sure the first production in 'Grammar' has S on the lhs
    if not match(r'^\s*S\s+->\s', grammar_text):
        print(
            _errcol('ERROR: ') + 'Your first rule in the grammar file '
            'should begin with "S ->"', file=stderr
        )
        exit(1)
    # a few warning checks
    if namespace.parse_trees_path and namespace.output_parse_trees_path and \
            abspath(namespace.parse_trees_path) == \
                abspath(namespace.output_parse_trees_path):
        print(
            _warncol('WARN: ') + "You've pointed the output and check"
            "parse tree options to the same file path. I'm going to "
            "check before I output", file=stderr)
    if basename(namespace.lexicon_path) != 'Lexicon':
        print(
            _warncol('WARN: ') + 'Your lexicon file is not named '
            '"Lexicon". Change this before submission', file=stderr)
    if basename(namespace.grammar_path) != 'Grammar':
        print(
            _warncol('WARN: ') + 'Your grammar file is not named '
            '"Grammar". Change this before submission', file=stderr)
    if basename(namespace.sentences_path) != 'Sentences':
        print(
            _warncol('WARN: ') + 'Your sentences file is not named '
            '"Sentences". Change this before submission', file=stderr)
    if namespace.parse_trees_path and \
            basename(namespace.parse_trees_path) != 'ParseTrees':
        print(
            _warncol('WARN: ') + 'Your parse trees file is not named '
            '"ParseTrees". Change this before submission', file=stderr)
    # construct grammar and parser
    grammar = nltk.grammar.CFG.fromstring(grammar_text + '\n' + lexicon_text)
    bu_parser = nltk.parse.BottomUpChartParser(grammar)
    # parse sentences
    trees_over_sentences = bu_parser.parse_sents(
        nltk.tokenize.word_tokenize(s) for s in sentences)
    # parse did not error. Now we print the results of parsing and
    # collect some text that's potentially for output. We don't write it
    # to the output file immediately because we might still error out
    out_string_io = StringIO()
    out_string_io.write('% {}, {}, {}\n\n'.format(*info_tuple))
    sfield_len = max(max(len(s) for s in sentences) + 1, 10)
    fmt_str = '{{:<{}}}| {{:10}}| {{}}'.format(sfield_len)
    print()
    print(fmt_str.format('Sentences', 'Actual', 'Expected'))
    print('-' * (sfield_len + 24))
    for trees, sentence, prediction in \
            zip(trees_over_sentences, sentences, predictions):
        sentence = sentence.strip()
        out_string_io.write(sentence)
        out_string_io.write('\n')
        tree_strings = set()
        for tree in trees:
            # Setting margin to infinity makes sure the tree is only on
            # one line
            tree_strings.add(tree.pformat(margin=float('inf')).strip())
            tree.pprint(stream=out_string_io)
        if parse_trees_to_check and \
                parse_trees_to_check[sentence] != tree_strings:
            print(
                _errcol('ERROR: ') + '"{}" trees for sentence "{}" '
                'do not match output'
                ''.format(namespace.parse_trees_path, sentence),
                file=stderr
            )
            exit(1)
        actual = 'Parses'
        if not len(tree_strings):
            actual = 'No parses'
            out_string_io.write('No parses\n')
        out_string_io.write('\n')
        expected = _errcol(prediction) if prediction != actual \
                else _okcol(prediction)
        print(fmt_str.format(sentence, actual, expected))
    print()
    if namespace.output_parse_trees_path:
        out_string_io.seek(0)
        with open(namespace.output_parse_trees_path, 'w') as out_file:
            out_file.write(out_string_io.read())

if __name__ == '__main__':
    main()
