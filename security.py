from lib.ast import *
from lib.utils import *
from traverse import walk_tree, map_tree, fold_tree, partial, traverse_tree

def assign_security_labels(node: AstNode):
  match node:
    case EInt() | EBool():
      return map_tree(assign_security_labels, node)
    case EId(span, type, _, name, sym):
      return EId(span, type, sym.secure, name, sym)
    case EUnOp(span, type, _, op, expr):
      nexpr = assign_security_labels(expr)
      return EUnOp(span, type, nexpr.secure, op, nexpr)
    case EBinOp(span, type, _, op, lhs, rhs):
      nlhs = assign_security_labels(lhs)
      nrhs = assign_security_labels(rhs)
      sec = HIGH if nlhs.secure == HIGH or nrhs.secure == HIGH else LOW
      return EBinOp(span, type, sec, op, nlhs, nrhs)
    case SScope() | SVarDef() | SAssign() | SIf() | SWhile() | SDebug() | File():
      return map_tree(assign_security_labels, node)
    case _:
      report_error('unhandled node while assigning security labels', node.span)

def check_explicit_flows(node: AstNode):
  match node:
    case EInt() | EBool() | EId() | EUnOp() | EBinOp():
      walk_tree(check_explicit_flows, node)
    case SScope() | SIf() | SWhile() | SDebug() | File():
      walk_tree(check_explicit_flows, node)
    case SVarDef(span, sec, lhs, rhs):
      if lhs.secure == LOW and rhs.secure == HIGH:
        report_security_error('insecure explicit flow', span)
    case SAssign(span, lhs, rhs):
      if lhs.secure == LOW and rhs.secure == HIGH:
        report_security_error('insecure explicit flow', span)
    case _:
      report_error('unexpected node while checking explicit flows', node.span)
