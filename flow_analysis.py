from lib.ast import *
from lib.utils import *
from traverse import walk_tree, map_tree

def resolve_seclabel(*labels: list[bool]) -> bool:
  return any(labels)

def join_secmodtbls(tbl1: dict[Symbol, bool], tbl2: dict[Symbol, bool]):
  for key, value in tbl2.items():
    tbl1[key] = any((tbl1.get(key, LOW), value))

def flow_analysis(node: AstNode, pc: bool, secmodtbl: dict[Symbol, bool]):
  match node:
    case EId(span, type, _, name, sym):
      sec = secmodtbl.get(sym, sym.secure)
      return EId(span, type, sec, name, sym)
    case EInt() | EBool() | EGlobal():
      return map_tree(flow_analysis, node, pc, secmodtbl)
    case SScope() | SVarDef():
      return map_tree(flow_analysis, node, pc, secmodtbl)
    case SAssign(span, (EId(name=name, sym=sym) | EArray(expr=EId(name=name, sym=sym))) as lhs, rhs):
      origsec = sym.secure
      nrhs = flow_analysis(rhs, pc, secmodtbl)
      # TODO: for arrays, need to keep track which index
      # is tainted. In general, need to be more careful with
      # arrays
      # modify symbol table
      # sym.secure = resolve_seclabel(pc, nrhs.secure)
      secmodtbl[sym] = resolve_seclabel(pc, nrhs.secure)
      nlhs = flow_analysis(lhs, pc, secmodtbl)
      if origsec != secmodtbl[sym]:
        label = 'high' if secmodtbl[sym] else 'low'
        report_note(f'label of {blue(name)} set to {yellow(label)}', span,
                    preamble_lines=0)
      return SAssign(span, nlhs, nrhs)
    case SIf(span, clause, body, els):
      nclause = flow_analysis(clause, pc, secmodtbl)
      npc = resolve_seclabel(pc, nclause.secure)
      els_secmodtbl = secmodtbl.copy()
      nbody = flow_analysis(body, npc, secmodtbl)
      nels = flow_analysis(els, npc, els_secmodtbl) if els else None
      # merge else branch into the original secmodtbl
      join_secmodtbls(secmodtbl, els_secmodtbl)
      return SIf(span, nclause, nbody, nels)
    case SWhile(span, clause, body):
      nclause = flow_analysis(clause, pc, secmodtbl)
      npc = resolve_seclabel(pc, nclause.secure)
      if npc == HIGH:
        # TODO: better error message if inside high if ()
        report_error('insecure implicit flow - while loop with a high guard', clause.span)
      nbody = flow_analysis(body, npc, secmodtbl)
      nclause = flow_analysis(clause, pc, secmodtbl)
      npc = resolve_seclabel(pc, nclause.secure)
      if npc == HIGH:
        # TODO: better error message if inside high if ()
        report_error('insecure implicit flow - while loop with a high guard after iteration', clause.span)
      return SWhile(span, nclause, nbody)
    case File():
      return map_tree(flow_analysis, node, pc, secmodtbl)
    case _:
      report_error('unhandled node in flow analysis', node.span)
