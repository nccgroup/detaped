class DukItem:
    def __init__(self, address):
        self.address = address

    def getStartAddress(self):
        return self.address

    def getEndAddress(self):
        return self.getStartAddress() + (self.getInstructionCount() - 1)

    def containsAddress(self, address):
        return address >= self.getStartAddress() and address <= self.getEndAddress()

    def getInstructionCount(self):
        return 1