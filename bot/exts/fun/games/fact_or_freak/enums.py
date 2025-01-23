from enum import Enum

class Category(Enum):
    Empty = 0
    Truth = 1
    Dare = 2

class CategorySelectionResponse(Enum):
    NoResponse = 0
    ChoseTruth = 1
    ChoseDare  = 2

class LobbyExitCodes(Enum):
    Normal = 0
    LeaderLeft = 1
    LeaderSkipped = 2

class PromptExitCode(Enum):
    Normal = 0
    TimedOut = 1
    Passed = 2

class QuestionType(Enum):
    Truth = 1
    Dare = 2