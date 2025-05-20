from dataclasses import dataclass, field

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
