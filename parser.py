from lib.ast import *
from lib.types import *
from lib.utils import report_error

PRECTABLE_ARITH      = 0
PRECTABLE_BITWISE    = 1
PRECTABLE_SHIFT      = 2
PRECTABLE_BOOLEAN    = 3
PRECTABLE_COMPARISON = 4

PRECTABLE_AUTO_RESOLUTION = {
  (PRECTABLE_ARITH, PRECTABLE_COMPARISON):   True,
  (PRECTABLE_BITWISE, PRECTABLE_COMPARISON): True,
  (PRECTABLE_SHIFT, PRECTABLE_COMPARISON):   True,

  (PRECTABLE_COMPARISON, PRECTABLE_ARITH):   False,
  (PRECTABLE_COMPARISON, PRECTABLE_BITWISE): False,
  (PRECTABLE_COMPARISON, PRECTABLE_SHIFT):   False,
}

BINOPS = {
  '+': (PRECTABLE_ARITH, 1),
  '-': (PRECTABLE_ARITH, 1),
  '*': (PRECTABLE_ARITH, 2),
  '/': (PRECTABLE_ARITH, 2),
  '%': (PRECTABLE_ARITH, 2),

  '^':  (PRECTABLE_BITWISE, 1),
  '|':  (PRECTABLE_BITWISE, 1),
  '&':  (PRECTABLE_BITWISE, 1),

  '<<': (PRECTABLE_SHIFT, 1),
  '>>': (PRECTABLE_SHIFT, 1),

  '||': (PRECTABLE_BOOLEAN, 1),
  '&&': (PRECTABLE_BOOLEAN, 1),

  '<':  (PRECTABLE_COMPARISON, 1),
  '>':  (PRECTABLE_COMPARISON, 1),
  '<=': (PRECTABLE_COMPARISON, 1),
  '>=': (PRECTABLE_COMPARISON, 1),
  '==': (PRECTABLE_COMPARISON, 1),
  '!=': (PRECTABLE_COMPARISON, 1),
}
UNOPS = {
  '-': PRECTABLE_ARITH,
  '+': PRECTABLE_ARITH,
  '!': PRECTABLE_BOOLEAN,
  '~': PRECTABLE_BITWISE,
}

