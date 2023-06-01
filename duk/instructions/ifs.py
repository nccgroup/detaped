from duk.instructions.instructions import DukInstruction

class DukInstructionIf(DukInstruction):
    def getConditionStatement(self, constants):
        raise RuntimeError()
    def getDestinationAddress(self):
        return self.address + 2
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}if ({self.getConditionStatement(constants)}); jump {self.getDestinationAddress():04x};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        raise RuntimeError()

class DukInstructionIfC(DukInstructionIf):
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.formatConst(self.constBC(constants))}, {self.getDestinationAddress():04x}'

class DukInstructionIfR(DukInstructionIf):
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.bc}, {self.getDestinationAddress():04x}'

class DukInstructionIfTrueR(DukInstructionIfR):
    def getConditionStatement(self, constants):
        return f'r{self.bc} == true'

class DukInstructionIfTrueC(DukInstructionIfC):
    def getConditionStatement(self, constants):
        return f'{self.formatConst(self.constBC(constants))} == true'

class DukInstructionIfFalseR(DukInstructionIfR):
    def getConditionStatement(self, constants):
        return f'r{self.bc} == false'

class DukInstructionIfFalseC(DukInstructionIfC):
    def getConditionStatement(self, constants):
        return f'{self.formatConst(self.constBC(constants))} == false'