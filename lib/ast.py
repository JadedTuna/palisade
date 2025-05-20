from dataclasses import dataclass, field

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
class AstNode:
  pass

@dataclass
class Expr(AstNode):
  type: Type

@dataclass
class EId(Expr):
  name: str

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

@dataclass
class SAssign(Stmt):
  lhs: EId
  rhs: Expr

@dataclass
class SIf(Stmt):
  clause: Expr
  body: Stmt
  else_stmt: Stmt | None

@dataclass
class SWhile(Stmt):
  clause: Expr
  body: Stmt

@dataclass
class File(AstNode):
  stmts: list[Stmt]
