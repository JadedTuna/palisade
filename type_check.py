from lib.ast import *

def type_check(ast: AstNode):
  match ast:
    case EId(TUnresolved(), v):
      raise NotImplementedError
    case EInt(TUnresolved(), v):
      return EInt(TInt(), v)
    case EBool(TUnresolved(), v):
      return EBool(TBool(), v)
    case EBinOp(TUnresolved(), op, lhs, rhs):
      nlhs = type_check(lhs)
      nrhs = type_check(rhs)
      type = type_resolve(nlhs, nrhs)
      return EBinOp(type, op, nlhs, nrhs)