class Parser:
  def __init__(self, tokens):
    self.tokens = tokens
    self.idx = 0

  def token(self) -> Token:
    if self.idx < len(self.tokens):
      return self.tokens[self.idx]
    else:
      return TOKEN_EOF

  def peek(self, n: int) -> Token:
    self.idx += n
    tok = self.token()
    self.idx -= n
    return tok

  def expect(self, *types) -> Token:
    tok = self.token()
    if tok.type not in types:
      if len(types) > 1:
        s = f'one of {", ".join(types)}'
      else:
        s = types[0]
      report_error(f'expected {s} but got {tok.type}', tok.span)
    self.idx += 1
    return tok

  def maybe(self, *types) -> bool:
    return self.token().type in types

  def consume(self) -> Token:
    tok = self.token()
    self.idx += 1
    return tok

  def check_precedence(self, prev_op, op) -> bool:
    if prev_op is None:
      return False
    prev_type, prev_prio = BINOPS[prev_op.type]
    type, prio = BINOPS[op.type]
    if prev_type == type:
      # same type of op
      return prev_prio >= prio
    elif (prev_type, type) in PRECTABLE_AUTO_RESOLUTION:
      # no ambiguity between op types
      return PRECTABLE_AUTO_RESOLUTION[(prev_type, type)]
    else:
      report_error('ambiguous precedence, use parenthesis', op.span)

  def parse(self) -> File:
    stmts = []
    ins, outs = self.parse_globals()
    while not self.maybe('eof'):
      stmts.append(self.parse_stmt())
    return File(FAKE_SPAN, stmts, SymTab(None, {}), ins, outs)

  def parse_expr(self):
    if(self.maybe('declassify')):
      return self.parse_declassify()
    if(self.maybe('[')):
      return self.parse_array_literal()
    return self.parse_expr_prec(None)

  def parse_expr_prec(self, prev_op):
    expr = self.parse_term()
    while True:
      op = self.token()
      if not op.type in BINOPS:
        # not an operator, expression is done
        return expr
      # check precedence
      if self.check_precedence(prev_op, op):
        # prev_op binds tighter than op
        return expr
      # consume operator token
      self.consume()
      rhs = self.parse_expr_prec(op)
      expr = EBinOp(op.span, TUnresolved(), HIGH, op.type, expr, rhs)

  def parse_term(self):
    if self.maybe('identifier'):
      if self.peek(1).type == '(':
        # function call
        return self.parse_call()
      else:
        return self.parse_lvalue()
    elif self.maybe('integer', 'integer_hex', 'integer_bin', 'integer_oct'):
      return self.parse_integer()
    elif self.maybe('true', 'false'):
      return self.parse_boolean()
    elif self.maybe('('):
      self.expect('(')
      expr = self.parse_expr()
      self.expect(')')
      return expr
    elif self.maybe(*UNOPS):
      op = self.consume()
      return EUnOp(op.span, TUnresolved(), HIGH, op.type, self.parse_term())
    else:
      report_error('unexpected token while parsing expression', self.token().span)

  def parse_lvalue(self) -> ELValue:
    eid = self.parse_identifier()
    if(self.maybe('[')):
      self.expect('[')
      index = self.parse_expr()
      self.expect(']')
      return EArray(eid.span, TUnresolved(), HIGH, eid, index)
    return eid

  def parse_identifier(self) -> EId:
    tok = self.expect('identifier')
    return EId(tok.span, TUnresolved(), HIGH, tok.value, SYMBOL_UNRESOLVED)

  def parse_integer(self) -> EInt:
    tok = self.expect('integer', 'integer_hex', 'integer_bin', 'integer_oct')
    if tok.type == 'integer_hex':
      return EInt(tok.span, TUnresolved(), LOW, int(tok.value, 16))
    if tok.type == 'integer_bin':
      return EInt(tok.span, TUnresolved(), LOW, int(tok.value, 2))
    if tok.type == 'integer_oct':
      return EInt(tok.span, TUnresolved(), LOW, int(tok.value, 8))
    else:
      return EInt(tok.span, TUnresolved(), LOW, int(tok.value))

  def parse_boolean(self) -> EBool:
    tok = self.expect('true', 'false')
    return EBool(tok.span, TUnresolved(), LOW, tok.type == 'true')
  
  def parse_array_literal(self) -> EArrayLiteral:
    tok = self.expect('[')
    values = []
    while True:
      values.append(self.parse_expr())
      if self.maybe(']'):
        self.expect(']')
        break
      self.expect(',')
    return EArrayLiteral(tok.span, TArray(TUnresolved(), len(values)), LOW, values)

  def parse_type(self) -> Type:
    # TODO: array type
    tok = self.expect('int', 'bool')
    if tok.type == 'int':
      return TInt()
    else:
      return TBool()

  def parse_call(self) -> ECall:
    name = self.parse_identifier()
    self.expect('(')
    params = []
    while not self.maybe(')'):
      params.append(self.parse_expr())
      if self.maybe(')'):
        break
      self.expect(',')
    self.expect(')')
    return ECall(name.span, TUnresolved(), LOW, name, params)

  def parse_stmt(self) -> Stmt:
    if self.maybe('{'):
      return self.parse_scope()
    elif self.maybe('fn'):
      return self.parse_fndef()
    elif self.maybe('if'):
      return self.parse_if()
    elif self.maybe('while'):
      return self.parse_while()
    elif self.maybe('try'):
      return self.parse_try_catch()
    elif self.maybe('throw'):
      return self.parse_throw()
    elif self.maybe('debug'):
      return self.parse_debug()
    elif self.maybe('identifier'):
      if self.peek(1).type == ':=':
        return self.parse_vardef()
      return self.parse_assign()
    # TODO: function calls
    else:
      report_error('unexpected token while parsing statement', self.token().span)

  def parse_scope(self) -> SScope:
    tok = self.expect('{')
    stmts = []
    while not self.maybe('}'):
      stmts.append(self.parse_stmt())
    self.expect('}')
    return SScope(tok.span, stmts, HIGH, SymTab(None, {}))

  def parse_assign(self) -> SAssign:
    # lvalue = expr;
    lhs = self.parse_lvalue()
    tok = self.expect('=')
    rhs = self.parse_expr()
    self.expect(';')
    return SAssign(tok.span, lhs, rhs)

  def parse_seclabel(self) -> bool:
    tok = self.expect('high', 'low')
    return tok.type == 'high'

  def parse_fndef(self) -> SFnDef:
    # fn name(params) reseclabel retype body
    tok = self.expect('fn')
    name = self.parse_identifier()
    self.expect('(')
    # arguments
    params = []
    while not self.maybe(')'):
      pseclabel = self.parse_seclabel()
      # TODO: lvalue?
      pname = self.parse_identifier()
      self.expect(':')
      ptype = self.parse_type()
      param = EFnParam(pname.span, ptype, pseclabel, pname.name,
        SYMBOL_UNRESOLVED)
      params.append(param)
      if self.maybe(')'):
        break
      self.expect(',')
    self.expect(')')
    reseclabel = self.parse_seclabel()
    retype = self.parse_type()
    body = self.parse_scope()
    return SFnDef(tok.span, name, params, reseclabel, retype, body)

  def parse_if(self) -> SIf:
    # if (clause) stmt [else stmt]
    tok = self.expect('if')
    self.expect('(')
    clause = self.parse_expr()
    self.expect(')')
    body = self.parse_scope()
    if self.maybe('else'):
      self.expect('else')
      else_stmt = self.parse_scope()
    else:
      else_stmt = None
    return SIf(tok.span, clause, body, else_stmt)

  def parse_while(self) -> SWhile:
    # while (clause) stmt
    tok = self.expect('while')
    self.expect('(')
    clause = self.parse_expr()
    self.expect(')')
    body = self.parse_scope()
    return SWhile(tok.span, clause, body)

  def parse_debug(self) -> SDebug:
    # debug expr;
    tok = self.expect('debug')
    expr = self.parse_expr()
    self.expect(';')
    return SDebug(tok.span, expr)
  
  def parse_declassify(self) -> SDeclassify:
    # declassify expr;
    tok = self.expect('declassify')
    expr = self.parse_expr()
    return SDeclassify(tok.span, TUnresolved(), LOW, expr)
  
  def parse_try_catch(self) -> STryCatch:
    # try { stmts } catch { stmts }
    tok = self.expect('try')
    try_body = self.parse_scope()
    self.expect('catch')
    catch_body = self.parse_scope()
    return STryCatch(tok.span, try_body, catch_body)
    
  def parse_throw(self) -> SThrow:
    # throw;
    tok = self.expect('throw')
    self.expect(';')
    return SThrow(tok.span)

  def parse_vardef(self) -> SVarDef:
    # identifier = expr ;
    lhs = self.parse_lvalue()
    tok = self.expect(':=')
    rhs = self.parse_expr()
    if isinstance(lhs, EArray):
      if not isinstance(lhs.index, EInt):
        report_error('only integer literals allowed when specifying array length', lhs.expr.span)
      if lhs.index.value <= 0:
        report_error('array length must be greater than 0', lhs.expr.span)
      if not isinstance(rhs, EArrayLiteral):
        report_error('no array literal provided while defining array', rhs.span)
      if lhs.index.value > len(rhs.values):
        report_error('the array literal is to short', rhs.span)
      if lhs.index.value < len(rhs.values):
        report_error('the array literal is to long', rhs.span)
    self.expect(';')
    return SVarDef(tok.span, rhs.secure, lhs, rhs)
  
  def parse_global_variable(self) -> EGlobal:
    seclabel = self.parse_seclabel()
    # TODO: lvalue?
    name = self.parse_identifier()
    self.expect(':')
    type = self.parse_type()
    return EGlobal(name.span, type, seclabel, name, seclabel)

  def parse_globals(self):
    ins = []
    self.expect('in')
    self.expect('{')
    while not self.maybe('}'):
      ins.append(self.parse_global_variable())
      self.expect(';')
    self.expect('}')

    outs = []
    self.expect('out')
    self.expect('{')
    while not self.maybe('}'):
      outs.append(self.parse_global_variable())
      self.expect(';')
    self.expect('}')
    return (ins, outs)
