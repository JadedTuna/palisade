from lib.ast import *
from lib.types import *
from lib.utils import report_error, pprint
from traverse import make_traverse
from parser import BINOPS, UNOPS, PRECTABLE_BOOLEAN, PRECTABLE_COMPARISON

def type_eunop(op: str, span: Span, expr: Expr) -> Type:
  opkind = UNOPS[op]
  match expr.type:
    case TInt() if opkind == PRECTABLE_BOOLEAN:
      report_error('cannot use boolean operators with integers', span)
    case TInt():
      return TInt()

    case TBool() if opkind == PRECTABLE_BOOLEAN:
      return TBool()
    case TBool():
      report_error('can only use boolean operators with booleans', span)

    case _:
      raise RuntimeError(expr)

def type_ebinop(op: str, span: Span, lhs: Expr, rhs: Expr) -> Type:
  opkind = BINOPS[op][0]
  match (lhs.type, rhs.type):
    case (TInt(), TInt()) if opkind == PRECTABLE_BOOLEAN:
      report_error('cannot use boolean operators with integers', span)
    case (TInt(), TInt()) if opkind == PRECTABLE_COMPARISON:
      return TBool()
    case (TInt(), TInt()):
      return TInt()

    case (TBool(), TBool()) if opkind == PRECTABLE_BOOLEAN:
      return TBool()
    case (TBool(), TBool()):
      report_error('can only use boolean operators with booleans', span)

    case _:
      report_error('type mismatch', span)

def _type_check(node: AstNode):
  match node:
    case EId(span, TUnresolved(), sec, name, sym):
      return EId(span, sym.type, sec, name, sym)
    case EInt(span, TUnresolved(), sec, v):
      return EInt(span, TInt(), sec, v)
    case EBool(span, TUnresolved(), sec, v):
      return EBool(span, TBool(), sec, v)
    case EUnOp(span, TUnresolved(), sec, op, expr):
      type = type_eunop(op, span, expr)
      return EUnOp(span, type, sec, op, expr)
    case EBinOp(span, TUnresolved(), sec, op, lhs, rhs):
      type = type_ebinop(op, span, lhs, rhs)
      return EBinOp(span, type, sec, op, lhs, rhs)

    case SScope() | File():
      return node
    case SVarDef(_, _, lhs, rhs):
      # type inference
      lhs.sym.type = rhs.type
      # TODO: HACK
      lhs.type = rhs.type
      return node
    case SAssign(span, lhs, rhs):
      if lhs.type != rhs.type:
        report_error('type mismatch in assignment', span)
      return node
    case SIf(span, clause, _, _):
      # TODO: maybe somehow check this before the body
      if not isinstance(clause.type, TBool):
        report_error('if-statement clause should be a bool', span)
      return node
    case SWhile(span, clause, _):
      # TODO: maybe somehow check this before the body
      if not isinstance(clause.type, TBool):
        report_error('while-statement clause should be a bool', span)
      return node

    case _:
      report_error('unexpected node in type check', node.span)

type_check = make_traverse(_type_check)
