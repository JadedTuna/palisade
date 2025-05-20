from lib.ast import *
from lib.utils import report_error

PRECTABLE_ARITH      = 0
PRECTABLE_BITWISE    = 1
PRECTABLE_SHIFT      = 2
PRECTABLE_BOOLEAN    = 3
PRECTABLE_COMPARISON = 4

PRECTABLE_TYPE = {
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
UNOPS = [
  '-', '+', '!', '~',
]

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
      # raise RuntimeError(f'expected {s} but got {tok.type}')
      # exit(1)
    self.idx += 1
    return tok

  def maybe(self, *types) -> bool:
    return self.token().type in types

  def consume(self) -> Token:
    tok = self.token()
    self.idx += 1
    return tok

  def parse(self) -> File:
    stmts = []
    while not self.maybe('eof'):
      stmts.append(self.parse_stmt())

    return File(stmts)

  def check_precedence(self, prev_op, op) -> bool:
    if prev_op is None:
      return False

    prev_type, prev_prio = BINOPS[prev_op.type]
    type, prio = BINOPS[op.type]
    if prev_type == type:
      # same type of op
      return prev_prio >= prio
    elif (prev_type, type) in PRECTABLE_TYPE:
      # no ambiguity between op types
      return PRECTABLE_TYPE[(prev_type, type)]
    else:
      report_error('ambiguous precedence, use parenthesis', op.span)

  def parse_expr(self):
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
      expr = EBinOp(op.type, expr, rhs)

  def parse_term(self):
    if self.maybe('identifier'):
      return self.parse_identifier()
    elif self.maybe('integer', 'integer_hex'):
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
      return EUnOp(op.type, self.parse_term())
    else:
      report_error('unexpected token while parsing expression', self.token().span)
      # raise RuntimeError(self.token())

  def parse_identifier(self) -> EId:
    tok = self.expect('identifier')
    return EId(tok.value)

  def parse_integer(self) -> EInt:
    tok = self.expect('integer', 'integer_hex')
    if tok.type == 'integer_hex':
      return EInt(int(tok.value, 16))
    else:
      return EInt(int(tok.value))

  def parse_boolean(self) -> EBool:
    if self.maybe('true'):
      tok = self.expect('true')
    else:
      tok = self.expect('false')
    return EBool(tok.type == 'true')

  def parse_stmt(self) -> Stmt:
    if self.maybe('{'):
      return self.parse_scope()
    elif self.maybe('if'):
      return self.parse_if()
    elif self.maybe('while'):
      return self.parse_while()
    elif self.maybe('identifier'):
      # TODO: function calls
      # TODO: high/low
      return self.parse_assign()
    # TODO: skip
    else:
      report_error('unexpected token while parsing statement', self.token().span)
      # raise RuntimeError(self.token())

  def parse_scope(self) -> SScope:
    self.expect('{')
    stmts = []
    while not self.maybe('}'):
      stmts.append(self.parse_stmt())
    self.expect('}')

    return SScope(stmts)

  def parse_assign(self) -> SAssign:
    # identifier = expr ;
    lhs = self.parse_identifier()
    self.expect('=')
    rhs = self.parse_expr()
    self.expect(';')

    return SAssign(lhs, rhs)

  def parse_if(self) -> SIf:
    # if ( clause ) stmt [else stmt]
    self.expect('if')
    self.expect('(')
    clause = self.parse_expr()
    self.expect(')')

    body = self.parse_stmt()

    if self.maybe('else'):
      self.expect('else')
      else_stmt = self.parse_stmt()
    else:
      else_stmt = None

    return SIf(clause, body, else_stmt)

  def parse_while(self) -> SWhile:
    # while ( clause ) stmt
    self.expect('while')
    self.expect('(')
    clause = self.parse_expr()
    self.expect(')')

    body = self.parse_stmt()

    return SWhile(clause, body)
