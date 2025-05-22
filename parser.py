from lib.ast import *
from lib.types import TUnresolved
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
    while not self.maybe('eof'):
      stmts.append(self.parse_stmt())
    return File(FAKE_SPAN, stmts, SymTab(None, {}))

  def parse_expr(self):
    if(self.maybe('declassify')):
      return self.parse_declassify()
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
      return self.parse_identifier()
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

  def parse_stmt(self) -> Stmt:
    if self.maybe('{'):
      return self.parse_scope()
    elif self.maybe('if'):
      return self.parse_if()
    elif self.maybe('while'):
      return self.parse_while()
    elif self.maybe('high', 'low'):
      return self.parse_vardef()
    elif self.maybe('debug'):
      return self.parse_debug()
    elif self.maybe('identifier'):
      return self.parse_assign()
    # TODO: function calls
    # TODO: skip
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
    # identifier = expr;
    lhs = self.parse_identifier()
    tok = self.expect('=')
    rhs = self.parse_expr()
    self.expect(';')
    return SAssign(tok.span, lhs, rhs)

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

  def parse_vardef(self) -> SVarDef:
    # (high|low) identifier = expr ;
    sectok = self.expect('high', 'low')
    secure = sectok.type == 'high'
    lhs = self.parse_identifier()
    tok = self.expect('=')
    rhs = self.parse_expr()
    self.expect(';')
    return SVarDef(tok.span, secure, lhs, rhs)
