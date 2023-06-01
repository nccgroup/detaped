import struct

class FileReader:
    def __init__(self, file):
        self.file = file

    def unpack(self, format, length):
        data = self.file.read(length)
        if len(data) != length:
            return None
        return struct.unpack(format, data)[0]

    def uint8(self):
        return self.unpack('>B', 1)

    def uint16(self):
        return self.unpack('>H', 2)

    def uint32(self):
        return self.unpack('>I', 4)

    def double(self):
        return self.unpack('>d', 8)

    def rawString(self):
        length = self.uint32()
        if length == None:
            return None
        return self.file.read(length)

    def string(self):
        rawString = self.rawString()
        if rawString == None:
            return None

        rStr = ''
        for c in rawString:
            if c < 0x20 or c > 0x7e or chr(c) in '\'"':
                rStr += f'\\x{c:02x}'
                continue
            rStr += chr(c)
        return rStr