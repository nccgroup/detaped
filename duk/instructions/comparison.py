from duk.instructions.instructions import DukInstruction

class DukInstructionComparison(DukInstruction):
    def getComparisonText(self):
        raise RuntimeError()
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = {self.regConstB(constants, True)} {self.getComparisonText()} {self.regConstC(constants, True)};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {self.regConstB(constants, True)}, {self.regConstC(constants, True)}'

class DukInstructionEq(DukInstructionComparison):
    def getComparisonText(self):
        return '=='

class DukInstructionNeq(DukInstructionComparison):
    def getComparisonText(self):
        return '!='

class DukInstructionSeq(DukInstructionComparison):
    def getComparisonText(self):
        return '=='

class DukInstructionSNeq(DukInstructionComparison):
    def getComparisonText(self):
        return '!='

class DukInstructionGt(DukInstructionComparison):
    def getComparisonText(self):
        return '>'

class DukInstructionGe(DukInstructionComparison):
    def getComparisonText(self):
        return '>='

class DukInstructionLt(DukInstructionComparison):
    def getComparisonText(self):
        return '<'

class DukInstructionLe(DukInstructionComparison):
    def getComparisonText(self):
        return '<='