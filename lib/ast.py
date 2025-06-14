from dataclasses import dataclass, field
from itertools import count as idcount
from .types import Type, TUnresolved, SecLabel

@dataclass
class Span:
  off_start: int
  off_end: int
  lnum: int
  cstart: int
  cend: int
  src: str = field(repr=False)

@dataclass
class Token:
  type: str
  value: str
  span: Span = field(repr=False)

FAKE_SPAN = Span(0, 0, 0, 0, 0, '')
TOKEN_EOF = Token('eof', 'eof', FAKE_SPAN)

@dataclass
class Symbol:
  name: str
  type: Type
  secure: SecLabel
  origin: Span = field(repr=False)
  id: int = field(default_factory=idcount().__next__, init=False)

  def __hash__(self):
    return self.id

SYMBOL_UNRESOLVED = Symbol('UNRESOLVED', TUnresolved(), SecLabel.INVALID, FAKE_SPAN)

@dataclass
class SymTab:
  parent: 'SymTab|None'
  symbols: dict[str, Symbol]

  def lookup(self, name: str) -> Symbol|None:
    if name in self.symbols:
      return self.symbols[name]
    elif self.parent is not None:
      # not in this scope
      return self.parent.lookup(name)
    else:
      # not found
      return None

  def register(self, name: str, sym: Symbol):
    assert(self.lookup(name) is None)
    self.symbols[name] = sym

@dataclass
class AstNode:
  span: Span = field(repr=False)

@dataclass
class Expr(AstNode):
  type: Type
  secure: SecLabel

@dataclass
class ELValue(Expr):
  pass

@dataclass
class EId(ELValue):
  name: str
  sym: Symbol

@dataclass
class EInt(Expr):
  value: int

@dataclass
class EBool(Expr):
  value: bool

@dataclass
class EArray(ELValue):
  expr: EId
  index: Expr

@dataclass
class EArrayLiteral(Expr):
  values: list[Expr]

@dataclass
class EUnOp(Expr):
  op: str
  expr: Expr

@dataclass
class EBinOp(Expr):
  op: str
  lhs: Expr
  rhs: Expr

@dataclass
class FnParam(AstNode):
  type: Type
  name: str
  sym: Symbol

@dataclass
class ECall(Expr):
  name: EId
  params: list[Expr]

@dataclass
class EDeclassify(Expr):
  expr: Expr

@dataclass
class Stmt(AstNode):
  pass

@dataclass
class SScope(Stmt):
  stmts: list[Stmt]
  secure: SecLabel
  symtab: SymTab = field(repr=False)

@dataclass
class SVarDef(Stmt):
  lhs: ELValue
  rhs: Expr

@dataclass
class SFnDef(Stmt):
  name: EId
  params: list[FnParam]
  retype: Type
  body: SScope

@dataclass
class SAssign(Stmt):
  lhs: ELValue
  rhs: Expr

@dataclass
class SIf(Stmt):
  clause: Expr
  body: SScope
  else_stmt: SScope | None
  # TODO: allow if (...) do ...

@dataclass
class SWhile(Stmt):
  clause: Expr
  body: SScope

@dataclass
class STryCatch(Stmt):
  tryBody: SScope
  catchBody: SScope

@dataclass
class SThrow(Stmt):
  pass

@dataclass
class SDebug(Stmt):
  expr: Expr

@dataclass
class SReturn(Stmt):
  secure: SecLabel
  expr: Expr

@dataclass
class SGlobal(Stmt):
  type: Type
  expr: ELValue
  orig_secure: SecLabel

@dataclass
class File(AstNode):
  stmts: list[Stmt]
  symtab: SymTab = field(repr=False)
  inputs: list[SGlobal]
  outputs: list[SGlobal]