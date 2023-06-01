#!/usr/bin/env python3

import argparse
import os
from decompiler import Decompiler
from util.logger import Logger, Verbosity

def resolveDirectoryToFilename(input, output, basename, extension):
    if output == None:
        return None

    if os.path.isfile(input):
        # If output directory is provided, change the path to a file inside that directory
        if os.path.exists(output) and os.path.isdir(output):
            output = os.path.join(output, basename + '.' + extension)
        return output

    return output

def main(args):
    # Logger
    Logger.setVerbosity(args.verbosity)
    Logger.useColor(not args.no_ansi)
    if args.txt != None:
        Logger.setFile(args.txt)

    # Validation
    if not os.path.exists(args.input):
        Logger.fatal(Verbosity.NORMAL, 1, f'{args.input} does not exist on the filesystem.')

    if not os.path.isdir(args.input) and not os.path.isfile(args.input):
        Logger.fatal(Verbosity.NORMAL, 2, 'Unhandled input type.')

    if os.path.isdir(args.input):
        if args.output != None and os.path.isfile(args.output):
            Logger.fatal(Verbosity.NORMAL, 3, 'Input is a directory therefore the output must be a directory.')
        if args.asm != None and os.path.isfile(args.asm):
            Logger.fatal(Verbosity.NORMAL, 4, 'Input is a directory therefore the ASM must be a directory.')

    # Disable grouping options
    disableGrouping = {
        'call': args.disable_call,
        'jump': args.disable_jump,
        'if_else': args.disable_if_else,
        'if_condition': args.disable_if_condition,
        'try_catch_finally': args.disable_try_catch_finally,
        'for': args.disable_for_loop,
        'while': args.disable_while_loop,
        'init_array': args.disable_init_array,
        'init_object': args.disable_init_object,
        'get_prop': args.disable_get_prop,
        'join_operator': args.disable_join_operator,
        'double_return': args.disable_double_return,
    }

    # Create output directories / files
    inputBasename = os.path.splitext(os.path.basename(args.input.rstrip('/')))[0]
    output = resolveDirectoryToFilename(args.input, args.output, inputBasename, 'js')
    asm = resolveDirectoryToFilename(args.input, args.asm, inputBasename, 'asm.js')

    # Handle directory
    if os.path.isdir(args.input):
        for directory, subdirs, files in os.walk(args.input):
            directory = directory.rstrip('/')
            for file in files:
                filepath = os.path.join(directory, file)

                # Get the path without the input directory path
                subpath = os.path.relpath(directory, args.input)
                if subpath == '.':
                    subpath = ''

                Decompiler.decompile(filepath, not args.disable_grouping, os.path.join(asm, subpath, file) if asm != None else None, os.path.join(output, subpath, file) if output != None else None, disableGrouping)
        return

    # Handle file
    Decompiler.decompile(args.input, not args.disable_grouping, asm, output, disableGrouping)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Duktape JavaScript bytecode decompiler')
    parser.add_argument('input', help='The Duktape bytecode file or directory to be decompiled.')
    parser.add_argument('-o', '--output', required=False, help='The decompiled output JavaScript file or directory.')
    parser.add_argument('-a', '--asm', required=False, help='The output JavaScript ASM file or directory.')
    parser.add_argument('-t', '--txt', required=False, help='The command output text file.')
    parser.add_argument('-n', '--no-ansi', action='store_true', help='Disable ANSI color output.')
    parser.add_argument('-v', '--verbosity', default='normal', choices=['none', 'normal', 'debug'], help='The script output verbosity mode. (Default "normal")')

    grouping = parser.add_argument_group('Decompiler Grouping', 'Disable specific decompiler grouping functionality.')
    grouping.add_argument('--disable-grouping', action='store_true', help='Disables all grouping functionality.')
    grouping.add_argument('--disable-call', action='store_true', help='Disables call grouping.')
    grouping.add_argument('--disable-jump', action='store_true', help='Disables jump block grouping.')
    grouping.add_argument('--disable-if-else', action='store_true', help='Disables if/else block grouping.')
    grouping.add_argument('--disable-if-condition', action='store_true', help='Disables grouping if statement with preceding condition.')
    grouping.add_argument('--disable-try-catch-finally', action='store_true', help='Disables try/catch/finally block grouping.')
    grouping.add_argument('--disable-for-loop', action='store_true', help='Disables for loop block grouping.')
    grouping.add_argument('--disable-while-loop', action='store_true', help='Disables while loop block grouping.')
    grouping.add_argument('--disable-init-array', action='store_true', help='Disables grouping array initialization.')
    grouping.add_argument('--disable-init-object', action='store_true', help='Disables grouping object initialization properties.')
    grouping.add_argument('--disable-get-prop', action='store_true', help='Disables grouping get properties.')
    grouping.add_argument('--disable-join-operator', action='store_true', help='Disables grouping join operators.')
    grouping.add_argument('--disable-double-return', action='store_true', help='Disables grouping return undefined after return.')

    main(parser.parse_args())