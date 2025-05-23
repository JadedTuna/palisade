from dataclasses import dataclass

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
  seclabels: list[bool]
