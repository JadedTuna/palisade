from dataclasses import dataclass
from enum import Enum, auto

class SecLabel(Enum):
  INVALID = auto()
  LOW = auto()
  HIGH = auto()

  def join(self, *others: 'SecLabel') -> 'SecLabel':
    # always traverse to find any INVALID labels
    result = self
    for i in range(len(others)):
      match others[i]:
        case SecLabel.HIGH:
          result = SecLabel.HIGH
        case SecLabel.LOW:
          pass
        case _:
          raise RuntimeError(others[i])
    return result

  @staticmethod
  def from_label(label: str) -> 'SecLabel':
    match label:
      case 'high':
        return SecLabel.HIGH
      case 'low':
        return SecLabel.LOW
      case _:
        raise RuntimeError(label)

  def __str__(self) -> str:
    match self:
      case SecLabel.LOW:
        return 'low'
      case SecLabel.HIGH:
        return 'high'
      case SecLabel.INVALID:
        return 'invalid'
      case _:
        raise RuntimeError(self)

  def __repr__(self) -> str:
    return f'<{str(self)}>'

@dataclass
class Type:
  pass

@dataclass
class TUnresolved(Type):
  pass

@dataclass
class TInt(Type):
  pass

@dataclass
class TBool(Type):
  pass

@dataclass
class TArray(Type):
  of: Type
  length: int

@dataclass
class TFn(Type):
  retype: Type
  params: list[Type]
  sfndef: 'SFnDef'
