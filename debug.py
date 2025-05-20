from lib.ast import *
from lib.types import *
from lib.utils import *
from traverse import make_traverse

def dpprint_type(type: Type) -> str:
  match type:
    case TInt(): return 'int'
    case TBool(): return 'bool'
    case TUnresolved(): return 'unresolved'
    case _: return red('invalid')

def dpprint_seclabel(seclabel: bool) -> str:
  return 'high' if seclabel else 'low'

def _debug_ast(node: AstNode):
  match node:
    case SDebug(_, EId() as id):
      report_debug(f'variable {id.name}', id.span)
      print(blue('name:'), id.name, end=', ')
      print(blue('type:'), dpprint_type(id.type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(id.secure))
      if id.sym is not SYMBOL_UNRESOLVED:
        lnum = id.sym.origin.lnum + 1
        report_debug(f'defined on line {lnum}', id.sym.origin)
      print()
      return node
    case SDebug(_, EBinOp(span, type, secure, op, lhs, rhs)):
      report_debug(f'expression with binary operator', span)
      print(blue('type:'), dpprint_type(type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(secure))

      print(cyan('lhs: '), end='')
      print(blue('type:'), dpprint_type(lhs.type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(lhs.secure))

      print(cyan('rhs: '), end='')
      print(blue('type:'), dpprint_type(rhs.type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(rhs.secure))
      print()

      return node
    case SDebug(_, x):
      report_debug('', x.span, None, x)
      return node
    case _:
      return node

debug_ast = make_traverse(_debug_ast)
