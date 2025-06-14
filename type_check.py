from lib.ast import *
from lib.types import *
from lib.utils import report_error, report_error_cont, exit
from traverse import map_tree, walk_tree
from debug import debug_ast
from parser import BINOPS, UNOPS, PRECTABLE_BOOLEAN, PRECTABLE_COMPARISON

def type_eunop(op: str, span: Span, expr: Expr) -> Type:
  opkind = UNOPS[op]
  match expr.type:
    case TInt() if opkind == PRECTABLE_BOOLEAN:
      report_error('cannot use boolean operators with integers', span)
    case TInt():
      return TInt()
    case TBool() if opkind == PRECTABLE_BOOLEAN:
      return TBool()
    case TBool():
      report_error('can only use boolean operators with booleans', span)
    case _:
      raise RuntimeError(expr)

def type_ebinop(op: str, span: Span, lhs: Expr, rhs: Expr) -> Type:
  opkind = BINOPS[op][0]
  match (lhs.type, rhs.type):
    case (TInt(), TInt()) if opkind == PRECTABLE_BOOLEAN:
      report_error('cannot use boolean operators with integers', span)
    case (TInt(), TInt()) if opkind == PRECTABLE_COMPARISON:
      return TBool()
    case (TInt(), TInt()):
      return TInt()
    case (TBool(), TBool()) if opkind == PRECTABLE_BOOLEAN:
      return TBool()
    case (TBool(), TBool()):
      report_error('can only use boolean operators with booleans', span)
    case _:
      report_error_cont('type mismatch', span)
      exit(1)

def type_annotate(node: AstNode):
  match node:
    case EId(span, TUnresolved(), sec, name, sym):
      return EId(span, sym.type, sec, name, sym)
    case EInt(span, TUnresolved(), sec, v):
      return EInt(span, TInt(), sec, v)
    case EBool(span, TUnresolved(), sec, v):
      return EBool(span, TBool(), sec, v)
    case FnParam(type=type, sym=sym):
      sym.type = type
      return node
    case EArray() | EUnOp() | EBinOp() | EArrayLiteral() | ECall():
      return map_tree(type_annotate, node)

    case SVarDef(span, (EId(sym=sym) | EArray(expr=EId(sym=sym))) as lhs, rhs):
      nrhs = type_annotate(rhs)
      # type inference
      sym.type = nrhs.type
      nlhs = type_annotate(lhs)
      return SVarDef(span, nlhs, nrhs)
    case SFnDef(span, EId(_, _, _, _, sym) as lhs, params, retype, body):
      nparams = [type_annotate(param) for param in params]
      # functions don't have explicit type defined, create one
      tparams = [param.type for param in params]
      sym.type = TFn(retype, tparams, None)
      nlhs = type_annotate(lhs)
      # annotate body after connecting type to symbol, to handle recursive calls
      nbody = type_annotate(body)
      nnode = SFnDef(span, nlhs, nparams, retype, nbody)
      sym.type.sfndef = nnode
      return nnode
    case SScope() | SAssign() | SIf() | SWhile() | STryCatch() | SThrow() | SDebug() | SReturn() | EDeclassify() | File():
      return map_tree(type_annotate, node)
    case SGlobal(span, type, EId() as expr, origsec):
      expr.sym.type = type
      nexpr = type_annotate(expr)
      return SGlobal(span, type, nexpr, origsec)
    case SGlobal(span, type, EArray(expr=EId() as id, index=EInt(value=length)) as expr, origsec):
      id.sym.type = TArray(type, length)
      nexpr = type_annotate(expr)
      return SGlobal(span, type, nexpr, origsec)
    case _:
      report_error('unhandled node in type annotate', node.span)

def type_check_return(node: AstNode, retype: Type):
  match node:
    case SReturn(span, _, expr):
      if expr.type != retype:
        report_error('type mismatch in return', span)
    case _:
      walk_tree(type_check_return, node, retype)

