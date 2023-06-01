from duk.instructions.instructions import DukInstruction

class DukInstructionBlank(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return ''
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name}'

class DukInstructionNop(DukInstructionBlank):
    pass

class DukInstructionInvalid(DukInstructionBlank):
    pass