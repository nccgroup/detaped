from duk.instructions.instructions import DukInstruction
from duk.constants import DukConstants

class DukInstructionLoad(DukInstruction):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        raise RuntimeError()

    def getAssignee(self):
        return f'r{self.a}'

    def getCommentText(self):
        return None

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{self.getStringPrefix(indentation, showAddress)}{self.getAssignee()} = {self.getValue(constants, functions, varmap, formals, indentation, showAddress)};'
        if self.getCommentText() != None:
            text += f' // {self.getCommentText()}'
        return text

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.getAssignee()}, {self.getValue(constants, functions, varmap, formals, indentation, showAddress)}'
        if self.getCommentText() != None:
            text += f' ; {self.getCommentText()}'
        return text

class DukInstructionGetVar(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return self.constBC(constants)

class DukInstructionLdReg(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'r{self.bc}'

class DukInstructionLdConst(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return self.formatConst(self.constBC(constants))

class DukInstructionLdInt(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return self.bc - DukConstants.DUK_BC_LDINT_BIAS

class DukInstructionLdIntx(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'(r{self.a} << {DukConstants.DUK_BC_LDINTX_SHIFT}) + {self.bc}'

class DukInstructionLdThis(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'this'

class DukInstructionLdUndef(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'undefined'

class DukInstructionLdNull(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'null'

class DukInstructionLdTrue(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'true'

class DukInstructionLdFalse(DukInstructionLoad):
    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'false'