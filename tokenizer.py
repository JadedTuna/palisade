import string
from lib.ast import Span, Token
from lib.utils import report_error

WHITESPACE = string.whitespace
DIGITS = string.digits
BINDIGITS = '01'
OCTDIGITS = '01234567'
HEXDIGITS = DIGITS + 'ABCDEF'
ID_START = string.ascii_letters + '_'
ID_BODY = ID_START + DIGITS
EASY_MAP = '+-*%^~()[]{}:;,'
KEYWORDS = [
  'if',
  'else',
  'while',
  'debug',
  'declassify',

  'try',
  'catch',
  'throw',

  'true',
  'false',

  'high',
  'low',
]

class Tokenizer:
  def __init__(self, src):
    self.src = src
    self.idx = 0
    self.state = 'default'
    self.tokens = []
    self.lnum = 0
    self.cnum = 0
    self.tok_start = 0
    self.tok_cstart = 0

  def getc(self) -> str|None:
    if self.idx < len(self.src):
      return self.src[self.idx]
    else:
      return None

  def value(self) -> str:
    return self.src[self.tok_start:self.idx]

  def advance(self):
    self.idx += 1
    self.cnum += 1

  def newline(self):
    self.advance()
    self.cnum = 0
    self.lnum += 1

  def token_start(self, state: str):
    self.tok_start = self.idx
    self.tok_cstart = self.cnum
    self.state = state

  def token_end(self, type: str|None = None) -> Token:
    if type is None:
      type = self.state
    span = Span(self.tok_start, self.idx, self.lnum, self.tok_cstart, self.cnum, self.src)
    token = Token(type, self.src[self.tok_start:self.idx], span)
    self.tokens.append(token)
    self.state = 'default'
    return token

  def token_onec(self, type):
    span = Span(self.idx, self.idx+1, self.lnum, self.cnum, self.cnum+1, self.src)
    token = Token(type, self.src[self.idx:self.idx+1], span)
    self.tokens.append(token)

  def tokenize(self):
    self.state = 'default'
    while (c := self.getc()) is not None:
      if self.state == 'default':
        if c == '\n':
          self.newline()
        elif c in WHITESPACE:
          self.advance()
        elif c in ID_START:
          self.token_start('identifier')
        elif c == '0':
          self.token_start('integer_0')
          # next character will determine type: 0x, 0o, 0b
          self.advance()
        elif c in DIGITS:
          self.token_start('integer')
        # single-char/dual-char operators
        elif c == '=':
          self.token_start('=')
          self.advance()
        elif c == '<':
          self.token_start('<')
          self.advance()
        elif c == '>':
          self.token_start('>')
          self.advance()
        elif c == '|':
          self.token_start('|')
          self.advance()
        elif c == '&':
          self.token_start('&')
          self.advance()
        elif c == '!':
          self.token_start('!')
          self.advance()
        elif c == '/':
          self.token_start('/')
          self.advance()
        # end single-char/dual-char operators
        elif c in EASY_MAP:
          self.token_onec(c)
          self.advance()
        else:
          raise RuntimeError(c)
      elif self.state == 'identifier':
        if c in ID_BODY:
          self.advance()
        else:
          if self.value() in KEYWORDS:
            self.token_end(self.value())
          else:
            self.token_end('identifier')
      # start integer handling
      elif self.state == 'integer_0':
        if c == 'x':
          self.state = 'integer_hex'
          self.advance()
        elif c == 'b':
          self.state = 'integer_bin'
          self.advance()
        elif c == 'o':
          self.state = 'integer_oct'
          self.advance()
        elif c in DIGITS:
          tok = self.token_end()
          report_error('leading zeroes with no prefix are not allowed,' +
            ' use 0o for octal', tok.span)
        else:
          # just a single zero
          self.token_end('integer')
      elif self.state == 'integer_hex':
        if c in HEXDIGITS:
          self.advance()
        elif self.value() == '0x':
          tok = self.token_end()
          report_error('empty hex literal', tok.span)
        else:
          self.token_end()
      elif self.state == 'integer_bin':
        if c in BINDIGITS:
          self.advance()
        elif self.value() == '0b':
          tok = self.token_end()
          report_error('empty binary literal', tok.span)
        else:
          self.token_end()
      elif self.state == 'integer_oct':
        if c in OCTDIGITS:
          self.advance()
        elif self.value() == '0o':
          tok = self.token_end()
          report_error('empty octal literal', tok.span)
        else:
          self.token_end()
      elif self.state == 'integer':
        if c in DIGITS:
          self.advance()
        else:
          self.token_end()
      # end integer handling
      # start single-char/dual-char operators
      elif self.state == '=':
        if c == '=':
          self.advance()
          self.token_end('==')
        else:
          self.token_end('=')
      elif self.state == '<':
        if c == '<':
          self.advance()
          self.token_end('<<')
        elif c == '=':
          self.advance()
          self.token_end('<=')
        else:
          self.token_end('<')
      elif self.state == '>':
        if c == '>':
          self.advance()
          self.token_end('>>')
        elif c == '=':
          self.advance()
          self.token_end('>=')
        else:
          self.token_end('>')
      elif self.state == '|':
        if c == '|':
          self.advance()
          self.token_end('||')
        else:
          self.token_end('|')
      elif self.state == '&':
        if c == '&':
          self.advance()
          self.token_end('&&')
        else:
          self.token_end('&')
      elif self.state == '!':
        if c == '=':
          self.advance()
          self.token_end('!=')
        else:
          self.token_end('!')
      elif self.state == '/':
        if c == '/':
          # comment
          self.state = 'comment'
          self.advance()
        else:
          self.token_end('/')
      # end single-char/dual-char operators
      elif self.state == 'comment':
        # keep skipping until newline
        if c == '\n':
          self.state = 'default'
        else:
          self.advance()
      else:
        raise RuntimeError(self.state)
