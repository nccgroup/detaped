from duk.constants import DukConstants
from duk.item import DukItem
import ctypes

class DukInstruction(DukItem):
    def __init__(self, address, encoded):
        super().__init__(address)
        self.opcode = encoded & 0xFF
        self.a = (encoded >> 8) & 0xFF
        self.b = (encoded >> 16) & 0xFF
        self.c = (encoded >> 24) & 0xFF
        self.bc = (encoded >> 16) & 0xFFFF
        self.abc = (encoded >> 8) & 0xFFFFFF
        self.name = DukConstants.DUK_OP[self.opcode]

    def formatConst(self, const):
        return f'"{const}"' if type(const) == str else const

    def constA(self, constants):
        return constants[self.a]

    def constB(self, constants):
        return constants[self.b]

    def constC(self, constants):
        return constants[self.c]

    def constBC(self, constants):
        return constants[self.bc]

    def regConstB(self, constants, format = False):
        if self.opcode & DukConstants.DUK__RCBIT_B:
            return self.formatConst(self.constB(constants)) if format else self.constB(constants)
        return f'r{self.b}'

    def regConstC(self, constants, format = False):
        if self.opcode & DukConstants.DUK__RCBIT_C:
            return self.formatConst(self.constC(constants)) if format else self.constC(constants)
        return f'r{self.c}'

    def __str__(self):
        return f'{self.name}(A:{self.a}, B:{self.b}, C:{self.c}, BC:{self.bc})'

    def getStringPrefix(self, indentation = '', showAddress = False):
        text = indentation
        if showAddress:
            text += f'/* {self.address:04x} */ '
        return text

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return self.getStringPrefix(indentation, showAddress) + str(self)

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return self.getStringPrefix(indentation, showAddress) + str(self)

class DukInstructionJump(DukInstruction):
    def getDestinationAddress(self):
        return self.address + 1 + (self.abc - DukConstants.DUK_BC_JUMP_BIAS)
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}jump {self.getDestinationAddress():04x};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.getDestinationAddress():04x}'

class DukInstructionDeclVar(DukInstruction):
    def getPropFlags(self):
        return self.a & DukConstants.DUK_PROPDESC_FLAGS_MASK

    def isFunctionDeclaration(self):
        return (self.a & DukConstants.DUK_BC_DECLVAR_FLAG_FUNC_DECL) != 0

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        if not self.isFunctionDeclaration():
            return f'{self.getStringPrefix(indentation, showAddress)}var {self.regConstB(constants)}; // prop_flags: {self.getPropFlags()}'
        return f'{self.getStringPrefix(indentation, showAddress)}var {self.regConstB(constants)} = r{self.c}; // prop_flags: {self.getPropFlags()}'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        if not self.isFunctionDeclaration():
            return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.regConstB(constants)} ; prop_flags: {self.getPropFlags()}'
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.regConstB(constants)}, r{self.c} ; prop_flags: {self.getPropFlags()}'

class DukInstructionRegExp(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        # self.regConstB(constants) - Expanded regular expression binary text
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = /{self.regConstC(constants)}/;'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, /{self.regConstC(constants)}/'

class DukInstructionTypeOf(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = typeof r{self.bc};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, r{self.bc}'

class DukInstructionTypeOfId(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = typeof {self.constBC(constants)};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {self.constBC(constants)}'

class DukInstructionPutVar(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.constBC(constants)} = r{self.a};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.constBC(constants)}, r{self.a}'

class DukInstructionDelVar(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}delete {self.constBC(constants)};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.constBC(constants)}'

class DukInstructionClosure(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = {functions[self.bc].getName()}; // CLOSURE' # Closure
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {functions[self.bc].getName()}'

class DukInstructionRetReg(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}return r{self.bc};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.bc}'

class DukInstructionRetUndef(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}return;'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name}'

class DukInstructionRetConst(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}return {self.formatConst(self.constBC(constants))};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.formatConst(self.constBC(constants))}'

class DukInstructionLabel(DukInstruction):
    def getDestinationAddress(self):
        return self.address + 3
    def getFlags(self):
        return ctypes.c_uint32((DukConstants.DUK_CAT_TYPE_LABEL | (self.bc << DukConstants.DUK_CAT_LABEL_SHIFT))).value
    def getLabelId(self):
        return ((self.getFlags() & DukConstants.DUK_CAT_LABEL_MASK) >> DukConstants.DUK_CAT_LABEL_SHIFT)
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}LABEL_{self.getLabelId():03x}; jump {self.getDestinationAddress():04x};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.getLabelId()}, {self.getDestinationAddress():04x}'

