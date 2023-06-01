from duk.instructions.instructions import DukInstruction

class DukInstructionIncDec(DukInstruction):
    def isIncPre(self):
        raise RuntimeError()

    def wrapIncPreText(self, inner):
        text = ''
        isInc, isPre = self.isIncPre()
        if isPre:
            text += '++' if isInc else '--'
        text += inner
        if not isPre:
            text += '++' if isInc else '--'
        return text

# Increment/Decrement Assign Register
class DukInstructionIncDecR(DukInstructionIncDec):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        inner = f'r{self.bc}'
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = ' + self.wrapIncPreText(inner) + ';'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.bc}, r{self.a}'

class DukInstructionPreIncR(DukInstructionIncDecR):
    def isIncPre(self):
        return True, True

class DukInstructionPreDecR(DukInstructionIncDecR):
    def isIncPre(self):
        return False, True

class DukInstructionPostIncR(DukInstructionIncDecR):
    def isIncPre(self):
        return True, False

class DukInstructionPostDecR(DukInstructionIncDecR):
    def isIncPre(self):
        return False, False

# Increment/Decrement Register
class DukInstructionIncDecV(DukInstructionIncDec):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        inner = f'{self.constBC(constants)}'
        return f'{self.getStringPrefix(indentation, showAddress)}' + self.wrapIncPreText(inner) + ';'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.constBC(constants)}'

class DukInstructionPreIncV(DukInstructionIncDecV):
    def isIncPre(self):
        return True, True

class DukInstructionPreDecV(DukInstructionIncDecV):
    def isIncPre(self):
        return False, True

class DukInstructionPostIncV(DukInstructionIncDecV):
    def isIncPre(self):
        return True, False

class DukInstructionPostDecV(DukInstructionIncDecV):
    def isIncPre(self):
        return False, False

# Increment/Decrement Assign Prop
class DukInstructionIncDecP(DukInstructionIncDec):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        inner = f'{self.regConstB(constants, True)}[{self.regConstC(constants, True)}]'
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = ' + self.wrapIncPreText(inner) + ';'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {self.regConstB(constants, True)}, {self.regConstC(constants, True)}'

class DukInstructionPreIncP(DukInstructionIncDecP):
    def isIncPre(self):
        return True, True

class DukInstructionPreDecP(DukInstructionIncDecP):
    def isIncPre(self):
        return False, True

class DukInstructionPostIncP(DukInstructionIncDecP):
    def isIncPre(self):
        return True, False

class DukInstructionPostDecP(DukInstructionIncDecP):
    def isIncPre(self):
        return False, False
