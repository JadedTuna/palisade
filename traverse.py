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
  f2 = lambda acc_, n: f(acc_, n, *args)
  return _traverse_tree(f2, acc, node)

def fold_tree(f, acc, node: AstNode, *args):
  '''Map `f` over the each node and collect the results in `acc`.'''
  f2 = lambda acc_, n: (f(acc_, n, *args), n)
  return traverse_tree(f2, acc, node, *args)[0]

def _traverse_tree(f, acc, node: AstNode):
  match node:
    case EId() | EInt() | EBool() | FnParam():
      return (acc, node)
    case EArray(span, type, sec, expr, index):
      acc, nexpr = f(acc, expr)
      acc, nindex = f(acc, index)
      return (acc, EArray(span, type, sec, nexpr, nindex))
    case EArrayLiteral(span, type, sec, values):
      nvalues = []
      for expr in values: 
        acc, nexpr = f(acc, expr)
        nvalues.append(nexpr)
      return (acc, EArrayLiteral(span, type, sec, nvalues))
    case EUnOp(span, type, sec, op, expr):
      acc, nexpr = f(acc, expr)
      return (acc, EUnOp(span, type, sec, op, nexpr))
    case EBinOp(span, type, sec, op, lhs, rhs):
      acc, nlhs = f(acc, lhs)
      acc, nrhs = f(acc, rhs)
      return (acc, EBinOp(span, type, sec, op, nlhs, nrhs))
    case ECall(span, type, sec, name, params):
      acc, nname = f(acc, name)
      nparams = []
      for param in params:
        acc, nparam = f(acc, param)
        nparams.append(nparam)
      return (acc, ECall(span, type, sec, nname, nparams))
    case SScope(span, stmts, sec, symtab):
      nstmts = []
      for stmt in stmts:
        acc, nstmt = f(acc, stmt)
        nstmts.append(nstmt)
      return (acc, SScope(span, nstmts, sec, symtab))
    case SGlobal(span, type, expr, origsec):
      acc, nexpr = f(acc, expr)
      return (acc, SGlobal(span, type, nexpr, origsec))
    case SVarDef(span, lhs, rhs):
      acc, nlhs = f(acc, lhs)
      acc, nrhs = f(acc, rhs)
      return (acc, SVarDef(span, nlhs, nrhs))
    case SFnDef(span, name, args, retype, body):
      acc, nname = f(acc, name)
      nargs = []
      for arg in args:
        acc, narg = f(acc, arg)
        nargs.append(narg)
      acc, nbody = f(acc, body)
      return (acc, SFnDef(span, nname, nargs, retype, nbody))
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
    case STryCatch(span, try_body, catch_body):
      acc, ntry = f(acc, try_body)
      acc, ncatch = f(acc, catch_body)
      return (acc, STryCatch(span, ntry, ncatch))
    case SThrow():
      return (acc, node)
    case SDebug(span, expr):
      acc, nexpr = f(acc, expr)
      return (acc, SDebug(span, nexpr))
    case SReturn(span, sec, expr):
      acc, nexpr = f(acc, expr)
      return (acc, SReturn(span, sec, nexpr))
    case EDeclassify(span, type, sec, expr):
      acc, nexpr = f(acc, expr)
      return (acc, EDeclassify(span, type, sec, nexpr))
    case File(span, stmts, symtab, ins, outs):
      nstmts = []
      nins = []
      nouts = []
      for in_ in ins:
        acc, nin = f(acc, in_)
        nins.append(nin)
      for out in outs:
        acc, nout = f(acc, out)
        nouts.append(nout)
      for stmt in stmts:
        acc, nstmt = f(acc, stmt)
        nstmts.append(nstmt)
      return (acc, File(span, nstmts, symtab, nins, nouts))
    case _:
      report_error('unhandled node in traverse', node.span)
