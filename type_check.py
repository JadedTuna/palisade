from lib.ast import *
from lib.types import *
from lib.utils import report_error, pprint
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

def type_check(ast: AstNode):
  match ast:
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

    case SScope(span, stmts, symtab_):
      symtab_.parent = symtab
      nstmts = [type_check(s, symtab_) for s in stmts]
      return SScope(span, nstmts, symtab_)
    case SVarDef(span, secure, lhs, rhs):
      sym = symtab.lookup(lhs.name)
      if sym is not None:
        report_error(f'redefinition of {lhs.name}', span)
      nrhs = type_check(rhs, symtab)
      # type inference
      type = nrhs.type
      symtab.register(lhs.name, Symbol(lhs.name, type, secure))
      nlhs = type_check(lhs, symtab)
      return SVarDef(span, secure, nlhs, nrhs)
    case SAssign(span, lhs, rhs):
      nlhs = type_check(lhs, symtab)
      nrhs = type_check(rhs, symtab)
      if nlhs.type != nrhs.type:
        report_error('type mismatch in assignment', span)
      return SAssign(span, nlhs, nrhs)
    case SIf(span, clause, body, else_stmt):
      nclause = type_check(clause, symtab)
      if not isinstance(nclause.type, TBool):
        report_error('if-statement clause should be a bool', span)
      nbody = type_check(body, symtab)
      nelse_stmt = type_check(else_stmt, symtab) if else_stmt else None
      return SIf(span, nclause, nbody, nelse_stmt)
    case SWhile(span, clause, body):
      nclause = type_check(clause, symtab)
      if not isinstance(nclause.type, TBool):
        report_error('while-statement clause should be a bool', span)
      nbody = type_check(body, symtab)
      return SWhile(span, nclause, nbody)

    case File(span, stmts, symtab_):
      nstmts = [type_check(s, symtab_) for s in stmts]
      return File(span, nstmts, symtab_)

    case _:
      report_error('unexpected node in type check', ast.span)
