from lib.ast import *
from lib.utils import *
from functools import partial

def make_traverse_data(postcb, precb):
  return partial(traverse_data, postcb, precb)

def make_traverse(postcb, precb = lambda x: x):
  return partial(traverse, precb, postcb)

def traverse_data(postcb, precb, data, node: AstNode):
  nnode, ndata = precb(node, data)
  f = partial(traverse_data, postcb, precb, ndata)
  return postcb(_traverse(f, nnode), ndata)

def traverse(postcb, precb, node: AstNode):
  f = partial(traverse, postcb, precb)
  return postcb(_traverse(f, precb(node)))

def _traverse(f, node: AstNode):
  match node:
    case EId() | EInt() | EBool():
      return node
    case EUnOp(span, type, sec, op, expr):
      nexpr = f(expr)
      return EUnOp(span, type, sec, op, nexpr)
    case EBinOp(span, type, sec, op, lhs, rhs):
      nlhs = f(lhs)
      nrhs = f(rhs)
      return EBinOp(span, type, sec, op, nlhs, nrhs)

    case SScope(span, stmts, symtab):
      nstmts = [f(s) for s in stmts]
      return SScope(span, nstmts, symtab)
    case SVarDef(span, sec, lhs, rhs):
      nlhs = f(lhs)
      nrhs = f(rhs)
      return SVarDef(span, sec, nlhs, nrhs)
    case SAssign(span, lhs, rhs):
      nlhs = f(lhs)
      nrhs = f(rhs)
      return SAssign(span, nlhs, nrhs)
    case SIf(span, clause, body, else_stmt):
      nclause = f(clause)
      nbody = f(body)
      nelse_stmt = f(else_stmt) if else_stmt else None
      return SIf(span, nclause, nbody, nelse_stmt)
    case SWhile(span, clause, body):
      nclause = f(clause)
      nbody = f(body)
      return SWhile(span, nclause, nbody)

    case File(span, stmts, symtab):
      nstmts = [f(s) for s in stmts]
      return File(span, nstmts, symtab)

    case _:
      report_error('unexpected node in traverse', node.span)
