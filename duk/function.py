from duk.constants import DukConstants
from duk.instructions.lookup import DUK_OP_CLASSES
from duk.instructions.instructions import DukInstruction
from duk.groups.groups import DukGroup
from util.logger import Logger, Verbosity

class DukFunction:
    COUNT = 0

    @staticmethod
    def disassemble(reader, parentCount = 0):
        prefix = (parentCount * 4) * ' '
        Logger.success(Verbosity.DEBUG, f'{prefix}Function')
        prefix += 4 * ' '

        instructionCount = reader.uint32()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Instructions: {instructionCount}')
        constantCount = reader.uint32()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Constants: {constantCount}')
        functionCount = reader.uint32()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Sub Functions: {functionCount}')
        numberOfRegs = reader.uint16()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Registers: {numberOfRegs}')
        numberOfArgs = reader.uint16()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Arguments: {numberOfArgs}')
        startLine = reader.uint32()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Start Line: {startLine}')
        endLine = reader.uint32()
        Logger.info(Verbosity.DEBUG, f'{prefix}- End Line: {endLine}')
        flags = reader.uint32()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Flags: {flags:#010x}')

        # Parse instructions
        instructions = []
        if instructionCount > 0:
            Logger.info(Verbosity.DEBUG, f'{prefix}Instructions')
        for i in range(instructionCount):
            encoded = reader.uint32()
            opcode = encoded & 0xff
            Logger.info(Verbosity.DEBUG, f'{prefix}    - Instruction #{i:04}: {encoded:#010x} ({opcode:03} - {DukConstants.DUK_OP[opcode]})')

            # Append instruction
            if opcode in DUK_OP_CLASSES:
                instructions.append(DUK_OP_CLASSES[opcode](i, encoded))
            else:
                instructions.append(DukInstruction(i, encoded))

        # Parse constants
        constants = []
        if constantCount > 0:
            Logger.info(Verbosity.DEBUG, f'{prefix}Constants')
        for i in range(constantCount):
            Logger.info(Verbosity.DEBUG, f'{prefix}    - Constant #{i:03}')
            constType = reader.uint8()

            # String Constant
            if constType == DukConstants.DUK__SER_STRING:
                Logger.info(Verbosity.DEBUG, f'{prefix}        - Type: {constType} (STRING)')
                string = reader.string()
                Logger.info(Verbosity.DEBUG, f'{prefix}        - Value: {string}')
                constants.append(string)
                continue

            # Number Constant
            if constType == DukConstants.DUK__SER_NUMBER:
                Logger.info(Verbosity.DEBUG, f'{prefix}        - Type: {constType} (NUMBER)')
                double = reader.double()
                Logger.info(Verbosity.DEBUG, f'{prefix}        - Value: {double}')
                constants.append(double)
                continue

            Logger.info(Verbosity.DEBUG, f'{prefix}        - Type: {constType} (Unknown)')
            raise Exception(f'Unhandled constant type: {hex(constType)}')

        # Parse inner function
        functions = []
        if functionCount > 0:
            Logger.info(Verbosity.DEBUG, f'{prefix}Functions')
        for i in range(functionCount):
            functions.append(DukFunction.disassemble(reader, parentCount + 1))

        length = reader.uint32()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Length: {length}')
        name = reader.string()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Name: {name}')
        filename = reader.string()
        Logger.info(Verbosity.DEBUG, f'{prefix}- Filename: {filename}')
        pc2line = reader.rawString()
        Logger.info(Verbosity.DEBUG, f'{prefix}- PC2 Line: {pc2line.hex()}')

        # Parse Varmap
        varmap = {}
        foundVarmap = False
        while True:
            varmapName = reader.string()
            if varmapName == '':
                break

            # Heading
            if not foundVarmap:
                Logger.info(Verbosity.DEBUG, f'{prefix}Varmap')
                foundVarmap = True

            varmapValue = reader.uint32()
            varmap[varmapName] = varmapValue
            Logger.info(Verbosity.DEBUG, f'{prefix}    {varmapName}: {varmapValue}')

        # Parse Formals
        formals = []
        formalCount = reader.uint32()
        if formalCount != DukConstants.DUK__NO_FORMALS:
            Logger.info(Verbosity.DEBUG, f'{prefix}Formals: {formalCount}')
            for i in range(formalCount):
                formal = reader.string()
                Logger.info(Verbosity.DEBUG, f'{prefix}    {formal}')
                formals.append(formal)

        return DukFunction(instructionCount, constantCount, functionCount,
            numberOfRegs, numberOfArgs, startLine, endLine, flags,
            instructions, constants, functions, length, name, filename,
            pc2line, varmap, formals, parentCount
        )

    def __init__(self, instructionCount, constantCount, functionCount,
            numberOfRegs, numberOfArgs, startLine, endLine, flags,
            instructions, constants, functions, length, name, filename,
            pc2line, varmap, formals, parentCount = 0
        ):
        self.index = DukFunction.COUNT
        DukFunction.COUNT += 1
        self.instructionCount = instructionCount
        self.constantCount = constantCount
        self.functionCount = functionCount
        self.numberOfRegs = numberOfRegs
        self.numberOfArgs = numberOfArgs
        self.startLine = startLine
        self.endLine = endLine
        self.flags = flags
        self.instructions = instructions
        self.constants = constants
        self.functions = functions
        self.length = length
        self.name = name
        self.filename = filename
        self.pc2line = pc2line
        self.varmap = varmap
        self.formals = formals
        self.parentCount = parentCount
        self.group = DukGroup(0 if len(self.instructions) == 0 else self.instructions[0].address, self.instructions)

    def isAnonymous(self):
        return self.name == ''

    def getName(self):
        return f'FUNC_{self.index:03x}' if self.isAnonymous() else self.name

    def getArgs(self):
        args = []
        for i in range(0, self.numberOfArgs):
            args.append(f'r{i}')
        return args

    def getDefinition(self):
        return f'function {self.getName()}({", ".join(self.getArgs())})'

    def decompile(self, disableGrouping = {}):
        # Group instructions to high-level instructions
        self.group.decompile(self.constants, self.functions, self.varmap, self.formals, disableGrouping, '    ')

        for func in self.functions:
            func.decompile(disableGrouping)

        return self.group

    def toAsm(self):
        indentation = '' if self.parentCount == 0 else ((self.parentCount - 1) * 4) * ' '

        # Output
        text = ''

        # Filename
        if self.parentCount == 0:
            text += f'; File: {self.filename}\n\n'

        # Function definition
        if self.parentCount > 0:
            text += f'{indentation}{self.getName()}: ; Function({", ".join(self.getArgs())})\n'

        # Sub functions
        for func in self.functions:
            text += func.toAsm()

        # Instructions
        for ins in self.instructions:
            text += f'{indentation}{("" if self.parentCount == 0 else "    ")}{ins.address:04x}: {ins.toAsm(self.constants, self.functions, self.varmap, self.formals)}\n'

        text += '\n'
        return text

    def toString(self, group = True):
        indentation = '' if self.parentCount == 0 else (self.parentCount - 1) * '    '
        subIndentation =  '' if self.parentCount == 0 else self.parentCount * '    '

        # Output function
        text = ''

        # Filename
        if self.parentCount == 0:
            text += f'// {self.filename}\n\n'

        # Function definition
        if self.parentCount > 0:
            text += f'{indentation}{self.getDefinition()}\n'
            text += f'{indentation}{{\n'

        # Sub functions
        for func in self.functions:
            text += str(func)

        if group:
            # Groups
            prefixAddresses = self.group.hasRawAddressInstruction()
            text += self.group.toString(self.constants, self.functions, self.varmap, self.formals, subIndentation, prefixAddresses)
        else:
            # Instructions
            for ins in self.instructions:
                text += f'{indentation}{("" if self.parentCount == 0 else "    ")}/* {ins.address:04x} */'
                text += f' {ins.toString(self.constants, self.functions, self.varmap, self.formals)}\n'

        # Function end
        if self.parentCount > 0:
            text += f'{indentation}}}\n\n'
        return text

    def __str__(self):
        return self.toString()
