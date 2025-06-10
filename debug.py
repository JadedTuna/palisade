from lib.ast import *
from lib.types import *
from lib.utils import *
from traverse import walk_tree

def dpprint_type(type: Type) -> str:
  match type:
    case TInt(): return 'int'
    case TBool(): return 'bool'
    case TUnresolved(): return 'unresolved'
    case _: return red('invalid')

def dpprint_seclabel(seclabel: SecLabel) -> str:
  return str(seclabel)

def debug_ast(node: AstNode):
  match node:
    case SDebug(_, EId() as id):
      report_debug(f'variable {id.name}', id.span)
      print(blue('name:'), id.name, end=', ')
      print(blue('type:'), dpprint_type(id.type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(id.secure))
      if id.sym is not SYMBOL_UNRESOLVED:
        lnum = id.sym.origin.lnum + 1
        report_debug(f'defined on line {lnum}', id.sym.origin, '')
    case SDebug(_, EInt(span, t, sec, _) | EBool(span, t, sec, _) | ECall(span, t, sec, _, _)):
      ts = dpprint_type(t)
      ss = dpprint_seclabel(sec)
      report_debug(f'{blue("type:")} {ts}, {blue("seclabel:")} {ss}', span)
    case SDebug(_, EUnOp(span, t, sec, _, Expr(_, et, esec))):
      report_debug(f'expression with unary operator', span)
      print(blue('type:'), dpprint_type(t), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(sec))
      print(cyan('expr: '), end='')
      print(blue('type:'), dpprint_type(et), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(esec), '\n')
    case SDebug(_, EBinOp(span, type, secure, op, lhs, rhs)):
      report_debug(f'expression with binary operator', span)
      print(blue('type:'), dpprint_type(type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(secure))

      print(cyan('lhs: '), end='')
      print(blue('type:'), dpprint_type(lhs.type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(lhs.secure))

      print(cyan('rhs: '), end='')
      print(blue('type:'), dpprint_type(rhs.type), end=', ')
      print(blue('seclabel:'), dpprint_seclabel(rhs.secure), '\n')
    case SDebug(_, x):
      report_debug('no special debug handler found', x.span, None, x)
    case _:
      walk_tree(debug_ast, node)
