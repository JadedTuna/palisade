from lib.ast import *
from lib.utils import report_error
from traverse import make_traverse_data

def _symbolize_pre(node: AstNode, symtab: SymTab):
  match node:
    case SScope(_, _, symtab_):
      symtab_.parent = symtab
      return (node, symtab_)
    case SVarDef(span, secure, lhs, _):
      sym = symtab.lookup(lhs.name)
      if sym is not None:
        report_error(f'redefinition of {lhs.name}', span)
      symtab.register(lhs.name, Symbol(lhs.name, TUnresolved(), secure, span))
      return (node, symtab)
    case _:
      return (node, symtab)

def _symbolize_post(node: AstNode, symtab: SymTab):
  match node:
    case EId(span, type, sec, name, _):
      sym = symtab.lookup(name)
      if sym is None:
        report_error('use of undefined variable', span)
      return EId(span, type, sec, name, sym)
    # TODO: functions?
    case _:
      return node

symbolize = make_traverse_data(_symbolize_post, _symbolize_pre)
