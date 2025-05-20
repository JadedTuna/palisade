from pprint import pprint
from typing import NoReturn
from sys import exit

from .ast import Span

def color(s, c): return f'\033[1;{c}m{s}\033[0m'
def red(s): return color(s, 31)
def purple(s): return color(s, 35)
def cyan(s): return color(s, 36)
def yellow(s): return color(s, 93)

def report(level: str, msg: str, span: Span, colorfn, preamble_lines: int = 2,
           epilogue: str|None = None, epilogue_pp = None):
  lines = span.src.splitlines()
  lstart = max(span.lnum - preamble_lines, 1)
  lend = span.lnum

  print('\n' + colorfn(f'{level}: ') + msg)
  for i in range(lstart, lend):
    print(f'{i:4} | ' + lines[i])

  cstart = span.cstart
  cend = span.cend

  line = lines[lend]
  print(f'{lend:4} | ' + line[:cstart] + colorfn(line[cstart:cend]) + line[cend:])

  print('       ' + colorfn('~' * cstart) + colorfn('^' * (cend - cstart)))
  if epilogue is not None:
    print(epilogue)
  if epilogue_pp is not None:
    pprint(epilogue_pp)

def report_error(msg: str, span: Span):
  report('error', msg, span, red)
  exit(1)

def report_security_error(msg: str, span: Span):
  report('security error', msg, span, purple)
  exit(1)

def report_debug(msg: str, span: Span, epilogue: str|None = None, epilogue_pp = None):
  report('debug', msg, span, cyan,
    epilogue = epilogue, epilogue_pp = epilogue_pp)
