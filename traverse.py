'''
# example usage of map_tree:
def handler(arg1, arg2, node: AstNode):
  match node:
    case ...
    ...
    case _:
      return map_tree(handler, node, arg1, arg2)
'''

from lib.ast import *
from lib.utils import *
from functools import partial

def map_tree(f, node: AstNode, *args):
  '''Build a new tree by mapping `f` over the each node.'''
  f2 = lambda acc, n: (acc, f(n, *args))
  return _traverse_tree(f2, None, node)[1]

def walk_tree(f, node: AstNode, *args):
  '''Walk a tree and map `f` over each node. Does not build a new tree.'''
  f2 = lambda acc, n: (acc, (f(n, *args), n)[1])
  _traverse_tree(f2, None, node)

def traverse_tree(f, acc, node: AstNode, *args):
  '''Traverse a tree, updating `acc` and building a new tree.'''
  f2 = lambda acc1, n: f(acc1, n, *args)
  return _traverse_tree(f2, acc, node)

def fold_tree(f, acc, node: AstNode, *args):
  '''Map `f` over the each node and collect the results in `acc`.'''
  return traverse_tree(f, acc, node, *args)[0]

def _traverse_tree(f, acc, node: AstNode):
  match node:
    case EId() | EInt() | EBool():
      return (acc, node)
    case EUnOp(span, type, sec, op, expr):
      acc, nexpr = f(acc, expr)
      return (acc, EUnOp(span, type, sec, op, nexpr))
    case EBinOp(span, type, sec, op, lhs, rhs):
      acc, nlhs = f(acc, lhs)
      acc, nrhs = f(acc, rhs)
      return (acc, EBinOp(span, type, sec, op, nlhs, nrhs))
    case SScope(span, stmts, symtab):
      nstmts = []
      for stmt in stmts:
        acc, nstmt = f(acc, stmt)
        nstmts.append(nstmt)
      return (acc, SScope(span, nstmts, symtab))
    case SVarDef(span, sec, lhs, rhs):
      acc, nlhs = f(acc, lhs)
      acc, nrhs = f(acc, rhs)
      return (acc, SVarDef(span, sec, nlhs, nrhs))
    case SAssign(span, lhs, rhs):
      acc, nlhs = f(acc, lhs)
      acc, nrhs = f(acc, rhs)
      return (acc, SAssign(span, nlhs, nrhs))
    case SIf(span, clause, body, else_stmt):
      acc, nclause = f(acc, clause)
      acc, nbody = f(acc, body)
      acc, nelse_stmt = f(acc, else_stmt) if else_stmt else (acc, None)
      return (acc, SIf(span, nclause, nbody, nelse_stmt))
    case SWhile(span, clause, body):
      acc, nclause = f(acc, clause)
      acc, nbody = f(acc, body)
      return (acc, SWhile(span, nclause, nbody))
    case SDebug(span, expr):
      acc, nexpr = f(acc, expr)
      return (acc, SDebug(span, nexpr))
    case File(span, stmts, symtab):
      nstmts = []
      for stmt in stmts:
        acc, nstmt = f(acc, stmt)
        nstmts.append(nstmt)
      return (acc, File(span, nstmts, symtab))
    case _:
      report_error('unhandled node in traverse', node.span)
