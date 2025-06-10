from lib.ast import *
from lib.utils import *
from lib.types import *
from traverse import *

@dataclass
class SecurityContext:
  ctxvar: dict[Symbol, SecLabel]
  ctxarr: dict[Symbol, list[SecLabel]]

  def copy(self) -> 'SecurityContext':
    return SecurityContext(self.ctxvar.copy(), self.ctxarr.copy())

  def label_of(self, sym: Symbol, default: SecLabel|None = None) -> SecLabel:
    if sym in self.ctxvar:
      return self.ctxvar[sym]
    elif sym in self.ctxarr:
      return SecLabel.LOW.join(*self.ctxarr[sym])
    elif default is not None:
      return default
    else:
      raise RuntimeError(sym)

  def label_of_var(self, sym: Symbol, default: SecLabel|None = None) -> SecLabel:
    if sym in self.ctxvar:
      return self.ctxvar[sym]
    elif default is not None:
      return default
    else:
      raise RuntimeError(sym)

  def register_var(self, sym: Symbol, seclabel: SecLabel):
    assert(sym not in self.ctxvar)
    self.ctxvar[sym] = seclabel

  def relabel_var(self, sym: Symbol, seclabel: SecLabel):
    if not sym in self.ctxvar:
      pprint(self)
    assert(sym in self.ctxvar)
    self.ctxvar[sym] = seclabel


  def register_array(self, sym: Symbol, seclabels: list[SecLabel]):
    assert(sym not in self.ctxarr)
    self.ctxarr[sym] = seclabels

  def register_array_basic(self, sym: Symbol, size: int, seclabel: SecLabel):
    assert(sym not in self.ctxarr)
    self.ctxarr[sym] = [seclabel] * size

  def label_of_array_index(self, sym: Symbol, idx: int) -> SecLabel:
    return self.ctxarr[sym][idx]

  def labels_of_array(self, sym: Symbol) -> list[SecLabel]:
    return self.ctxarr[sym][::]

  def relabel_array_index(self, sym: Symbol, idx: int, seclabel: SecLabel):
    self.ctxarr[sym][idx] = seclabel

  def relabel_array(self, sym: Symbol, seclabel: SecLabel):
    assert(sym in self.ctxarr)
    self.ctxarr[sym] = [seclabel] * len(self.ctxarr[sym])

  def merge(self, other: 'SecurityContext'):
    # merge variables
    for sym, seclabel in other.ctxvar.items():
      newlabel = seclabel.join(self.label_of_var(sym, SecLabel.LOW))
      self.relabel_var(sym, newlabel)
    # merge arrays
    for sym, seclabels in other.ctxarr.items():
      assert(sym in self.ctxarr)
      if sym in self.ctxarr:
        for idx, seclabel in enumerate(seclabels):
          nseclabel = seclabel.join(self.label_of_array_index(sym, idx))
          self.relabel_array_index(sym, idx, nseclabel)
      else:
        assert(False)
        self.regarr(sym)

def fold_fn_returns(acc: list[SecLabel], node: AstNode):
  match node:
    case SReturn(secure=sec):
      return acc + [sec]
    case _:
      return fold_tree(fold_fn_returns, acc, node)

