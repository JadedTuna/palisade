from lib.ast import *
from lib.utils import *
from traverse import make_traverse

# TODO: if before type-check, maybe have TUnresolved()

def _assign_security_labels(node: AstNode):
  match node:
    case EInt() | EBool():
      return node
    case EId(span, type, _, name, sym):
      return EId(span, type, sym.secure, name, sym)
    case EUnOp(span, type, _, op, expr):
      return EUnOp(span, type, expr.secure, op, expr)
    case EBinOp(span, type, _, op, lhs, rhs):
      sec = HIGH if lhs.secure or rhs.secure else LOW
      return EBinOp(span, type, sec, op, lhs, rhs)
    case SScope() | SVarDef() | SAssign() | SIf() | SWhile() | SDebug() | File():
      return node
    case _:
      report_error('unexpected node while assigning security labels', node.span)

def _security_debug(node: AstNode):
  match node:
    case SDebug(span, id):
      report_debug(id.name, id.span, None, id)
      return node
    case _:
      return node

def _check_explicit_flows(node: AstNode):
  match node:
    case EInt() | EBool() | EId() | EUnOp() | EBinOp():
      return node
    case SScope() | SIf() | SWhile() | SDebug() | File():
      return node
    case SVarDef(span, _, lhs, rhs):
      if lhs.secure == LOW and rhs.secure == HIGH:
        # TODO: have diff function with diff colors
        report_security_error('insecure explicit flow', span)
      return node
    case SAssign(span, lhs, rhs):
      if lhs.secure == LOW and rhs.secure == HIGH:
        # TODO: have diff function with diff colors
        report_security_error('insecure explicit flow', span)
      return node

    case _:
      report_error('unexpected node while checking explicit flows', node.span)

assign_security_labels = make_traverse(_assign_security_labels)
security_debug = make_traverse(_security_debug)
check_explicit_flows = make_traverse(_check_explicit_flows)