def type_check(node: AstNode):
  match node:
    case EId(span, TUnresolved(), sec, name, sym):
      # any identifiers not resolved in type-annot can be resolved now
      return EId(span, sym.type, sec, name, sym)
    case EId():
      return map_tree(type_check, node)
    case EArray():
      nnode =  map_tree(type_check, node)
      nnode.type = nnode.expr.type.of
      if not isinstance(nnode.index.type, TInt):
        report_error('array index must be an int', nnode.index.span)
      return nnode
    case EArrayLiteral():
      nnode = map_tree(type_check, node)
      if not all(val.type == nnode.values[0].type for val in nnode.values):
        report_error('values of different types in array literal', nnode.span)
      nnode.type.of = nnode.values[0].type
      return nnode
    case EUnOp(span, TUnresolved(), sec, op, expr):
      nexpr = type_check(expr)
      type = type_eunop(op, span, nexpr)
      return EUnOp(span, type, sec, op, nexpr)
    case EBinOp(span, TUnresolved(), sec, op, lhs, rhs):
      nlhs = type_check(lhs)
      nrhs = type_check(rhs)
      type = type_ebinop(op, span, nlhs, nrhs)
      return EBinOp(span, type, sec, op, nlhs, nrhs)
    case ECall(span, TUnresolved(), sec, EId(_, _, _, name, sym) as lhs, params):
      nnode = map_tree(type_check, node)
      if not isinstance(sym.type, TFn):
        report_error(f'{name} is not a function', span)
      for idx, (ty, param) in enumerate(zip(sym.type.params, params)):
        if param.type != ty:
          report_error(f'function parameter #{idx+1} has invalid type', param.span)
      # propagate function return type to the ECall
      nnode.type = sym.type.retype
      return nnode
    case EDeclassify(span, _, sec, expr):
      nexpr = type_check(expr)
      ntype = nexpr.type
      return EDeclassify(span, ntype, sec, nexpr)
    case EId() | EInt() | EBool():
      return map_tree(type_check, node)

    case SAssign(span, _, _):
      nnode = map_tree(type_check, node)
      if nnode.lhs.type != nnode.rhs.type:
        report_error('type mismatch in assignment', span)
      return nnode
    case SVarDef(span, EArray(expr=EId(sym=sym), index=EInt() as index) as lhs, EId(sym=rsym) as rhs):
      nrhs = type_check(rhs)
      # type inference
      if not isinstance(nrhs.type, TArray):
        report_error('type mismatch, expected array type', nrhs.span)
      sym.type = nrhs.type
      nlhs = type_check(lhs)
      # guaranteed by type-checking
      assert(isinstance(rsym.type, TArray))
      if rsym.type.length != index.value:
        report_error('size mismatch between arrays', nrhs.span)
      return SVarDef(span, nlhs, nrhs)
    case SVarDef(span, (EId(sym=sym) | EArray(expr=EId(sym=sym))) as lhs, rhs):
      nrhs = type_check(rhs)
      # type inference
      sym.type = nrhs.type
      nlhs = type_check(lhs)
      match (nlhs, nrhs, nrhs.type):
        case (EId(), EId(), TArray()):
          # not allowed to define arrays without size specification
          report_error('array definition must have size specification', span)
        case _:
          pass
      return SVarDef(span, nlhs, nrhs)
    case SFnDef(span, name, params, retype, body):
      nname = type_check(name)
      nparams = list(map(type_check, params))
      nbody = type_check(body)
      # make sure return statements have correct types
      type_check_return(nbody, retype)
      return SFnDef(span, nname, nparams, retype, body)
    case SIf(span, clause, body, else_stmt):
      nclause = type_check(clause)
      if not isinstance(nclause.type, TBool):
        report_error('if-statement clause should be a bool', span)
      nbody = type_check(body)
      nelse_stmt = type_check(else_stmt) if else_stmt else None
      return SIf(span, nclause, nbody, nelse_stmt)
    case SWhile(span, clause, body):
      nclause = type_check(clause)
      if not isinstance(nclause.type, TBool):
        report_error('while-statement clause should be a bool', span)
      nbody = type_check(body)
      return SWhile(span, nclause, nbody)
    case SScope() | SVarDef() |  STryCatch() | SThrow() | SDebug() | SReturn() | SGlobal() | File() | FnParam():
      return map_tree(type_check, node)
    case _:
      report_error('unhandled node in type check', node.span)
