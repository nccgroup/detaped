from duk.instructions.load import DukInstructionLoad

class DukInstructionUnary(DukInstructionLoad):
    def getOperatorText(self):
        raise RuntimeError()

    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getOperatorText()}r{self.bc}'

class DukInstructionBNot(DukInstructionUnary):
    def getOperatorText(self):
        return '~'

class DukInstructionLNot(DukInstructionUnary):
    def getOperatorText(self):
        return '!'

class DukInstructionUnm(DukInstructionUnary):
    def getOperatorText(self):
        return '-'

class DukInstructionUnp(DukInstructionUnary):
    def getOperatorText(self):
        return '+'