def flow_analysis(node: AstNode, pc: SecLabel, ctx: SecurityContext):
  match node:
    case EId(span, type, _, name, sym):
      sec = ctx.label_of_var(sym, sym.secure)
      return EId(span, type, sec, name, sym)
    case EInt(span, type, _, value):
      return EInt(span, type, SecLabel.LOW, value)
    case EBool(span, type, _, value):
      return EBool(span, type, SecLabel.LOW, value)
    case EArray(expr=EId(sym=sym)):
      nnode = map_tree(flow_analysis, node, pc, ctx)
      # l_arr = join(l_index, l_arr)
      # TODO: make sure this makes sense
      nnode.secure = nnode.index.secure.join(ctx.label_of(sym))
      return nnode
    case EArrayLiteral(span, type, _, values):
      nvalues = [flow_analysis(val, pc, ctx) for val in values]
      return EArrayLiteral(span, type, SecLabel.LOW, nvalues)
    case EUnOp():
      nnode = map_tree(flow_analysis, node, pc, ctx)
      nnode.secure = nnode.expr.secure
      return nnode
    case EBinOp():
      nnode = map_tree(flow_analysis, node, pc, ctx)
      nnode.secure = nnode.lhs.secure.join(nnode.rhs.secure)
      return nnode
    case EDeclassify(span, type, _, expr):
      nexpr = flow_analysis(expr, pc, ctx)
      if nexpr.secure is not SecLabel.HIGH:
        report_security_error('can only declassify high information', span)
      return EDeclassify(span, type, SecLabel.LOW, nexpr)

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

      # this is guaranteed by type-checking
      assert(isinstance(name.sym.type, TFn))
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
      sec = SecLabel.LOW.join(*retseclabels)
      return ECall(span, type, sec, nname, nargs)

    case SScope():
      return map_tree(flow_analysis, node, pc, ctx)
    case SVarDef(span, EId(sym=sym) as lhs, rhs):
      # var def
      nrhs = flow_analysis(rhs, pc, ctx)
      # register security label for the symbol
      ctx.register_var(sym, nrhs.secure)
      # update lhs security label from the symbol
      nlhs = flow_analysis(lhs, pc, ctx)
      return SVarDef(span, nlhs, nrhs)
    case SVarDef(span, EArray() as lhs, rhs):
      # array def
      nrhs = flow_analysis(rhs, pc, ctx)
      match nrhs:
        case EArrayLiteral(values=values):
          seclabels = [v.secure for v in values][::]
        case EId(sym=rsym):
          seclabels = ctx.labels_of_array(rsym)
        case _:
          # should've been caught in type-checking
          raise RuntimeError()
      # register security labels for the array symbol
      ctx.register_array(lhs.expr.sym, seclabels)
      # update lhs security label from the symbol
      nlhs = flow_analysis(lhs, pc, ctx)
      return SVarDef(span, nlhs, nrhs)
    case SFnDef():
      # this will be processed manually on every ECall(...)
      return node
    case SAssign(span, EId(name=name, sym=Symbol(type=TArray()) as sym) as lhs, rhs):
      # x = ... where x is array
      oseclabels = ctx.labels_of_array(sym)
      nrhs = flow_analysis(rhs, pc, ctx)
      match nrhs:
        case EArrayLiteral(values=values):
          # x = [...]
          nseclabels = [val.secure for val in values][::]
        case EId(sym=rsym):
          # x = y
          # type-checking made sure y is an array
          nseclabels = ctx.labels_of_array(rsym)
        case _:
          raise RuntimeError(nrhs)
      for idx, (osec, nsec) in enumerate(zip(oseclabels, nseclabels)):
        if osec is not nsec:
          label = str(nsec)
          # TODO: this can get really verbose
          report_note(f'label of {blue(name)}[{blue(idx)}] set to {yellow(label)}', span,
            preamble_lines=0)
        ctx.relabel_array_index(sym, idx, nsec)
      nlhs = flow_analysis(lhs, pc, ctx)
      return SAssign(span, nlhs, nrhs)
    case SAssign(span, EId(name=name, sym=sym) as lhs, rhs):
      # x = ... where x is var
      origsec = ctx.label_of_var(sym, sym.secure)
      nrhs = flow_analysis(rhs, pc, ctx)
      # update variable's security label
      ctx.relabel_var(sym, pc.join(nrhs.secure))
      nlhs = flow_analysis(lhs, pc, ctx)
      if origsec is not ctx.label_of_var(sym):
        label = str(ctx.label_of_var(sym))
        report_note(f'label of {blue(name)} set to {yellow(label)}', span,
                    preamble_lines=0)
      return SAssign(span, nlhs, nrhs)
    case SAssign(span, EArray(expr=EId(name=name, sym=sym), index=EInt() as index) as lhs, rhs):
      # array[EInt()] = ...
      nrhs = flow_analysis(rhs, pc, ctx)
      oldsec = ctx.label_of_array_index(sym, index.value)
      if oldsec != nrhs.secure:
        label = str(nrhs.secure)
        report_note(f'label of {blue(name)}[{blue(index.value)}] set to {yellow(label)}', span,
          preamble_lines=0)
      ctx.relabel_array_index(sym, index.value, nrhs.secure)
      nlhs = flow_analysis(lhs, pc, ctx)
      return SAssign(span, nlhs, nrhs)
    case SAssign(span, EArray(expr=EId(name=name, sym=sym)) as lhs, rhs):
      # array[x] = ...
      nrhs = flow_analysis(rhs, pc, ctx)
      nlhs = flow_analysis(lhs, pc, ctx)
      newsec = nlhs.secure.join(nrhs.secure)
      if newsec is SecLabel.HIGH:
        # index is not statically known, hence mark whole array as high
        report_note(f'label of whole array {blue(name)} set to {yellow("high")}', span,
          preamble_lines=0)
        ctx.relabel_array(sym, SecLabel.HIGH)
      else:
        # cannot know which index becomes low, so err on the side of
        # caution and don't mark any as low
        pass
      return SAssign(span, nlhs, nrhs)
    case SIf(span, clause, body, els):
      nclause = flow_analysis(clause, pc, ctx)
      npc = pc.join(nclause.secure)
      els_ctx = ctx.copy()
      nbody = flow_analysis(body, npc, ctx)
      nels = flow_analysis(els, npc, els_ctx) if els else None
      # merge else branch into the original security context
      ctx.merge(els_ctx)
      return SIf(span, nclause, nbody, nels)
    case SWhile(span, clause, body):
      nclause = flow_analysis(clause, pc, ctx)
      npc = pc.join(nclause.secure)
      if npc is SecLabel.HIGH:
        # TODO: better error message if inside high if ()
        report_security_error('insecure implicit flow - while loop with a high guard', clause.span)
      nbody = flow_analysis(body, npc, ctx)
      nclause = flow_analysis(clause, pc, ctx)
      npc = pc.join(nclause.secure)
      if npc is SecLabel.HIGH:
        # TODO: better error message if inside high if ()
        report_security_error('insecure implicit flow - while loop with a high guard after iteration',
          clause.span)
      return SWhile(span, nclause, nbody)
    case SThrow(span):
      if pc is SecLabel.HIGH:
        report_security_error('throw in high context is not allowed', span)
      return SThrow(span)
    case SReturn(span, _, expr):
      nexpr = flow_analysis(expr, pc, ctx)
      return SReturn(span, pc.join(nexpr.secure), nexpr)
    case SGlobal(span, type, expr, origsec):
      match expr:
        case EId(sym=sym):
          ctx.register_var(sym, origsec)
        case EArray(expr=EId(sym=sym), index=EInt(value=size)):
          ctx.register_array_basic(sym, size, origsec)
        case _:
          report_error(f'unhandled lvalue in flow analysis', expr.span)
      nexpr = flow_analysis(expr, pc, ctx)
      return SGlobal(span, type, nexpr, origsec)
    case File() | STryCatch():
      return map_tree(flow_analysis, node, pc, ctx)
    case _:
      report_error('unhandled node in flow analysis', node.span)
