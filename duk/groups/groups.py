from duk.item import DukItem
from duk.instructions.instructions import *
from duk.instructions.comparison import *
from duk.instructions.ifs import *
from duk.instructions.incdec import *
from duk.instructions.load import *
from duk.instructions.operator import *
from util.logger import Logger, Verbosity

class DukGroup(DukItem):
    @staticmethod
    def isChain(instructions, chain):
        if len(instructions) < len(chain):
            return False

        for i in range(0, len(chain)):
            if not isinstance(instructions[i], chain[i]):
                return False
        return True

    @staticmethod
    def isAny(instruction, classes):
        for i in range(0, len(classes)):
            if isinstance(instruction, classes[i]):
                return True
        return False

    def __init__(self, address, items):
        super().__init__(address)
        self.items = items
        self.hasChanged = False

    def getInstructionCount(self):
        count = 0
        for item in self.items:
            count += item.getInstructionCount()
        return count

    def getIndexFromAddress(self, address):
        for i in range(0, len(self.items)):
            if self.items[i].containsAddress(address):
                return i
        return None

    def getItemByAddress(self, address, offset = 0):
        index = self.getIndexFromAddress(address)
        if index == None:
            return None
        return self.items[index + offset]

    def getItemsByAddress(self, fromAddress = None, toAddress = None, fromOffset = 0, toOffset = 0):
        fromIndex = None if fromAddress == None else self.getIndexFromAddress(fromAddress)
        toIndex = None if toAddress == None else self.getIndexFromAddress(toAddress)
        if fromIndex == None and toIndex == None:
            return self.items
        if fromIndex == None and toIndex != None:
            return self.items[:toIndex + toOffset]
        if fromIndex != None and toIndex == None:
            return self.items[fromIndex + fromOffset:]
        return self.items[fromIndex + fromOffset:toIndex + toOffset]

    def getAddressOfNextInstruction(self, address, cls):
        index = self.getIndexFromAddress(address)
        if index == None:
            return None

        for item in self.items[index:]:
            if isinstance(item, cls):
                return item.getStartAddress()

        return None

    def hasRawAddressInstruction(self):
        rawAddressInstructions = [
            DukInstructionJump,
            DukInstructionIf,
            DukInstructionLabel,
            DukInstructionNextEnum,
        ]

        for item in self.items:
            if isinstance(item, DukGroup):
                if item.hasRawAddressInstruction():
                    return True
            elif isinstance(item, DukInstruction):
                if DukGroup.isAny(item, rawAddressInstructions):
                    return True
        return False

    def replaceItems(self, group, startIndex, endIndex):
        self.items = self.items[:startIndex] + [group] + self.items[endIndex + 1:]
        self.hasChanged = True
        return group

    def replaceItemsByAddress(self, group, startAddress, endAddress, startOffset = 0, endOffset = 0):
        startIndex = self.getIndexFromAddress(startAddress)
        endIndex = self.getIndexFromAddress(endAddress)
        if startIndex == None or endIndex == None:
            return group

        return self.replaceItems(group, startIndex + startOffset, endIndex + endOffset)

    def removeItemsByAddress(self, address, count):
        startIndex = self.getIndexFromAddress(address)
        endIndex = self.getIndexFromAddress(address + count)
        self.items = self.items[:startIndex] + self.items[endIndex:]
        self.hasChanged = True

    def decompile(self, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):

        # Dump group items
        Logger.info(Verbosity.DEBUG, f'{indentation}{self.__class__.__name__}: {self.getStartAddress():04x}-{self.getEndAddress():04x}')
        Logger.info(Verbosity.DEBUG, f'{indentation}Items: ')
        for item in self.items:
            Logger.info(Verbosity.DEBUG, f'{indentation}    {item.getStartAddress():04x}: {item.toString(constants, functions, varmap, formals)}')
        Logger.bar(Verbosity.DEBUG)

        # Keep grouping until no changes occur
        self.hasChanged = True
        while self.hasChanged:
            self.hasChanged = False

            # Group each item
            i = 0
            while i < len(self.items):

                # Jumps
                if not disableGrouping['jump']:
                    self.decompileJumps(i, constants, functions, varmap, formals, disableGrouping, indentation)

                # Call
                if not disableGrouping['call']:
                    self.decompileCall(i, constants, functions, varmap, formals, disableGrouping, indentation)
                    self.decompileCallVar(i, constants, functions, varmap, formals, disableGrouping, indentation)

                # Get prop
                if not disableGrouping['get_prop']:
                    self.decompileGetProp(i, constants, functions, varmap, formals, disableGrouping, indentation)

                # Put object
                if not disableGrouping['init_object']:
                    self.decompileInitObject(i, constants, functions, varmap, formals, disableGrouping, indentation)

                # Put array
                if not disableGrouping['init_array']:
                    self.decompileInitArray(i, constants, functions, varmap, formals, disableGrouping, indentation)

                # Join operators
                if not disableGrouping['join_operator']:
                    self.decompileJoinOperator(i, constants, functions, varmap, formals, disableGrouping, indentation)

                # return r1; return;
                if not disableGrouping['double_return']:
                    self.decompileDoubleReturn(i, constants, functions, varmap, formals, disableGrouping, indentation)

                i += 1

    def decompileJumps(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        # if / else
        if not disableGrouping['if_else']:
            self.decompileIfElse(index, constants, functions, varmap, formals, disableGrouping, indentation)

        # try / catch / finally
        if not disableGrouping['try_catch_finally']:
            self.decompileTryCatch(index, constants, functions, varmap, formals, disableGrouping, indentation)

        # for
        if not disableGrouping['for']:
            self.decompileFor(index, constants, functions, varmap, formals, disableGrouping, indentation)

        # while
        if not disableGrouping['while']:
            self.decompileWhile(index, constants, functions, varmap, formals, disableGrouping, indentation)

        # r3 = r9 == "all" ; if (r3 == true)
        if not disableGrouping['if_condition']:
            self.decompileIfCondition(index, constants, functions, varmap, formals, disableGrouping, indentation)

    def decompileIfElse(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if (not DukGroup.isChain(self.items[index:], [DukInstructionIfTrueR, DukInstructionJump]) and
            not DukGroup.isChain(self.items[index:], [DukInstructionIfFalseR, DukInstructionJump])):
            return

        # Validate if jump only skips the following jump instruction
        if self.items[index].getDestinationAddress() != self.items[index].getStartAddress() + 2:
            return

        # Get first "if" instruction
        firstIfInstruction = self.getItemByAddress(self.items[index].getDestinationAddress())
        if firstIfInstruction == None:
            return

        # If a third jump follows, it's a unhandled for loop
        if isinstance(firstIfInstruction, DukInstructionJump):
            return

        # If the jump is backwards, it's a ?
        if self.items[index + 1].getDestinationAddress() <= self.items[index + 1].address:
            return

        # Otherwise it's a standard if/if-else
        self.decompileIfElseForward(index, constants, functions, varmap, formals, disableGrouping, indentation)
        return

    # LABEL_000; jump 0004; jump 000d; jump 0009; r1 = 0; r2 = r1 < 10.0; if (r2 == false); jump 0008; jump 000b; jump 000d; r1 = r2++; jump 0005; ..[loop statements].. jump 0009; end LABEL_000;
    # ->
    # for (r1 = 0; r2 = (r1 < 10.0; if (r2 == false)); r1 = r2++) { ..[loop statements].. }
    # 
    # LABEL_000; jump 0004; jump 0007; jump 0005; jump 0005; ..[loop statements].. jump 0005; end LABEL_000;
    # ->
    # for (;;) { ..[loop statements].. }
    def decompileFor(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if not DukGroup.isChain(self.items[index:], [DukInstructionLabel, DukInstructionJump, DukInstructionJump]):
            return

        # Get jump addresses
        insLabel = self.items[index]
        insJumpEnd = self.items[index + 1]
        insJump2 = self.items[index + 2]

        initStartAddress = insLabel.getDestinationAddress()
        endAddress = insJumpEnd.getDestinationAddress()
        jump2StartAddress = insJump2.getDestinationAddress()

        # Instruction before end label should be jump
        insEndJump = self.getItemByAddress(endAddress - 1)
        insEnd = self.getItemByAddress(endAddress)

        # Validate end instructions
        if not isinstance(insEndJump, DukInstructionJump) or not isinstance(insEnd, DukInstructionEndLabel):
            return

        # for (;;)
        if DukGroup.isChain(self.items[index:], [DukInstructionLabel, DukInstructionJump, DukInstructionJump, DukInstructionJump]):
            insJump3 = self.items[index + 3]
            jump3StartAddress = insJump3.getDestinationAddress()
            instructionStart = self.items[index + 4]
            instructionStartAddress = instructionStart.getStartAddress()

            # Jump validation
            if (
                initStartAddress != insJump3.getStartAddress() or
                jump2StartAddress != instructionStartAddress or
                jump3StartAddress != instructionStartAddress or
                insEndJump.getDestinationAddress() != instructionStartAddress
            ):
                return

            # Get for instruction group items
            instructionEndAddress = endAddress - 2
            instructionGroupItems = self.getItemsByAddress(instructionStartAddress, instructionEndAddress, 0, 1)

            # For instruction group
            self.dumpGroupItems('For Instruction Group', instructionStartAddress, instructionEndAddress, instructionGroupItems, constants, functions, varmap, formals, indentation)

            # Grouping
            forGroup = self.replaceItemsByAddress(
                DukGroupFor(insLabel, insJumpEnd, insJump2, insEndJump, insEnd, instructionGroupItems),
                instructionStartAddress,
                instructionEndAddress,
                -4, # Ignore label, jump, jump, jump
                2, # Ignore jump, end label
            )

            # Recursive Decompile
            forGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')
            return

        # for (r1 = 0; r2 = (r1 < 10.0; if (r2 == false)); r1 = r2++) { ..[loop statements].. }
        if DukGroup.isChain(self.items[index:], [DukInstructionLabel, DukInstructionJump, DukInstructionJump, DukInstructionLdInt, DukInstructionComparison, DukInstructionIfR, DukInstructionJump, DukInstructionJump, DukInstructionIncDec, DukInstructionJump]):
            insLdInt = self.items[index + 3]
            insComparison = self.items[index + 4]
            insIf = self.items[index + 5]
            insIfJump = self.items[index + 6]
            insJumpEnd2 = self.items[index + 7]
            insIncDec = self.items[index + 8]
            insJumpComparison = self.items[index + 9]
            instructionStart = self.items[index + 10]
            instructionStartAddress = instructionStart.getStartAddress()

            # Jump validation
            if (
                initStartAddress != insLdInt.getStartAddress() or
                jump2StartAddress != insIncDec.getStartAddress() or
                insIf.getDestinationAddress() != insJumpEnd2.getStartAddress() or
                insIfJump.getDestinationAddress() != instructionStartAddress or
                insJumpEnd2.getDestinationAddress() != endAddress or
                insJumpComparison.getDestinationAddress() != insComparison.getStartAddress()
            ):
                return

            # Get for init group items
            initEndAddress = insLdInt.getEndAddress()
            initGroupItems = self.getItemsByAddress(initStartAddress, initEndAddress, 0, 1)

            # For init group
            self.dumpGroupItems('For Init Group', initStartAddress, initEndAddress, initGroupItems, constants, functions, varmap, formals, indentation)

            # Grouping
            forInitGroup = self.replaceItemsByAddress(
                DukGroupForInit(initGroupItems),
                initStartAddress,
                initEndAddress
            )

            # Get for comparison group items
            comparisonStartAddress = insComparison.getStartAddress()
            comparisonEndAddress = insIfJump.getEndAddress()

            # Grouping
            forComparisonGroup = self.replaceItemsByAddress(
                DukGroupForComparison(insComparison, insIf, insIfJump),
                comparisonStartAddress,
                comparisonEndAddress,
                0,
                1 # Ignore jump
            )

            # Get for modifier group items
            modifierStartAddress = insIncDec.getStartAddress()
            modifierEndAddress = insIncDec.getEndAddress()
            modifierGroupItems = self.getItemsByAddress(modifierStartAddress, modifierEndAddress, 0, 1)

            # For modifier group
            self.dumpGroupItems('For Modifier Group', modifierStartAddress, modifierEndAddress, modifierGroupItems, constants, functions, varmap, formals, indentation)

            forModifierGroup = self.replaceItemsByAddress(
                DukGroupForModifier(modifierGroupItems),
                modifierStartAddress,
                modifierEndAddress,
                0,
                1 # Ignore jump
            )

            # Get for instruction group items
            instructionEndAddress = endAddress - 2
            instructionGroupItems = self.getItemsByAddress(instructionStartAddress, instructionEndAddress, 0, 1)

            # For instruction group
            self.dumpGroupItems('For Instruction Group', instructionStartAddress, instructionEndAddress, instructionGroupItems, constants, functions, varmap, formals, indentation)

            # Grouping
            forGroup = self.replaceItemsByAddress(
                DukGroupFor(insLabel, insJumpEnd, insJump2, insEndJump, insEnd, instructionGroupItems, forInitGroup, forComparisonGroup, forModifierGroup),
                instructionStartAddress,
                instructionEndAddress,
                -6, # Ignore label, jump, jump, for init, for comparison, for modifier
                2, # Ignore jump, end label
            )

            # Recursive Decompile
            forGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')
            return
        return

    # LABEL_000; jump 0004; jump 000a; jump 0004; r1 = r0 < 10.0; if (r1 == true); jump 0007; jump 000a; ..[loop statements].. jump 0004; end LABEL_000;
    # ->
    # while (r0 < 10.0) { ..[loop statements].. }
    def decompileWhile(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if not DukGroup.isChain(self.items[index:], [DukInstructionLabel, DukInstructionJump, DukInstructionJump, DukInstructionComparison, DukInstructionIfR, DukInstructionJump]):
            return

        # Get jump addresses
        insLabel = self.items[index]
        insJumpEnd = self.items[index + 1]
        insJump2 = self.items[index + 2]

        initStartAddress = insLabel.getDestinationAddress()
        endAddress = insJumpEnd.getDestinationAddress()
        jump2StartAddress = insJump2.getDestinationAddress()

        # Instruction before end label should be jump
        insEndJump = self.getItemByAddress(endAddress - 1)
        insEnd = self.getItemByAddress(endAddress)

        # Validate end instructions
        if not isinstance(insEndJump, DukInstructionJump) or not isinstance(insEnd, DukInstructionEndLabel):
            return

        insComparison = self.items[index + 3]
        insIf = self.items[index + 4]
        insIfJump = self.items[index + 5]
        instructionStart = self.items[index + 6]
        instructionStartAddress = instructionStart.getStartAddress()

        # Jump validation
        if (
            initStartAddress != insComparison.getStartAddress() or
            jump2StartAddress != insComparison.getStartAddress() or
            insIf.getDestinationAddress() != instructionStartAddress or
            insIfJump.getDestinationAddress() != endAddress or
            insEndJump.getDestinationAddress() != insComparison.getStartAddress()
        ):
            return

        # Get while group items
        instructionEndAddress = endAddress - 2
        instructionGroupItems = self.getItemsByAddress(instructionStartAddress, instructionEndAddress, 0, 1)

        # While group
        self.dumpGroupItems('While Instruction Group', instructionStartAddress, instructionEndAddress, instructionGroupItems, constants, functions, varmap, formals, indentation)

        # Grouping
        whileGroup = self.replaceItemsByAddress(
            DukGroupWhile(insLabel, insJumpEnd, insJump2, insComparison, insIf, insIfJump, insEndJump, insEnd, instructionGroupItems),
            instructionStartAddress,
            instructionEndAddress,
            -6, # Ignore label, jump, jump, comparison, if, if jump
            2, # Ignore jump, end label
        )

        # Recursive Decompile
        whileGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')
        return

    # r7 = r0 == 2.0; if (r7 == true); jump 0004; jump 0006; ..[if statements].. jump 0007; ..[else statements]..
    # ->
    # r7 = r0 == 2.0; if (r7 == true) { ..[if statements].. } else { ..[else statements].. }
    def decompileIfElseForward(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        ifStartAddress = self.items[index].getDestinationAddress()
        ifEndAddress = self.items[index + 1].getDestinationAddress() - 1

        # Else check
        elseJump = self.getItemByAddress(ifEndAddress)
        hasElseJump = elseJump != None and isinstance(elseJump, DukInstructionJump)

        # Substitute items for if group
        insIf = self.items[index]
        insJump = self.items[index + 1]
        ifGroupItems = self.getItemsByAddress(ifStartAddress, ifEndAddress, 0, 0 if hasElseJump else 1)

        # If group
        self.dumpGroupItems('If Group', ifStartAddress, ifEndAddress, ifGroupItems, constants, functions, varmap, formals, indentation)

        if isinstance(insIf, DukInstructionIfTrueR):
            ifGroup = DukGroupIfTrueR(insIf, insJump, ifGroupItems)
        elif isinstance(insIf, DukInstructionIfFalseR):
            ifGroup = DukGroupIfFalseR(insIf, insJump, ifGroupItems)

        ifGroup = self.replaceItemsByAddress(
            ifGroup,
            ifStartAddress,
            ifEndAddress,
            -2, # Ignore if, jump
            (-1 if hasElseJump else 0) # Keep else jump in parent if present
        )

        # Else group
        elseGroup = None
        if hasElseJump:
            elseJump = self.getItemByAddress(ifEndAddress)
            elseStartAddress = ifEndAddress + 1
            elseEndAddress = elseJump.getDestinationAddress() - 1

            # If else jump is negative
            if elseEndAddress < elseStartAddress:
                pass
            else:
                # Otherwise, it's a standard else
                elseGroupItems = self.getItemsByAddress(elseStartAddress, elseEndAddress, 0, 1)

                # Else group
                self.dumpGroupItems('Else Group', elseStartAddress, elseEndAddress, elseGroupItems, constants, functions, varmap, formals, indentation)

                # Substitute items for else group
                elseGroup = self.replaceItemsByAddress(
                    DukGroupElse(elseJump, elseGroupItems),
                    elseStartAddress,
                    elseEndAddress,
                    -1 # Ignore jump
                )

        # Recursive Decompile
        ifGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')
        if elseGroup != None:
            elseGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')

    # r2 = "err"; try (r2); jump 0006; jump 0009; ..[try statements].. endtry; err = r2; ..[catch statements].. endcatch;
    # ->
    # try { ..[try statements].. } catch (err) { ..[catch statements].. }
    def decompileTryCatch(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if not DukGroup.isChain(self.items[index:], [DukInstructionLdConst, DukInstructionTryCatch, DukInstructionJump, DukInstructionJump]):
            return

        endTryAddress = self.items[index + 2].getDestinationAddress() - 1
        endCatchAddress = self.items[index + 3].getDestinationAddress() - 1

        # Validate addresses are not backwards
        if endTryAddress <= self.items[index + 1].getEndAddress() or endCatchAddress <= self.items[index + 1].getEndAddress():
            return

        # Validate endtry instruction is at jump#1 - 1 and endcatch instruction is at jump#2 - 1
        endTry = self.getItemByAddress(endTryAddress)
        endCatch = self.getItemByAddress(endCatchAddress)
        if endTry == None or endCatch == None or not isinstance(endTry, DukInstructionEndTry) or not isinstance(endCatch, DukInstructionEndCatch):
            return

        # Get try/catch/finally register
        tryCatchFinallyRegister = self.items[index + 1].bc

        # Try
        tryStartAddress = self.items[index + 1].getEndAddress() + 3 # Try starts after 2 additional jump instructions
        tryEndAddress = endTryAddress - 1

        # Get try group items
        tryGroupItems = self.getItemsByAddress(tryStartAddress, tryEndAddress, 0, 1)

        # Try group
        self.dumpGroupItems('Try Group', tryStartAddress, tryEndAddress, tryGroupItems, constants, functions, varmap, formals, indentation)

        # Substitute items for try group
        tryGroup = self.replaceItemsByAddress(
            DukGroupTry(
                self.items[index + 0],
                self.items[index + 1],
                self.items[index + 2],
                self.items[index + 3],
                tryGroupItems
            ),
            tryStartAddress,
            tryEndAddress,
            -4, # Ignore ldconst, try, jump, jump
            1 # Ignore endtry
        )

        # Catch
        catchAddress = tryEndAddress + 2
        catchStartAddress = catchAddress + 1
        catchEndAddress = endCatchAddress - 1

        # Get catch group items
        catchGroupItems = self.getItemsByAddress(catchStartAddress, catchEndAddress, 0, 1)

        # Catch group
        self.dumpGroupItems('Catch Group', catchStartAddress, catchEndAddress, catchGroupItems, constants, functions, varmap, formals, indentation)

        # Substitute items for try group
        catchGroup = self.replaceItemsByAddress(
            DukGroupCatch(
                self.getItemByAddress(catchAddress),
                catchGroupItems
            ),
            catchStartAddress,
            catchEndAddress,
            -1, # Ignore var assign
            1 # Ignore endcatch
        )

        # Finally
        finallyIns = None
        for item in self.items:
            # Find EndFin with register matching try register
            if (
                isinstance(item, DukInstructionEndFin) and
                item.a == tryCatchFinallyRegister
            ):
                finallyIns = item
                break

        finallyGroup = None
        if finallyIns != None:
            finallyStartAddress = endCatchAddress + 1
            finallyEndAddress = finallyIns.getEndAddress() - 1

            # Get finally group items
            finallyGroupItems = self.getItemsByAddress(finallyStartAddress, finallyEndAddress, 0, 1)

            # Finally group
            self.dumpGroupItems('Finally Group', finallyStartAddress, finallyEndAddress, finallyGroupItems, constants, functions, varmap, formals, indentation)

            # Substitute items for try group
            finallyGroup = self.replaceItemsByAddress(
                DukGroupFinally(
                    self.getItemByAddress(finallyStartAddress),
                    finallyIns,
                    finallyGroupItems
                ),
                finallyStartAddress,
                finallyEndAddress,
                0,
                1 # Ignore endfin
            )

        # Recursive Decompile
        tryGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')
        catchGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')
        if finallyGroup != None:
            finallyGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')

    # r3 = r9 == "all" ; if (r3 == true)
    # ->
    # if (/*r3 = */r9 == "all")
    def decompileIfCondition(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if not DukGroup.isChain(self.items[index:], [DukInstructionComparison, DukGroupIfR]):
            return

        # Substitute items for if condition group
        if isinstance(self.items[index + 1], DukGroupIfTrueR):
            ifConditionGroup = DukGroupIfTrueCondition(self.items[index], self.items[index + 1], self.items[index:index + 1])
        elif isinstance(self.items[index + 1], DukGroupIfFalseR):
            ifConditionGroup = DukGroupIfFalseCondition(self.items[index], self.items[index + 1], self.items[index:index + 1])

        ifConditionGroup = self.replaceItems(
            ifConditionGroup,
            index, # Ignore eq
            index + 1 # Ignore if group
        )

        # Recursive Decompile
        ifConditionGroup.decompile(constants, functions, varmap, formals, disableGrouping, indentation + '    ')

    # r2 = r3["log"]; r4 = 1; r5 = r0; r2 = r2(r4, r5);
    # ->
    # r3.log(1, r0);
    def decompileCall(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if not isinstance(self.items[index], DukInstructionCall):
            return
        call = self.items[index]

        # Get argument count
        args = call.getArgRegs()

        # Validate there is enough room for argument assignments
        if index - len(args) < 0:
            return

        # Validate each argument assignment
        for i in range(0, len(args)):
            if not DukGroup.isAny(self.items[index - i - 1], [DukInstructionLoad, DukGroupLoad]):
                return

        # Validate function register
        funcReg = self.items[index - len(args) - 1]
        if not DukGroup.isAny(funcReg, [DukInstructionGetProp, DukInstructionCsReg, DukInstructionCsVar]):
            return

        # Call Arguments
        argGroupItems = []
        if len(args) > 0:
            argStartAddress = self.items[index - len(args)].getStartAddress()
            argEndAddress = self.items[index - 1].getStartAddress()

            # Get arg group items
            argGroupItems = self.items[index - len(args):index]

            # Arg group
            self.dumpGroupItems('Call Arguments', argStartAddress, argEndAddress, argGroupItems, constants, functions, varmap, formals, indentation)

        # Substitute items for call group
        self.replaceItemsByAddress(
            DukGroupCall(
                funcReg,
                call,
                argGroupItems
            ),
            funcReg.getStartAddress(),
            call.getEndAddress()
        )

    # r2 = console; r4 = r2; r3 = r4.log("Hello World");
    # ->
    # r3 = console.log("Hello World");
    def decompileCallVar(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if not DukGroup.isChain(self.items[index:], [DukInstructionGetVar, DukInstructionLdReg, DukGroupCall]):
            return

        insGetVar = self.items[index]
        insLdReg = self.items[index + 1]
        groupCall = self.items[index + 2]

        if not isinstance(groupCall.insFuncReg, DukInstructionGetProp) or groupCall.insFuncReg.opcode & DukConstants.DUK__RCBIT_B:
            return

        # Validate get var register matches load register and load register matches call register
        if insGetVar.a != insLdReg.bc or insLdReg.a != groupCall.insFuncReg.b:
            return

        # Substitute items for call var group
        self.replaceItemsByAddress(
            DukGroupCallVar(
                insGetVar,
                insLdReg,
                groupCall
            ),
            insGetVar.getStartAddress(),
            groupCall.getStartAddress()
        )

    # r1 = []; r2 = 0; r3 = 1; r4 = 2; r5 = 3; r1 += [r3, r4, r5];
    # ->
    # var arr = [1, 2, 3];
    def decompileInitArray(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if index >= len(self.items) or not isinstance(self.items[index], DukInstructionNewArr):
            return

        newArr = self.items[index]
        newArrAddress = self.items[index].getStartAddress()

        # Get put array
        putArrAddress = self.getAddressOfNextInstruction(newArrAddress, DukInstructionMPutArr)
        if putArrAddress == None:
            return

        putArr = self.getItemByAddress(putArrAddress)
        if putArr == None:
            return

        regs = putArr.getRegs()
        rStart = newArr.getStartAddress() + 2
        rEnd = rStart + len(regs)

        # Validate new array / put array register
        if newArr.b != putArr.a or newArr.a != len(regs):
            return

        # Validate each instruction between new / put is a register assignment
        i = 0
        for address in range(rStart, rEnd):
            insValue = self.getItemByAddress(address)

            if not DukGroup.isAny(insValue, [DukInstructionLoad]):
                return

            # Validate register
            if f'r{insValue.a}' != regs[i]:
                return
            i += 1

        # Group items
        instructionGroupItems = self.getItemsByAddress(rStart, rEnd, 0, 1)

        # Array group
        self.dumpGroupItems('Init Array Group', rStart, rEnd, instructionGroupItems, constants, functions, varmap, formals, indentation)

        # Grouping
        self.replaceItemsByAddress(
            DukGroupInitArray(newArr, putArr, instructionGroupItems),
            rStart,
            rEnd,
            -2, # Ignore new object, r2 = 0;
            1, # Ignore put object
        )

    # r0 = {}; r1 = "a"; r2 = "b"; r3 = "c"; r4 = 2; r0[r1] = r2; r0[r3] = r4;
    # ->
    # r0 = { "a": "b", "c": 2 };
    def decompileInitObject(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if index >= len(self.items) or not isinstance(self.items[index], DukInstructionNewObj):
            return

        newObj = self.items[index]
        newObjAddress = self.items[index].getStartAddress()

        # Get put object
        putObjAddress = self.getAddressOfNextInstruction(newObjAddress, DukInstructionMPutObj)
        if putObjAddress == None:
            return

        putObj = self.getItemByAddress(putObjAddress)
        if putObj == None:
            return

        rStart = putObj.b
        rEnd = putObj.b + putObj.c

        # Validate each instruction between new / put is a register assignment
        rCurrent = rStart
        for address in range(newObjAddress + 1, putObjAddress, 2):
            insKey = self.getItemByAddress(address)
            insValue = self.getItemByAddress(address + 1)

            if not DukGroup.isAny(insKey, [DukInstructionLoad]) or not DukGroup.isAny(insValue, [DukInstructionLoad]):
                return
            
            # Validate register
            if rCurrent != insKey.a or rCurrent + 1 != insValue.a:
                return

            rCurrent += 2
        
        if rCurrent != rEnd:
            return

        # Group items
        instructionStartAddress = newObjAddress + 1
        instructionEndAddress = putObjAddress - 1
        instructionGroupItems = self.getItemsByAddress(instructionStartAddress, instructionEndAddress, 0, 1)

        # Object group
        self.dumpGroupItems('Init Object Group', instructionStartAddress, instructionEndAddress, instructionGroupItems, constants, functions, varmap, formals, indentation)

        # Grouping
        self.replaceItemsByAddress(
            DukGroupInitObject(newObj, putObj, instructionGroupItems),
            instructionStartAddress,
            instructionEndAddress,
            -1, # Ignore new object
            1, # Ignore put object
        )

    # r3 = example; r3 = r3[1];
    # ->
    # r3 = example[1];
    def decompileGetProp(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if index >= len(self.items) or len(self.items[index:]) < 2:
            return

        if not DukGroup.isAny(self.items[index], [DukInstructionGetVar, DukInstructionLdReg]) or not isinstance(self.items[index + 1], DukInstructionGetProp):
            return

        insVarLd = self.items[index]
        insGetProp = self.items[index + 1]

        # Ensure prop instruction object is register
        if insGetProp.opcode & DukConstants.DUK__RCBIT_B:
            return

        # Validate get var / load register matches get prop registers
        if insVarLd.a != insGetProp.a or insGetProp.a != insGetProp.b:
            return

        # Substitute items for group
        if isinstance(insVarLd, DukInstructionGetVar):
            group = DukGroupGetVarProp(insVarLd, insGetProp)
        elif isinstance(insVarLd, DukInstructionLdReg):
            group = DukGroupLoadProp(insVarLd, insGetProp)

        self.replaceItemsByAddress(
            group,
            insVarLd.getStartAddress(),
            insGetProp.getStartAddress()
        )

    # r4 = r0 + r1; r4 = r4 + r2; r3 = r4 + "d";
    # ->
    # r3 = r0 + r1 + r2 + "d";
    def decompileJoinOperator(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if index >= len(self.items) or len(self.items[index:]) < 2:
            return

        if not DukGroup.isAny(self.items[index], [DukInstructionOperator, DukGroupJoinOperator]) or not DukGroup.isAny(self.items[index + 1], [DukInstructionOperator]):
            return

        insA = self.items[index]
        insB = self.items[index + 1]

        # Validate registers
        if insB.opcode & DukConstants.DUK__RCBIT_B or insA.getAssignee() != f'r{insB.b}':
            return

        # Substitute items for group
        self.replaceItemsByAddress(
            DukGroupJoinOperator(insA, insB),
            insA.getStartAddress(),
            insB.getEndAddress()
        )

    # return r1; return;
    # ->
    # return r1;
    def decompileDoubleReturn(self, index, constants, functions, varmap, formals, disableGrouping = {}, indentation = ''):
        if (
            DukGroup.isChain(self.items[index:], [DukInstructionRetReg, DukInstructionRetUndef]) or
            DukGroup.isChain(self.items[index:], [DukInstructionRetConst, DukInstructionRetUndef])
        ):
            self.replaceItems(self.items[index], index, index + 1) # Ignore return undefined

    def getAdressText(self, start, end):
        address = f'{start:04x}'
        if start != end:
            address = f'{start:04x}-{end:04x}'
        return f'/* {address} */ '

    def dumpGroupItems(self, name, startAddress, endAddress, items, constants, functions, varmap, formals, indentation = ''):
        addressRange = f'{startAddress:04x}' if startAddress == endAddress else f'{startAddress:04x}-{endAddress:04x}'
        Logger.info(Verbosity.DEBUG, f'{indentation}{name} {addressRange}')
        if items != None:
            for item in items:
                Logger.info(Verbosity.DEBUG, f'{indentation}    -> {item.getStartAddress():04x}-{item.getEndAddress():04x} {item.toString(constants, functions, varmap, formals)}')

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = ''
        for item in self.items:
            text += f'{item.toString(constants, functions, varmap, formals, indentation, showAddress)}\n'
        return text

class DukGroupInitObject(DukGroup):
    def __init__(self, newObj, putObj, items):
        super().__init__(newObj.address, items)
        self.newObj = newObj
        self.putObj = putObj

    def getEndAddress(self):
        return self.putObj.getEndAddress()

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{indentation}'
        if showAddress:
            text += f'{self.getAdressText(self.getStartAddress(), self.getEndAddress())}'
        text += f'r{self.newObj.b} = {{\n'

        for address in range(self.newObj.getStartAddress() + 1, self.putObj.getStartAddress(), 2):
            insKey = self.getItemByAddress(address)
            insValue = self.getItemByAddress(address + 1)
            text += f'{indentation}    {insKey.getValue(constants, functions, varmap, formals, indentation, showAddress)}: {insValue.getValue(constants, functions, varmap, formals, indentation, showAddress)},\n'

        text += f'{indentation}}};'
        return text

class DukGroupInitArray(DukGroup):
    def __init__(self, newArr, putArr, items):
        super().__init__(newArr.address, items)
        self.newArr = newArr
        self.putArr = putArr

    def getEndAddress(self):
        return self.putArr.getEndAddress()

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{indentation}'
        if showAddress:
            text += f'{self.getAdressText(self.getStartAddress(), self.getEndAddress())}'
        text += f'r{self.newArr.b} = ['

        regs = self.putArr.getRegs()
        rStart = self.newArr.getStartAddress() + 2
        rEnd = rStart + len(regs)

        values = []
        for address in range(rStart, rEnd):
            insValue = self.getItemByAddress(address)
            values.append(f'{insValue.getValue(constants, functions, varmap, formals, indentation, showAddress)}')
        text += ', '.join(values)

        text += f'];'
        return text

class DukGroupLoad(DukGroup):
    def __init__(self, insLoad):
        super().__init__(insLoad.address, [])
        self.insLoad = insLoad

    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        raise RuntimeError()

    def getAssignee(self):
        return self.insLoad.getAssignee()

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{indentation}'
        if showAddress:
            text += f'{self.getAdressText(self.getStartAddress(), self.getEndAddress())}'
        text += f'{self.getAssignee()} = {self.getValue(constants, functions, varmap, formals, indentation, showAddress)};'
        return text

class DukGroupJoinOperator(DukGroupLoad):
    def __init__(self, insLoad, insOther):
        DukGroupLoad.__init__(self, insLoad)
        self.insOther = insOther

    def getAssignee(self):
        return self.insOther.getAssignee()

    def getEndAddress(self):
        return self.insOther.getEndAddress()

    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        if isinstance(self.insLoad, DukGroupJoinOperator):
            return  f'({self.insLoad.getValue(constants, functions, varmap, formals, indentation, showAddress)}) {self.insOther.getOperatorText()} {self.insOther.getRight(constants)}'
        return f'({self.insLoad.getLeft(constants)} {self.insLoad.getOperatorText()} {self.insLoad.getRight(constants)}) {self.insOther.getOperatorText()} {self.insOther.getRight(constants)}'

class DukGroupProp(DukGroupLoad):
    def __init__(self, insLoad, insGetProp):
        DukGroupLoad.__init__(self, insLoad)
        self.insGetProp = insGetProp

    def getEndAddress(self):
        return self.insGetProp.getEndAddress()

    def getKeyValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        raise RuntimeError()

    def getValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.getKeyValue(constants, functions, varmap, formals, indentation, showAddress)}[{self.insGetProp.regConstC(constants, True)}]'

class DukGroupGetVarProp(DukGroupProp):
    def getKeyValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.insLoad.constBC(constants)}'

class DukGroupLoadProp(DukGroupProp):
    def getKeyValue(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'{self.insLoad.getValue(constants, functions, varmap, formals, indentation, showAddress)}'

class DukGroupCall(DukGroup):
    def __init__(self, insFuncReg, insCall, items):
        super().__init__(insFuncReg.address, items)
        self.insFuncReg = insFuncReg
        self.insCall = insCall

    def getInstructionCount(self):
        return super().getInstructionCount() + 2

    def toStringArguments(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        args = []
        for item in self.items:
            args.append(f'{item.getValue(constants, functions, varmap, formals, indentation, showAddress)}')
        return ', '.join(args)

    def toStringBrackets(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'({self.toStringArguments(constants, functions, varmap, formals, indentation, showAddress)}); // flags: {self.insCall.getFlags()}'

    def toStringFuncRegGetProp(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        if self.insFuncReg.opcode & DukConstants.DUK__RCBIT_C:
            return f'.{self.insFuncReg.constC(constants)}'
        return f'[r{self.insFuncReg.c}]'

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{indentation}'
        if showAddress:
            text += f'{self.getAdressText(self.getStartAddress(), self.getEndAddress())}'

        # Return argument
        text += f'r{self.insCall.getBaseReg()} = '

        # Function Register
        if isinstance(self.insFuncReg, DukInstructionGetProp):
            text += f'{self.insFuncReg.regConstB(constants, True)}'
            text += self.toStringFuncRegGetProp(constants, functions, varmap, formals, indentation, showAddress)
        elif isinstance(self.insFuncReg, DukInstructionCsReg):
            text += f'r{self.insFuncReg.a}' # (Closure Register)
        elif isinstance(self.insFuncReg, DukInstructionCsVar):
            text += f'{self.insFuncReg.constB(constants)}' # (Closure Variable)
        else:
            text += '?'

        text += self.toStringBrackets(constants, functions, varmap, formals, indentation, showAddress)
        return text

class DukGroupCallVar(DukGroup):
    def __init__(self, insGetVar, insLdReg, groupCall):
        super().__init__(insGetVar.address, [])
        self.insGetVar = insGetVar
        self.insLdReg = insLdReg
        self.groupCall = groupCall

    def getEndAddress(self):
        return self.groupCall.getEndAddress()

    def hasRawAddressInstruction(self):
        return super().hasRawAddressInstruction() or self.groupCall.hasRawAddressInstruction()

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = f'{indentation}'
        if showAddress:
            text += f'{self.getAdressText(self.getStartAddress(), self.getEndAddress())}'

        # Return argument
        text += f'r{self.groupCall.insCall.getBaseReg()} = '

        # Function Register
        text += f'{self.insGetVar.constBC(constants)}'
        text += self.groupCall.toStringFuncRegGetProp(constants, functions, varmap, formals, indentation, showAddress)

        text += self.groupCall.toStringBrackets(constants, functions, varmap, formals, indentation, showAddress)
        return text

class DukGroupBlock(DukGroup):
    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        raise RuntimeError()

    def toStringPrefix(self):
        return ''

    def toStringSuffix(self):
        return ''

    def toStringItems(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return super().toString(constants, functions, varmap, formals, indentation + '    ', showAddress)

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = self.toStringPrefix()
        if showAddress:
            text += f'{indentation}{self.getAdressText(self.getStartAddress(), self.getEndAddress())}\n'
        text += f'{indentation}{self.toStringStatement(constants, functions, varmap, formals, indentation, showAddress)}\n'
        text += f'{indentation}{{\n'
        text += self.toStringItems(constants, functions, varmap, formals, indentation, showAddress)
        text += f'{indentation}}}'
        text += self.toStringSuffix()
        return text

class DukGroupIfR(DukGroupBlock):
    def __init__(self, insIf, insJump, items):
        super().__init__(insIf.address, items)
        self.insIf = insIf
        self.insJump = insJump

    def toStringPrefix(self):
        return '\n'

class DukGroupIfTrueR(DukGroupIfR):
    def getEndAddress(self):
        return self.insJump.getEndAddress()

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'if (r{self.insIf.bc} == true)'

class DukGroupIfFalseR(DukGroupIfR):
    def getEndAddress(self):
        return self.insJump.getEndAddress()

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'if (r{self.insIf.bc} == false)'

class DukGroupElse(DukGroupBlock):
    def __init__(self, insJump, items):
        super().__init__(insJump.address, items)
        self.insJump = insJump

    def getEndAddress(self):
        return self.insJump.getEndAddress()

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'else'

    def toStringSuffix(self):
        return '\n'

class DukGroupIfCondition(DukGroupBlock):
    def __init__(self, insCondition, groupIf, items):
        super().__init__(insCondition.address, items)
        self.insCondition = insCondition
        self.groupIf = groupIf

    def hasRawAddressInstruction(self):
        return super().hasRawAddressInstruction() or self.groupIf.hasRawAddressInstruction()

    def toStringItems(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = ''
        for item in self.groupIf.items:
            text += f'{item.toString(constants, functions, varmap, formals, indentation + "    ", showAddress)}\n'
        return text

    def getEndAddress(self):
        return self.groupIf.getEndAddress()

    def toStringPrefix(self):
        return '\n'

class DukGroupIfTrueCondition(DukGroupIfCondition):
    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'if (/*r{self.insCondition.a} = */{self.insCondition.regConstB(constants, True)} {self.insCondition.getComparisonText()} {self.insCondition.regConstC(constants, True)})'

class DukGroupIfFalseCondition(DukGroupIfCondition):
    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'if (/*r{self.insCondition.a} = */({self.insCondition.regConstB(constants, True)} {self.insCondition.getComparisonText()} {self.insCondition.regConstC(constants, True)}) == false)'

class DukGroupTry(DukGroupBlock):
    def __init__(self, insLdConst, insTry, insJumpEndTry, insJumpEndCatch, items):
        super().__init__(insLdConst.address, items)
        self.insLdConst = insLdConst
        self.insTry = insTry
        self.insJumpEndTry = insJumpEndTry
        self.insJumpEndCatch = insJumpEndCatch

    def getEndAddress(self):
        return self.getStartAddress() + 2

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return 'try'

    def toStringPrefix(self):
        return '\n'

class DukGroupCatch(DukGroupBlock):
    def __init__(self, insVarAssign, items):
        super().__init__(insVarAssign.address, items)
        self.insVarAssign = insVarAssign

    def getStartAddress(self):
        return self.insVarAssign.getStartAddress() - 1

    def getEndAddress(self):
        return self.insVarAssign.getEndAddress()

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'catch ({self.insVarAssign.constBC(constants)})'

class DukGroupFinally(DukGroupBlock):
    def __init__(self, insFirst, insEndFin, items):
        super().__init__(insFirst.address, items)
        self.insFirst = insFirst
        self.insEndFin = insEndFin

    def getStartAddress(self):
        return self.insFirst.getStartAddress() - 1

    def getEndAddress(self):
        return self.insEndFin.getEndAddress()

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        return f'finally'

class DukGroupWhile(DukGroupBlock):
    def __init__(self, insLabel, insJumpEnd, insJump2, insCondition, insIf, insIfJump, insEndJump, insEnd, items):
        super().__init__(insLabel.address, items)
        self.insLabel = insLabel
        self.insJumpEnd = insJumpEnd
        self.insJump2 = insJump2
        self.insCondition = insCondition
        self.insIf = insIf
        self.insIfJump = insIfJump
        self.insEndJump = insEndJump
        self.insEnd = insEnd

    def getEndAddress(self):
        return self.insEnd.getEndAddress()

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = 'while ('

        if isinstance(self.insIf, DukInstructionIfTrueR):
            text += f'{self.insCondition.regConstB(constants, True)} {self.insCondition.getComparisonText()} {self.insCondition.regConstC(constants, True)}'
        elif isinstance(self.insIf, DukInstructionIfFalseR):
            text += f'({self.insCondition.regConstB(constants, True)} {self.insCondition.getComparisonText()} {self.insCondition.regConstC(constants, True)}) == false'
        else:
            text += f'?'

        text += ')'
        return text

    def toStringPrefix(self):
        return '\n'

class DukGroupFor(DukGroupBlock):
    def __init__(self, insLabel, insJumpEnd, insJump2, insEndJump, insEnd, items, initGroup = None, comparisonGroup = None, modifierGroup = None):
        super().__init__(insLabel.address, items)
        self.insLabel = insLabel
        self.insJumpEnd = insJumpEnd
        self.insJump2 = insJump2
        self.insEndJump = insEndJump
        self.insEnd = insEnd
        self.initGroup = initGroup
        self.comparisonGroup = comparisonGroup
        self.modifierGroup = modifierGroup

    def getEndAddress(self):
        return self.insEnd.getEndAddress()

    def toStringStatement(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = 'for ('
        if self.initGroup != None:
            text += self.initGroup.toString(constants, functions, varmap, formals, indentation, showAddress)
        text += ';'
        if self.comparisonGroup != None:
            text += ' ' + self.comparisonGroup.toString(constants, functions, varmap, formals, indentation, showAddress)
        text += ';'
        if self.modifierGroup != None:
            text += ' ' + self.modifierGroup.toString(constants, functions, varmap, formals, indentation, showAddress)
        text += ')'
        return text

    def toStringPrefix(self):
        return '\n'

class DukGroupForItems(DukGroup):
    def __init__(self, items):
        super().__init__(0 if len(items) == 0 else items[0].address, items)

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = ''
        if showAddress:
            lastItemAddress = 0 if len(self.items) == 0 else self.items[len(self.items) - 1].getStartAddress()
            text += f'{self.getAdressText(self.getStartAddress(), lastItemAddress)}'

        commands = []
        for item in self.items:
            commands.append(f'{item.toString(constants, functions, varmap, formals, "", False).rstrip(";")}')
        return text + ', '.join(commands)

class DukGroupForInit(DukGroupForItems):
    pass

class DukGroupForComparison(DukGroup):
    def __init__(self, insCondition, insIf, insIfJump):
        super().__init__(insCondition.getStartAddress(), [])
        self.insCondition = insCondition
        self.insIf = insIf
        self.insIfJump = insIfJump

    def toString(self, constants, functions, varmap, formals, indentation = '', showAddress = False):
        text = ''

        if showAddress:
            text += f'{self.getAdressText(self.getStartAddress(), self.insIfJump.getEndAddress())}'

        # Condition is inverted as it jumps to end of if statement
        if isinstance(self.insIf, DukInstructionIfTrueR):
            text += f'({self.insCondition.regConstB(constants, True)} {self.insCondition.getComparisonText()} {self.insCondition.regConstC(constants, True)}) == false'
        elif isinstance(self.insIf, DukInstructionIfFalseR):
            text += f'{self.insCondition.regConstB(constants, True)} {self.insCondition.getComparisonText()} {self.insCondition.regConstC(constants, True)}'
        else:
            text += f'?'
        return text

class DukGroupForModifier(DukGroupForItems):
    pass