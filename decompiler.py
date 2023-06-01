import os
from util.logger import Logger, Verbosity
from util.filereader import FileReader
from duk.function import DukFunction

class Decompiler:
    @staticmethod
    def decompile(filepath, grouping = True, asm = None, output = None, disableGrouping = {}):
        try:
            # Open file for reading
            with open(filepath, 'rb') as file:
                reader = FileReader(file)

                # Validate marker
                marker = reader.uint8()
                if marker != 0xbf:
                    if marker == None:
                        Logger.warning(Verbosity.DEBUG, f'{filepath}: No marker byte found, ignoring')
                    else:
                        Logger.warning(Verbosity.DEBUG, f'{filepath}: Invalid marker byte of 0x{marker:02X}, expecting 0xBF, ignoring')
                    return None

                # Disassemble global function
                Logger.info(Verbosity.NORMAL, f'Disassembling {filepath}')
                func = DukFunction.disassemble(reader)

                # Write to asm
                if asm != None:
                    os.makedirs(os.path.dirname(asm), exist_ok=True)
                    with open(asm, 'w') as fAsm:
                        fAsm.write(func.toAsm())

                # Write to output
                if output != None:
                    # Decompile function to high-level
                    Logger.bar(Verbosity.DEBUG)
                    Logger.info(Verbosity.NORMAL, f'Decompiling {filepath}')
                    if grouping:
                        func.decompile(disableGrouping)

                    os.makedirs(os.path.dirname(output), exist_ok=True)
                    with open(output, 'w') as fOutput:
                        fOutput.write(func.toString(grouping))

                # Check if there is any remaining data
                remaining = file.read()
                if remaining != b'':
                    Logger.warning(Verbosity.DEBUG, f'{filepath}: Failed to process excess data ({remaining.hex()})')
        except OSError:
            Logger.error(Verbosity.NORMAL, f'Failed to open {filepath}, ignoring')
            return