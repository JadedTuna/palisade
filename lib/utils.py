from typing import NoReturn
from sys import exit

from .ast import Span

def color(s, c): return f'\033[1;{c}m{s}\033[0m'
def red(s): return color(s, 31)
def yellow(s): return color(s, 93)

def report_error(msg, span: Span) -> NoReturn:
  PREAMBLE = 2
  lines = span.src.splitlines()
  lstart = max(span.lnum - PREAMBLE, 1)
  lend = span.lnum

  print()
  print(red('error: ') + msg)
  for i in range(lstart, lend):
    print(f'{i:4} | ' + lines[i])
  # print('\t' + '\n\t'.join(lines[lstart:lend]))

  cstart = span.cstart
  cend = span.cend

  line = lines[lend]
  print(f'{lend:4} | ' + line[:cstart] + red(line[cstart:cend]) + line[cend:])

  print('       ' + red('~' * cstart) + red('^' * (cend - cstart)))

  exit(1)
