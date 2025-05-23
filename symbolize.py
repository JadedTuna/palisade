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
    case EFnParam(span, type, sec, name, _) | EGlobal(span, type, sec, name, _):
      sym = symtab.lookup(name)
      if sym is not None:
        report_error_cont(f'redefinition of parameter {name}', span)
        report_note('previously defined here', sym.origin)
        exit(1)
      sym = Symbol(name, type, sec, span)
      symtab.register(name, sym)
      if isinstance(node, EFnParam):
        return EFnParam(span, type, sec, name, sym)
      return EGlobal(span, type, sec, name, sym)
    case SScope(span, stmts, sec, symtab_):
      symtab_.parent = symtab
      nstmts = [symbolize(stmt, symtab_) for stmt in stmts]
      return SScope(span, nstmts, sec, symtab_)
    case SVarDef(span, sec, (EId(name=name) | EArray(expr=EId(name=name))) as lhs, rhs):
      nrhs = symbolize(rhs, symtab)
      sym = symtab.lookup(name)
      if sym is not None:
        report_error_cont(f'redefinition of {name}', span)
        report_note('previously defined here', sym.origin)
        exit(1)
      symtab.register(name, Symbol(name, TUnresolved(), sec, span))
      nlhs = symbolize(lhs, symtab)
      return SVarDef(span, sec, nlhs, nrhs)
    case SFnDef(span, EId(_, _, _, name, _) as lhs, params, reseclabel, retype,
                SScope(_, _, _, symtab_) as body):
      sym = symtab.lookup(name)
      if sym is not None:
        report_error_cont(f'redefinition of {name}', span)
        report_note('previously defined here', sym.origin)
        exit(1)
      # register function
      symtab.register(name, Symbol(name, TUnresolved(), reseclabel, span))
      nlhs = symbolize(lhs, symtab)
      # register parameters
      # shadowing is allowed at this point, since symtab_
      # does not have a parent just yet
      nparams = [symbolize(param, symtab_) for param in params]
      # finally, symbolize the body
      nbody = symbolize(body, symtab)
      return SFnDef(span, nlhs, nparams, reseclabel, retype, nbody)
    case _:
      return map_tree(symbolize, node, symtab)
