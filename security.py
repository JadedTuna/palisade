from lib.ast import *
from lib.utils import *
from traverse import walk_tree, map_tree

def assign_security_labels(node: AstNode):
  match node:
    case EInt() | EBool() | EFnParam() | SGlobal():
      return map_tree(assign_security_labels, node)
    case EId(span, type, _, name, sym):
      return EId(span, type, sym.secure, name, sym)
    case EArray(span, type, _, expr, index):
      nnode = map_tree(assign_security_labels, node)
      nnode.secure = nnode.expr.sym.secure
      return nnode
    case EArrayLiteral(span, type, _, values):
      nnode = map_tree(assign_security_labels, node)
      nnode.secure = any([v.secure for v in nnode.values])
      return nnode
    case EUnOp(span, type, _, op, expr):
      nexpr = assign_security_labels(expr)
      return EUnOp(span, type, nexpr.secure, op, nexpr)
    case EBinOp(span, type, _, op, lhs, rhs):
      nlhs = assign_security_labels(lhs)
      nrhs = assign_security_labels(rhs)
      sec = HIGH if nlhs.secure == HIGH or nrhs.secure == HIGH else LOW
      return EBinOp(span, type, sec, op, nlhs, nrhs)
    case ECall():
      nnode = map_tree(assign_security_labels, node)
      nnode.secure = nnode.name.secure
      return nnode
    case SIf() | SWhile():
      nnode = map_tree(assign_security_labels, node)
      nnode.body.secure = nnode.clause.secure
      return nnode
    case SDeclassify(span, type, _, expr):
      nexpr = assign_security_labels(expr)
      return SDeclassify(span, type, LOW, nexpr)
    case SScope() | SVarDef() | SFnDef() | SAssign() | STryCatch() | SThrow() | SDebug() | File():
      return map_tree(assign_security_labels, node)
    case _:
      report_error('unhandled node while assigning security labels', node.span)

def check_explicit_flows(node: AstNode):
  match node:
    case EInt() | EBool() | EId() | EArray() | EArrayLiteral() | EUnOp() | EBinOp():
      walk_tree(check_explicit_flows, node)
    case SScope() | SIf() | SWhile() | STryCatch() | SThrow() | SDebug() | File():
      walk_tree(check_explicit_flows, node)
    case SVarDef(span, _, lhs, rhs):
      if lhs.secure == LOW and rhs.secure == HIGH:
        report_security_error('insecure explicit flow', span)
    case SFnDef():
      # TODO
      pass
    case SAssign(span, lhs, rhs):
      if lhs.secure == LOW and rhs.secure == HIGH:
        report_security_error('insecure explicit flow', span)
    case _:
      report_error('unexpected node while checking explicit flows', node.span)

def check_implicit_flows(node: AstNode, pc: bool):
  match node:
    case EArray(_, _, sec, _, index):
       if sec == LOW and index.secure == HIGH:
         report_security_error("can't index with a high value in a low array", index.span)
       walk_tree(check_implicit_flows, node, pc)
    case SIf(_, clause):
      pc = clause.secure == HIGH or pc == HIGH
      walk_tree(check_implicit_flows, node, pc)
    case SWhile(_, clause):
      if pc == HIGH or clause.secure == HIGH:
        report_security_error('insecure implicit flow - while loop using a high guard', node.span)
      walk_tree(check_implicit_flows, node, pc)
    case SAssign(_, lhs):
      if pc == HIGH and lhs.secure == LOW:
        report_security_error('insecure implicit flow inside high guard', node.span)
      walk_tree(check_implicit_flows, node, pc)
    case SThrow():
      if pc == HIGH:
        report_security_error("insecure implicit flow - can't throw inside a high guard", node.span)
      walk_tree(check_implicit_flows, node, pc)
    case _:
      walk_tree(check_implicit_flows, node, pc)