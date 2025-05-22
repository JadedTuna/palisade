from lib.ast import *
from lib.types import *
from lib.utils import report_error, report_error_cont, exit
from traverse import map_tree
from debug import debug_ast
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
      report_error_cont('type mismatch', span)
      debug_ast(SDebug(span, lhs))
      debug_ast(SDebug(span, rhs))
      exit(1)

def type_annotate(node: AstNode):
  match node:
    case EId(span, TUnresolved(), sec, name, sym):
      return EId(span, sym.type, sec, name, sym)
    case EInt(span, TUnresolved(), sec, v):
      return EInt(span, TInt(), sec, v)
    case EBool(span, TUnresolved(), sec, v):
      return EBool(span, TBool(), sec, v)
    case EUnOp() | EBinOp():
      return map_tree(type_annotate, node)
    case SVarDef(span, sec, EId(_, _, _, _, sym) as lhs, rhs):
      nrhs = type_annotate(rhs)
      # type inference
      sym.type = nrhs.type
      nlhs = type_annotate(lhs)
      return SVarDef(span, sec, nlhs, nrhs)
    case SScope() | SAssign() | SIf() | SWhile() | SDebug() | File():
      return map_tree(type_annotate, node)
    case _:
      report_error('unhandled node in type annotate', node.span)

def type_check(node: AstNode):
  match node:
    case EId(span, TUnresolved(), sec, name, sym):
      # any identifiers not resolved in type-annot can be resolved now
      return EId(span, sym.type, sec, name, sym)
    case EId():
      return map_tree(type_check, node)
    case EUnOp(span, TUnresolved(), _, op, expr):
      nexpr = type_check(expr)
      type = type_eunop(op, span, nexpr)
      return EUnOp(span, type, sec, op, nexpr)
    case EBinOp(span, TUnresolved(), sec, op, lhs, rhs):
      nlhs = type_check(lhs)
      nrhs = type_check(rhs)
      type = type_ebinop(op, span, nlhs, nrhs)
      return EBinOp(span, type, sec, op, nlhs, nrhs)
    case EId() | EInt() | EBool():
      return map_tree(type_check, node)
    case SAssign(span, _, _):
      nnode = map_tree(type_check, node)
      if nnode.lhs.type != nnode.rhs.type:
        report_error('type mismatch in assignment', span)
      return nnode
    case SVarDef(span, sec, EId(_, _, _, _, sym) as lhs, rhs):
      nrhs = type_check(rhs)
      # type inference
      sym.type = nrhs.type
      nlhs = type_check(lhs)
      return SVarDef(span, sec, nlhs, nrhs)
    case SIf(span, clause, body, else_stmt):
      nclause = type_check(clause)
      if not isinstance(nclause.type, TBool):
        report_error('if-statement clause should be a bool', span)
      nbody = type_check(body)
      nelse_stmt = type_check(else_stmt) if else_stmt else None
      return SIf(span, nclause, nbody, nelse_stmt)
    case SWhile(span, clause, body):
      nclause = type_check(clause)
      if not isinstance(clause.type, TBool):
        report_error('while-statement clause should be a bool', span)
      nbody = type_check(body)
      return SWhile(span, nclause, nbody)
    case SScope() | SVarDef() | SDebug() | File():
      return map_tree(type_check, node)
    case _:
      report_error('unhandled node in type check', node.span)