class DukInstructionEndLabel(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}end LABEL_{self.bc:03x};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.bc}'

class DukInstructionBreak(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}break LABEL_{self.bc:03x};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.bc}'

class DukInstructionContinue(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}continue LABEL_{self.bc:03x};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.bc}'

class DukInstructionTryCatch(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}try (r{self.bc}); // flags: {self.a}'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.bc}, {self.a}'

class DukInstructionEndTry(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}endtry;'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name}'

class DukInstructionEndCatch(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}endcatch;'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name}'

class DukInstructionEndFin(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}endfin (r{self.a});'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}'

class DukInstructionThrow(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}throw r{self.bc};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.bc}'

class DukInstructionCsReg(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.bc} = r{self.a};' # (Closure Register)
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.bc}, r{self.a}'

class DukInstructionCsVar(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = {self.constB(constants)};' # (Closure Variable)
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {self.constB(constants)}'

class DukInstructionCall(DukInstruction):
    def getFlags(self):
        return (self.opcode & 0x07) | DukConstants.DUK_CALL_FLAG_ALLOW_ECMATOECMA

    def getBaseReg(self):
        return self.bc

    def getNumberOfArgs(self):
        return self.a

    def getArgRegs(self):
        nargs = self.getNumberOfArgs()
        base = self.getBaseReg()
        regThis = base + 1
        regArg1 = base + 2

        regArgs = []
        for i in range(regArg1, regArg1 + nargs):
            regArgs.append(f'r{i}')
        return regArgs

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.getBaseReg()} = r{self.getBaseReg()}({", ".join(self.getArgRegs())}); // flags: {self.getFlags()}'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        regs = [f'r{self.getBaseReg()}', f'r{self.getBaseReg()}']
        regs.extend(self.getArgRegs())
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {", ".join(regs)} ; flags: {self.getFlags()}'

class DukInstructionGetProp(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} = {self.regConstB(constants, True)}[{self.regConstC(constants, True)}];'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {self.regConstB(constants, True)}, {self.regConstC(constants, True)}'

class DukInstructionInitEnum(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.b} = _ENUMERATOR(r{self.c});'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.b}, r{self.c}'

class DukInstructionNextEnum(DukInstruction):
    def getDestinationAddress(self):
        return self.address + 2
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.b} = _ENUMERATOR.next(r{self.c}); if _ENUMERATOR.more() {{ jump {self.getDestinationAddress():04x} }};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.b}, r{self.c}, {self.getDestinationAddress():04x}'

class DukInstructionPutProp(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a}[{self.regConstB(constants, True)}] = {self.regConstC(constants, True)};'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {self.regConstB(constants, True)}, {self.regConstC(constants, True)}'

class DukInstructionDelProp(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}delete {self.regConstB(constants, True)}[{self.regConstC(constants, True)}];'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} {self.regConstB(constants, True)}, {self.regConstC(constants, True)}'

class DukInstructionNewObj(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.b} = {{}}; // Size: {self.a}'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.b}, {self.a}'

class DukInstructionNewArr(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.b} = []; // Size: {self.a}'
    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.b}, {self.a}'

class DukInstructionMPutObj(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{self.getStringPrefix(indentation, showAddress)}'
        for i in range(self.b, self.b + self.c, 2):
            text += f'r{self.a}[r{i}] = r{i + 1}; '
        return text

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        regs = []
        for i in range(self.b, self.b + self.c, 2):
            regs.append(f'r{i}')
            regs.append(f'r{i + 1}')
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {", ".join(regs)}'

class DukInstructionMPutArr(DukInstruction):
    def getRegs(self):
        regs = []
        for i in range(self.b + 1, self.b + self.c):
            regs.append(f'r{i}')
        return regs

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a} += [{", ".join(self.getRegs())}];'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        regs = []
        for i in range(self.b + 1, self.b + self.c):
            regs.append(f'r{i}')
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, {", ".join(self.getRegs())}'

class DukInstructionSetALen(DukInstruction):
    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}r{self.a}.length = r{self.bc} + 1;'

    def toAsm(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getStringPrefix(indentation, showAddress)}{self.name} r{self.a}, r{self.bc}'