from pprint import pprint
from typing import NoReturn
from sys import exit
from .ast import Span, FAKE_SPAN

def color(s, c): return f'\033[1;{c}m{s}\033[0m'
def red(s): return color(s, 31)
def blue(s): return color(s, 34)
def purple(s): return color(s, 35)
def cyan(s): return color(s, 36)
def yellow(s): return color(s, 93)
def green(s): return color(s, 32)
def white(s): return color(s, 37)

def report(level: str, msg: str, span: Span, colorfn, preamble_lines: int = 2,
           epilogue: str|None = None, epilogue_pp = None):
  print(colorfn(f'{level}: ') + msg)
  if span is not FAKE_SPAN:
    lines = span.src.splitlines()
    lstart = max(span.lnum - preamble_lines, 0)
    lend = span.lnum
    # TODO: strip whitespace from the left of all lines, consistently
    # print preamble lines
    for i in range(lstart, lend):
      print(f'{i + 1:4} | ' + lines[i].replace('\t', '    '))

    cstart = span.cstart
    cend = span.cend

    # print marked line
    # NOTE: doing .replace on line here would mess up offsets
    line = lines[lend]
    before, highlighted, after = line[:cstart], line[cstart:cend], line[cend:]
    print(f'{lend + 1:4} | '
      + before.replace('\t', '    ')
      + colorfn(highlighted).replace('\t', '    ')
      + after.replace('\t', '    '))

    # print underline
    extra_spaces = len(before.replace('\t', '    ')) - len(before)
    print(' ' * 7 # padding for line numbers
      + colorfn('~' * (cstart + extra_spaces))
      + colorfn('^' * (cend - cstart)))

  if epilogue is not None:
    print(epilogue)
  if epilogue_pp is not None:
    pprint(epilogue_pp)

def report_error(msg: str, span: Span) -> NoReturn:
  report('error', msg, span, red)
  exit(1)

def report_error_cont(msg: str, span: Span):
  report('error', msg, span, red)

def report_security_error(msg: str, span: Span) -> NoReturn:
  report('security error', msg, span, purple)
  exit(1)

def report_security_error_cont(msg: str, span: Span):
  report('security error', msg, span, purple)

def report_note(msg: str, span: Span, **kwargs):
  report('note', msg, span, blue, **kwargs)

def report_debug(msg: str, span: Span,
                 epilogue: str|None = None, epilogue_pp = None):
  report('debug', msg, span, cyan,
    epilogue = epilogue, epilogue_pp = epilogue_pp)
