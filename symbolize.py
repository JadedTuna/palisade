from lib.ast import *
from lib.utils import *
from traverse import map_tree

def symbolize(node: AstNode, symtab: SymTab):
  match node:
    case EId(span, type, sec, name, _):
      sym = symtab.lookup(name)
      if sym is None:
        report_error('use of undefined variable', span)
      return EId(span, type, sec, name, sym)
    case SScope(span, stmts, sec, symtab_):
      symtab_.parent = symtab
      nstmts = [symbolize(stmt, symtab_) for stmt in stmts]
      return SScope(span, nstmts, sec, symtab_)
    case SVarDef(span, sec, EId(_, _, _, name, _) | EArray(_, _, _, EId(_, _, _, name, _)) as lhs, rhs):
      nrhs = symbolize(rhs, symtab)
      sym = symtab.lookup(name)
      if sym is not None:
        report_error_cont(f'redefinition of {name}', span)
        report_note('previously defined here', sym.origin)
        exit(1)
      symtab.register(name, Symbol(name, TUnresolved(), sec, span))
      nlhs = symbolize(lhs, symtab)
      return SVarDef(span, sec, nlhs, nrhs)
    case _:
      return map_tree(symbolize, node, symtab)
