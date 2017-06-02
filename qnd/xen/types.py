

def enum(**enums):
    return type('Enum', (), enums)

MessageType = enum(MESSAGE=1, TASK=2, NOTIFICATION=3)