from duk.instructions.load import DukInstructionLoad

class DukInstructionOperator(DukInstructionLoad):
    def getOperatorText(self):
        raise RuntimeError()

    def getLeft(self, constants):
        return f'{self.regConstB(constants, True)}'

    def getRight(self, constants):
        return f'{self.regConstC(constants, True)}'

    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getLeft(constants)} {self.getOperatorText()} {self.getRight(constants)}'

class DukInstructionAdd(DukInstructionOperator):
    def getOperatorText(self):
        return '+'

class DukInstructionSub(DukInstructionOperator):
    def getOperatorText(self):
        return '-'

class DukInstructionMul(DukInstructionOperator):
    def getOperatorText(self):
        return '*'

class DukInstructionDiv(DukInstructionOperator):
    def getOperatorText(self):
        return '/'

class DukInstructionMod(DukInstructionOperator):
    def getOperatorText(self):
        return '%'

class DukInstructionExp(DukInstructionOperator):
    def getOperatorText(self):
        return '**'

class DukInstructionBAnd(DukInstructionOperator):
    def getOperatorText(self):
        return '&'

class DukInstructionBOr(DukInstructionOperator):
    def getOperatorText(self):
        return '|'

class DukInstructionBXor(DukInstructionOperator):
    def getOperatorText(self):
        return '^'

class DukInstructionBaSl(DukInstructionOperator):
    def getOperatorText(self):
        return '<<'
    def getCommentText(self):
        return 'SIGNED'

class DukInstructionBlSr(DukInstructionOperator):
    def getOperatorText(self):
        return '>>'
    def getCommentText(self):
        return 'SIGNED'

class DukInstructionBaSr(DukInstructionOperator):
    def getOperatorText(self):
        return '>>'
    def getCommentText(self):
        return 'UNSIGNED'

class DukInstructionInstOf(DukInstructionOperator):
    def getOperatorText(self):
        return '>>'
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'instanceof'

class DukInstructionIn(DukInstructionOperator):
    def getOperatorText(self):
        return 'in'