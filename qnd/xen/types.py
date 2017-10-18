

def enum(**enums):
    return type('Enum', (), enums)

MessageType = enum(MESSAGE=1, TASK=2, NOTIFICATION=3)

TaskType = enum(BACKUP=1, RESTORE=2, ARCHIVE=3)