from lib.ast import *
from lib.utils import *
from traverse import *

def resolve_seclabel(*labels: bool) -> bool:
  return any(labels)

@dataclass
class SecurityContext:
  ctxvar: dict[Symbol, bool]
  ctxarr: dict[Symbol, list[bool]]

  def copy(self) -> 'SecurityContext':
    return copy_dataclass(self)

  def label_of(self, sym: Symbol, default: bool|None = None) -> bool:
    if sym in self.ctxvar:
      return self.ctxvar[sym]
    elif sym in self.ctxarr:
      return HIGH if any(self.ctxarr[sym]) else LOW
    else:
      return default

  def label_of_var(self, sym: Symbol, default: bool|None = None) -> bool:
    return self.ctxvar.get(sym, default)

  def register_var(self, sym: Symbol, seclabel: bool):
    assert(sym not in self.ctxvar)
    self.ctxvar[sym] = seclabel

  def relabel_var(self, sym: Symbol, seclabel: bool):
    if not sym in self.ctxvar:
      pprint(self)
    assert(sym in self.ctxvar)
    self.ctxvar[sym] = seclabel


  def register_array(self, sym: Symbol, size: int, seclabel: bool):
    assert(sym not in self.ctxarr)
    self.ctxarr[sym] = [seclabel] * size

  def label_of_array_index(self, sym: Symbol, idx: int) -> bool:
    return self.ctxarr[sym][idx]

  def relabel_array_index(self, sym: Symbol, idx: int, seclabel: bool):
    self.ctxarr[sym][idx] = seclabel

  def relabel_array(self, sym: Symbol, seclabel: bool):
    assert(sym in self.ctxarr)
    self.ctxarr[sym] = [seclabel] * len(self.ctxarr[sym])

  def merge(self, other: 'SecurityContext'):
    # merge variables
    for sym, seclabel in other.ctxvar.items():
      newlabel = resolve_seclabel(self.label_of_var(sym, LOW), seclabel)
      self.relabel_var(sym, newlabel)
    # merge arrays
    for sym, seclabels in other.ctxarr.items():
      assert(sym in self.ctxarr)
      if sym in self.ctxarr:
        for idx, seclabel in enumerate(seclabels):
          nseclabel = resolve_seclabel(
            self.label_of_array_index(sym, idx),
            seclabel
          )
          self.relabel_array_index(sym, idx, nseclabel)
      else:
        self.regarr(sym)

def fold_fn_returns(acc: list[bool], node: AstNode):
  match node:
    case SReturn(secure=sec):
      return acc + [sec]
    case _:
      return fold_tree(fold_fn_returns, acc, node)

