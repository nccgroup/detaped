import sys
import os
from enum import IntEnum

class Verbosity(IntEnum):
    NONE = 0
    NORMAL = 1
    DEBUG = 2

class Logger:
    VERBOSITY = Verbosity.NORMAL
    FILEPATH = None
    USE_COLOR = True

    # Colors
    DEFAULT = '\033[0m'
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    ORANGE = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    LIGHT_GRAY = '\033[0;37m'
    DARK_GRAY = '\033[1;30m'
    LIGHT_RED = '\033[1;31m'
    LIGHT_GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    LIGHT_BLUE = '\033[1;34m'
    LIGHT_PURPLE = '\033[1;35m'
    LIGHT_CYAN = '\033[1;36m'
    WIHTE = '\033[1;37m'

    @staticmethod
    def setVerbosity(verbosity):
        if verbosity == 'none':
            Logger.VERBOSITY = Verbosity.NONE
        elif verbosity == 'debug':
            Logger.VERBOSITY = Verbosity.DEBUG
        else:
            Logger.VERBOSITY = Verbosity.NORMAL

    @staticmethod
    def setFile(filepath):
        if not os.path.isfile(filepath):
            Logger.warning(Verbosity.NORMAL, 'Output text parameter must be a file, ignoring')
            return

        # Create/Open the file
        try:
            f = open(filepath, 'w+')
            f.close()
        except OSError:
            Logger.warning(Verbosity.NORMAL, f'Failed to create or open {filepath}.')
            return

        Logger.FILEPATH = filepath

    @staticmethod
    def useColor(toggle):
        Logger.USE_COLOR = toggle

    @staticmethod
    def write(verbosity, message = '', end='\n'):
        if Logger.VERBOSITY >= verbosity:
            # Print to screen
            print(message, end=end)

            # Write to file
            if Logger.FILEPATH != None:
                try:
                    with open(Logger.FILEPATH, 'a+') as f:
                        f.write(message + end)
                except OSError:
                    pass

    @staticmethod
    def space(verbosity):
        Logger.write(verbosity)
    
    @staticmethod
    def bar(verbosity):
        Logger.write(verbosity, '-' * 75)
    
    @staticmethod
    def fatal(verbosity, error, message = ''):
        Logger.error(verbosity, message)
        sys.exit(error)

    @staticmethod
    def writePrefix(verbosity, prefix, message, color, fullColor = False):
        builder = ''
        if Logger.USE_COLOR:
            builder += color

        builder += prefix + ' '

        # If the entire text is not in color, turn off color
        if Logger.USE_COLOR and not fullColor:
            builder += Logger.DEFAULT

        builder += message

        # If the entire text is in color, turn off color at the end
        if Logger.USE_COLOR and fullColor:
            builder += Logger.DEFAULT

        Logger.write(verbosity, builder)

    @staticmethod
    def error(verbosity, message = ''):
        Logger.writePrefix(verbosity, '[-]', message, Logger.RED, True)

    @staticmethod
    def warning(verbosity, message = ''):
        Logger.writePrefix(verbosity, '[!]', message, Logger.ORANGE, True)

    @staticmethod
    def info(verbosity, message = ''):
        Logger.writePrefix(verbosity, '[*]', message, Logger.CYAN)

    @staticmethod
    def success(verbosity, message = ''):
        Logger.writePrefix(verbosity, '[+]', message, Logger.GREEN)
