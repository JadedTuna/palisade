from dataclasses import dataclass, field
from .types import Type, TUnresolved

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

HIGH = True
LOW  = False

@dataclass
class Symbol:
  name: str
  type: Type
  secure: bool
  origin: Span = field(repr=False)

SYMBOL_UNRESOLVED = Symbol('UNRESOLVED', TUnresolved(), HIGH, FAKE_SPAN)

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
  secure: bool

@dataclass
class EId(Expr):
  name: str
  sym: Symbol

@dataclass
class EInt(Expr):
  value: int

@dataclass
class EBool(Expr):
  value: bool

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
class Stmt(AstNode):
  pass

@dataclass
class SScope(Stmt):
  stmts: list[Stmt]
  symtab: SymTab = field(repr=False)

@dataclass
class SVarDef(Stmt):
  secure: bool
  lhs: EId
  rhs: Expr

@dataclass
class SAssign(Stmt):
  lhs: EId
  rhs: Expr

@dataclass
class SIf(Stmt):
  clause: Expr
  body: SScope
  else_stmt: SScope | None
  # TODO: only accept SScope
  # TODO: allow if (...) do ...

@dataclass
class SWhile(Stmt):
  clause: Expr
  body: SScope

@dataclass
class SDebug(Stmt):
  expr: Expr

@dataclass
class File(AstNode):
  stmts: list[Stmt]
  symtab: SymTab = field(repr=False)