def flow_analysis(node: AstNode, pc: bool, ctx: SecurityContext):
  match node:
    case EId(span, type, _, name, sym):
      sec = ctx.label_of_var(sym, sym.secure)
      return EId(span, type, sec, name, sym)
    case EInt() | EBool():
      return map_tree(flow_analysis, node, pc, ctx)
    case EArray(expr=EId(sym=sym)):
      nnode = map_tree(flow_analysis, node, pc, ctx)
      # l_arr = join(l_index, l_arr)
      nnode.secure = HIGH if any((nnode.index.secure, ctx.label_of(sym))) else LOW
      return nnode
    case EUnOp():
      nnode = map_tree(flow_analysis, node, pc, ctx)
      nnode.secure = nnode.expr.secure
      return nnode
    case EBinOp():
      nnode = map_tree(flow_analysis, node, pc, ctx)
      nnode.secure = resolve_seclabel(nnode.lhs.secure, nnode.rhs.secure)
      return nnode
    case EDeclassify(span, type, _, expr):
      nexpr = flow_analysis(expr, pc, ctx)
      if nexpr.secure != HIGH:
        report_security_error('can only declassify high information')
      return EDeclassify(span, type, LOW, nexpr)

    # case SFnDef(span, params, retype, body):
    #   # create a new SecEnv for this
    #   fnctx = SecurityContext({}, {})
    #   for param in params:
    #     param.sym.
    case ECall(span, type, _, name, args):
      nname = flow_analysis(name, pc, ctx)
      nargs = []
      for arg in args:
        nargs.append(flow_analysis(arg, pc, ctx))

      sfndef = name.sym.type.sfndef
      # create a new SecEnv for this
      fnctx = SecurityContext({}, {})
      # register argument labels
      for param, narg in zip(sfndef.params, nargs):
        param.sym.secure = narg.secure
        fnctx.register_var(param.sym, narg.secure)
      # process body
      nbody = flow_analysis(sfndef.body, pc, fnctx)
      # figure out highest return security label
      retseclabels = fold_tree(fold_fn_returns, [], nbody)
      sec = resolve_seclabel(*retseclabels)
      return ECall(span, type, sec, nname, nargs)
    case SScope():
      return map_tree(flow_analysis, node, pc, ctx)
    case SVarDef(span, lhs, rhs):
      nrhs = flow_analysis(rhs, pc, ctx)
      # propagate security label to the symbol
      lhs.sym.secure = nrhs.secure
      # this will update lhs security label from the symbol
      nlhs = flow_analysis(lhs, pc, ctx)
      # TODO: handle arrays
      ctx.register_var(lhs.sym, nrhs.secure)
      return SVarDef(span, nlhs, nrhs)
    case SFnDef():
      # this will be processed manually on every ECall(...)
      return node
    case SAssign(span, EId(name=name, sym=sym) as lhs, rhs):
      origsec = ctx.label_of_var(sym, sym.secure)
      nrhs = flow_analysis(rhs, pc, ctx)
      # update variable's security label
      ctx.relabel_var(sym, resolve_seclabel(pc, nrhs.secure))
      nlhs = flow_analysis(lhs, pc, ctx)
      if origsec != ctx.label_of_var(sym):
        label = 'high' if ctx.label_of_var(sym) else 'low'
        report_note(f'label of {blue(name)} set to {yellow(label)}', span,
                    preamble_lines=0)
      return SAssign(span, nlhs, nrhs)
    case SAssign(span, EArray(expr=EId(name=name, sym=sym), index=EInt() as idx) as lhs, rhs):
      nrhs = flow_analysis(rhs, pc, ctx)
      oldsec = ctx.label_of_array_index(sym, idx.value)
      if oldsec != nrhs.secure:
        label = 'high' if nrhs.secure else 'low'
        report_note(f'label of {blue(name)}[{blue(idx.value)}] set to {yellow(label)}', span,
          preamble_lines=0)
      ctx.relabel_array_index(sym, idx.value, nrhs.secure)
      nlhs = flow_analysis(lhs, pc, ctx)
      return SAssign(span, nlhs, nrhs)
    case SAssign(span, EArray(expr=EId(name=name, sym=sym), index=idx) as lhs, rhs):
      nrhs = flow_analysis(rhs, pc, ctx)
      nlhs = flow_analysis(lhs, pc, ctx)
      newsec = HIGH if any((nlhs.secure, nrhs.secure)) else LOW
      if newsec == HIGH:
        # index is not statically known, hence mark whole array as high
        report_note(f'label of whole array {blue(name)} set to {yellow("high")}', span,
          preamble_lines=0)
        ctx.relabel_array(sym, HIGH)
      else:
        # cannot know which index becomes low, so err on the side of
        # caution and don't mark any as low
        pass

      return SAssign(span, nlhs, nrhs)
    case SIf(span, clause, body, els):
      nclause = flow_analysis(clause, pc, ctx)
      npc = resolve_seclabel(pc, nclause.secure)
      els_ctx = ctx.copy()
      nbody = flow_analysis(body, npc, ctx)
      nels = flow_analysis(els, npc, els_ctx) if els else None
      # merge else branch into the original security context
      ctx.merge(els_ctx)
      return SIf(span, nclause, nbody, nels)
    case SWhile(span, clause, body):
      nclause = flow_analysis(clause, pc, ctx)
      npc = resolve_seclabel(pc, nclause.secure)
      if npc == HIGH:
        # TODO: better error message if inside high if ()
        report_security_error('insecure implicit flow - while loop with a high guard', clause.span)
      nbody = flow_analysis(body, npc, ctx)
      nclause = flow_analysis(clause, pc, ctx)
      npc = resolve_seclabel(pc, nclause.secure)
      if npc == HIGH:
        # TODO: better error message if inside high if ()
        report_security_error('insecure implicit flow - while loop with a high guard after iteration',
          clause.span)
      return SWhile(span, nclause, nbody)
    case SThrow(span):
      if pc == HIGH:
        report_security_error('throw in high context is not allowed', span)
      return SThrow(span)
    case SReturn(span, _, expr):
      nexpr = flow_analysis(expr, pc, ctx)
      return SReturn(span, resolve_seclabel(pc, nexpr.secure), nexpr)
    case SGlobal(span, type, expr, origsec):
      match expr:
        case EId(sym=sym):
          ctx.register_var(sym, origsec)
        case EArray(expr=EId(sym=sym), index=EInt(value=size)):
          ctx.register_array(sym, size, origsec)
        case _:
          report_error(f'unhandled lvalue in flow analysis', expr.span)
      nexpr = flow_analysis(expr, pc, ctx)
      return SGlobal(span, type, nexpr, origsec)
    case File() | STryCatch():
      return map_tree(flow_analysis, node, pc, ctx)
    case _:
      report_error('unhandled node in flow analysis', node.span)
