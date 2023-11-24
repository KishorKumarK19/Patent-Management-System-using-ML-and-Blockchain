from enum import Enum

class Roles(Enum):
    PATENTOFFICE = 1
    NORMALUSER = 2

class PatentStatus(Enum):
    PENDING = 1
    UNDERREVIEW = 2
    APPROVED = 3
    REJECTED = 4