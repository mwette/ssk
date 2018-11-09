# uanlyz.py - analysis and instrumentation of uml2 tree for a uml2.Model
#
# Copyright 2005-2013,2018 Matthew R Wette
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the licence with this software.
# If not, see <http://www.gnu.org/licenses/>.

# In order to store the state we will need to assess the maxium possible
# number of concurrent regions executing and the state storage needed
# for history states.

# todo:
# * add anonynous name for unnamed states
# * (maybe) add production of flattened state machine
#   we already have longnames for states.  We need to get all transitions
#   exiting the state by setting up a set of outgoing transitions and marching 
#   up the tree ...
# * collect transitions at the top -- these can be scattered everywhere
# * check Namespaces.ownedMember in Package, Region, State
# * for each state, if exiting transition has "after" then add enter action
#   to arm a timer
# done:
# * collect signal names at the top --

# notes:
# * instead of adding attributes in uml2.py we could generate for each
#   uml2 class a proxy class here (e.g. see VRegion below).  Then have
#   the proxy have reference to the proxy and also have a dictionary of
#   proxy's, keyed by uml2 instance reference.
#    pstate = PState()
#    pstate.ustate = state
#    udict[state] = pstate

# We should also compute the number of bits needed to compute the
# state and provide margins for expansion.

# # bits for symbolic event names

from uml2 import *
import re

# ===== add more information to base UML2 structure ==========================

#  1. add index for each state in a container
#  X. for each composite state, add number of bits needed to encode
#     this composite state (shallow and/or deep?)
#  X. for each composite state, add number of bytes needed to encode
#     this composite state (shallow and/or deep?)
#  X. for each composite state, add max number of concurrent regions

# xtra rules: (rules needed for generating code)
#  X. Composite states need to have a name.

# notes:
#  X. Need to provide context for error messages.
#  X. in each region, number of bytes to encode is 1 plus
#     max number for all composite states
#  X. in each composite state, number of bytes to encode is
#     sum over all regions

from math import log

def add_element(l,e):
  """ Add element to set (list)
  """
  if e not in l: l.append(e)

def bits_for_int(n):
  """ Computes number of bits to hold integer in range 0..n-1
  """
  return int(log(2*n-1)/log(2))


def nbyt_for_region(region):
  """ This routine finds the maximum number of bytes to encode the region.
      It assumes that the number of top-level vertices (states) in each
      region is less than 256.
  """
  mr = 1				# to handle states within this region
  if len(region.subvertex) > 255:
    raise Exception, "too many states to encode in 1 byte"
  ms = 0
  for vertex in region.subvertex:	# max over all states in the region
    if vertex.__class__ != State: continue
    state = vertex
    ms1 = 0
    if state.isComposite:
      ms1 = 0
      for reg in state.region:		# loop over all regions in state
        ms1 = ms1 + nbyt_for_region(reg)
    ms = max(ms, ms1)
  mr = mr + ms
  region.nbyte = mr
  return mr


def nbit_for_region(region):
  """ This routine finds the maximum number of bits to encode the region.
  """
  mr = bits_for_int(len(region.subvertex)) # for states within this region
  ms = 0
  for vertex in region.subvertex:	# max over all states in the region
    if vertex.__class__ != State: continue
    state = vertex
    ms1 = 0
    if state.isComposite:
      for reg in state.region:		# loop over all regions in state
        ms1 = ms1 + nbit_for_region(reg)
    ms = max(ms, ms1)
  mr = mr + ms
  region.nbit = mr
  #print "region", region.longname, " .nbit=", mr
  return mr


def max_concur_region(region):
  """ This routine finds the maximum number of current regions that
      can be executing under the region given by the argument.  This
      looks all the way down.
  """
  mc = 1
  for vertex in region.subvertex:	# max over all states in the region
    ms = 1
    if vertex.__class__ != State: continue
    state = vertex
    if state.isComposite:
      ms = 0
      name = state.name or "-"
      n = 0
      for reg in state.region:		# loop over all regions in state
        mc1 = max_concur_region(reg)
        ms = ms + mc1
        n += 1
    mc = max(mc,ms)
  return mc


def nstate_in_region(region):
  """ This routine returns the number of states in the region.
  """
  return len(region.subvertex)


def least_common_ancestor(reg1, reg2):
  """ Find parent region common to reg1 and reg2 that is deepest in the
      hierarchy.
  """
  # This does not handle statemachine!  Should we use region?
  if reg1.level > reg2.level:
    while reg1.level > reg2.level:
      if not reg1.state: raise Exception, "expecting parent state"
      reg1 = reg1.state.container
  elif reg2.level > reg1.level:
    while reg2.level > reg1.level:
      if not reg2.state: raise Exception, "expecting parent state"
      reg2 = reg2.state.container
  while reg1.state != reg2.state:
    reg1 = reg1.state.container
    reg2 = reg2.state.container
  if reg1 != reg2:
    # this could be orthogonal regions
    raise Exception, "uanlyz.least_common_region: yikes!"
  return reg1


# =============================================================================

# \fix: make sure can handle state machine w/ multiple regions (at top)
# ProxyMach is attached to relevant uml2.Region in StateMachine.
# number_states_in_regaion first then pick off number of states and
# look through to get states[] array
# * question is whether we include composite states in our enumerations
# note: state numbering starts at 1.  0 is interpreted as "inactive"

class ProxyMach:
  """ This is a mechanism for handling orthogonal regions as proxy state
      machines.
  """
  def __init__(self, region):
    self.region = region                # Region: associated uml2 region
    self.ostate = []                    # State: list of contained ortho states
    self.oproxy = []                    # ProxyMach: proxy's for o-states
    self.states = [None]		# State: array of states
    self.nstate = 1			# int: number of states
    self.level = 0			# int: level in heirarchy top=0
    self.offset = 0			# int: state offset
    self.maxortho = 0			# int: maximum number of otho regions
    # others to add: maxShallowId, maxDepth so we can encode as byte array

  def search(self, region=None):
    # The search is breadth-first for simple states and depth first for
    # compound states.  Can't handle submachine states yet.
    if not region: region = self.region
    shallowId = 1
    deepId = region.baseId
    # Number simple states at this level.
    for vertex in region.subvertex:
      if not isinstance(vertex, State): continue
      state = vertex
      if not state.isSimple: continue
      #print "shal:", state.longname
      #
      region.numShallowStates += 1
      shallowId += 1
      state.shallowId = shallowId
      deepId += 1
      state.deepId = deepId
      if self.nstate != deepId: raise Exception
      self.states.append(state)
      self.nstate += 1
    #
    # Descend into each non-orthogonal composite state and number.
    self.maxortho = 0
    for vertex in region.subvertex:
      if not isinstance(vertex, State): continue
      state = vertex
      if not state.isComposite: continue
      #
      # composite states count as states
      region.numShallowStates += 1
      shallowId += 1
      state.shallowId = shallowId
      deepId += 1
      vertex.deepId = deepId
      if self.nstate != deepId: raise Exception
      self.states.append(state)
      self.nstate += 1
      #
      #print "deep:", state.longname
      if state.isOrthogonal:
        # Generate a proxy machine for each region.
        plist = []
        northo = 0
        for reg in state.region:
          #print "mach:", reg
          proxy = ProxyMach(reg)
          proxy.level = self.level + 1
          proxy.search()
          northo += proxy.maxortho
          plist.append(proxy)
        self.ostate.append(state)
        self.oproxy.append(plist)
        self.maxortho = max(self.maxortho, northo)
      else:
        # Descend into state and number.
        state.region[0].baseId = deepId
        self.search(state.region[0])
    #self.printx()

  def size_state(self):
    offset = 1
    for proxl in self.oproxy:
      for proxy in proxl:
        proxy.offset = self.offset + offset
        offset += 1 + proxy.maxortho
        proxy.size_state()

  def printx(self):
    print "self=", self
    print "region=", self.region
    print "nstate=", self.nstate - 1
    #print "states=", map(lambda s: s.longname, self.states[1:])
    print "states=", map(lambda s: s.name, self.states[1:])
    print "ostate=", self.ostate
    print ""

# =============================================================================

class ModelAnalyzer:
  """ This should evolve to something that can do analysis of a set of
      UML (and possibly other) models.
  """

  def __init__(self):
    self.models = []
    self.sigs = []
    self.curstm = None			# current state machine

  def add_uml_model(self, model):
    self.models.append(model)

  def analyze(self):
    model = self.models[0]
    for member in model.ownedMember:
      #print "ownedMember is ", member.name
      if member.__class__ == StateMachine:
        self.a_mach(member)
      else:
        #print "got member", member
        pass

  def check_stm_ownedMembers(self, namespace):
    # this is called on Regions and States within a Statemachine
    stm = self.curstm
    for member in namespace:
      if member.__class__ == Signal:
        if member.name: stm.allsig.append(member.name)
      elif member.__class__ == SignalEvent:
        pass
      elif member.__class__ == TimedEvent:
        pass
      else:
        pass

  def a_mach(self, mach):
    self.curstm = mach
    if mach.name:
      print " --- a_mach: name=", mach.name
      mach.longname = mach.name
    if len(mach.region) > 1:
      raise Exception, "can't handle multiple statemachine regions"
    ix = 1
    for region in mach.region:
      #print "max concur region=", max_concur_region(region)
      #print "nstate in region=", nstate_in_region(region)
      region.index = ix			# index in container state|statemachine
      self.a_region(region)
      nbit = nbit_for_region(region)
      nbyt = nbyt_for_region(region)
      #print "region needs", nbit, "bits  or", nbyt, "bytes"
      ix += 1
    # generate a ProxyMach tree for othogonal regions
    if 1:
      #print "len region=", len(mach.region)
      #print "top region=", mach.region[0]
      mach.proxy = ProxyMach(mach.region[0])
      mach.proxy.search()
      mach.proxy.size_state()
    from sets import Set
    subset = Set(mach.subsigs)
    pubset = Set(mach.pubsigs)
    extset = subset - pubset
    #print "subsigs:", mach.subsigs
    #print "pubsigs:", mach.pubsigs
    #print "extset=", extset

  def a_region(self, region):
    """ Analyze a region.
        1. A region can have at most one initial vertex
        2. A region can have at most one deep history vertex
        3. A region can have at most one shallow history vertex
        4. A region can be owned by a State or StateMachine but not both.
    """
    if region.state:			# parent is State
      #print "region.state"
      region.longname = region.state.longname
      if region.state.isOrthogonal:
         region.longname += '[' + str(region.index) + ']'
      region.level = region.state.level
    elif region.statemachine:		# parent is Statemachine
      #print "region.statemachine"
      region.longname = region.statemachine.name
      region.level = 0
    else:				# parent not defined
      raise Exception, " *** a_region: parent not defined"
    #print "region.longname=", region.longname
    # A region consists of a set of subvertices (class Vertex).
    # A vertex can be one of : State, Finalstate, Pseudostate
    for vertex in region.subvertex:
      if isinstance(vertex, State):
        self.a_state(vertex)
      elif type(vertex) == FinalState:
        print " --- a_region: has FinalState "
        pass
      elif isinstance(vertex, Pseudostate):
        #print " --- a_region: has (" + vertex.kind + ") Pseudostate"
        pass
    for trans in region.transition:
      self.a_transition(trans)
      # If region contains transition from initial state tag target as init
      if trans.source:
        if isinstance(trans.source, Pseudostate):
          if trans.source.kind == 'initial':
             region.initstate = trans.target
             #print "init-state is", trans.target.longname
    for member in region.ownedMember:
      # StateMachine, Signal, SignalEvent, TimeEvent, Package
      if member.__class__ == __Signal__:
        pass

  def a_state(self, state):
    """ Analyze a (composite) state
    """
    if state.isSimple:
      preg = state.container		# parent region
      #print "preg.longname=", preg.longname, "state.name=", state.name
      if not state.name:
        print " +++ a_state: simple state has no name" # could be FinalState?
        state.name = 'UNKNOWN'
      state.longname = preg.longname + '.' + state.name
      #print " --- a_state: [simp] " + state.longname
    elif state.isComposite:
      if state.isOrthogonal:
        #print " --- a_state: composite/orthogonal"
        pass
      else:
        #print " --- a_state: composite"
        pass
      if state.name == None:
        print " *** a_state: composite state has no name"
        state.name = 'UNKNOWN'
      preg = state.container		# parent region
      state.longname = preg.longname + '.' + state.name
      #print " --- a_state: [comp] " + state.longname,"nreg=",len(state.region)
    elif state.isSubmachineState:
      print " *** a_state: can't handle submachine states yet"
    else:
      print " *** a_state: undefined type", state
    state.level = state.container.level + 1
    # sanity checks
    if state.isOrthogonal and not state.isComposite:
      print " *** a_state: orthogonal but not composite"
    # process transitions
    for trans in state.outgoing: pass
    for trans in state.incoming: pass
    if state.isComposite:
      if not state.isOrthogonal and len(state.region) > 1: raise Exception
      ix = 1
      for region in state.region:
        region.index = ix
        self.a_region(region)
        ix += 1

  def a_transition(self, trans):
    # todo: check for non-determinism
    stm = self.curstm
    #print "transition ..."
    if not trans.source: raise Exception, " *** trans has no source!"
    if not trans.target: raise Exception, " *** trans has no target!"
    if isinstance(trans.source, Pseudostate):
      snam = '[' + trans.source.kind + ']'
    else:
      snam = trans.source.name
    if isinstance(trans.target, Pseudostate):
      tnam = '[' + trans.target.kind + ']'
    elif isinstance(trans.target, FinalState):
      tnam = 'FINI'
    else:
      tnam = trans.target.name
    tsig = ""				# transition signature
    for trig in trans.trigger:
      event = trig.event
      if event.__class__ == SignalEvent:
        #print " --- trig.event is SignalEvent, signal=", event.signal
        signame = event.signal.name
        add_element(stm.subsigs, signame)
        tsig += signame
      elif event.__class__ == TimeEvent:
        #print " --- trig.event is TimeEvent"
        pass
    if trans.guard:
      tsig += '[' + trans.guard + ']'
    if trans.effect:
      # something to parse for publish messages
      tsig += '/' + trans.effect
      stmts = trans.effect.split(';')
      for stmt in stmts:
        # need to parse here to find sig
        signame = trans.effect		# \fix HACK
        add_element(stm.pubsigs, signame)
    #print " --- trans: %s -| %s |-> %s" % (snam, tsig, tnam)


# === validate ========================

# need to compbine this with ModelAnalyzer in uanlyz.py !!!

# This is for validation / syntax checking (/ semantic checking?).
# This could be a huge job on its own.  What do we want to validate:
# 1. Each region must have an initial state or an entry point.
#    (connection point for submachine or external transtition for xxx)
# 2. Termination syntax/semantics.  This could be tough to check.
#    a. region may have final state
#    b. region may have exit transition
#    c. exit from one region of orthongonal state => all exit ?
#    d. exit from parent region (or state?)
# 3. If statemachine is used as submachine, then:
#    a. if no initial state, then entry connection point
#    b. if no final state, then exit connection point (from each orthongonal)
# 4. Make sure elements in statemachine show up in the diagram.  It is possible
#    to have a state w/ transitions to other states and it doesn't show up in
#    the diagram.  This happened with state that was removed.
# 5. If a single trigger generates multiple signal events, warning?
#    (signals could be going to different objects)  Idea is that we should
#    not generate ambigous string (..,a,b,..) or (..,b,a,..)
# 6. Transition from initial state should have no trigger

# Sublanguage Constraint possibilities:
# 1. if transitions use choice points
# 2. Deep/Shallow histories?
# 3. Terminate?
# 4. transition effects?
#    a. only use simple stuff, 
#    b. use std convention for generating signal emit(GO_HOME)
# 5. state names are AbcDef style
# 6. signal names are CAPS_AND_UNDERSCORES



# Notes:
# 1. Maybe this should be a validator for a set of models.  So we can put in
#    the xxx.

def v_eror(self, msg):
    print " *** " + msg

def v_warn(self, msg):
    print " +++ " + msg

def v_info(self, msg):
    print " --- " + msg


# The V-classes are to hold state to validate the UML models.
class VStateMachine:
    def __init__(self, ustatemachine):
        self.ustatemachine = ustatemachine

class VRegion:
    def __init__(self, uregion):
        self.uregion = uregion
        self.has_exit = False           # ?

class VState:
    def __init__(self, ustate):
        self.ustate = ustate


class ModelValidator:
    """
    UML ModelValidator.
    The methods here are not reentrant.  That is, you can't instantiate one
    validator and call from different threads.
    """

    def __init__(self):
        # no params/options yet -- should get lots if we define sublanguage
        self.statemachine_d = {}
        self.region_d = {}
        self.state_d = {}
        self.transition_d = {}

    def validate_model(self, model):
        self.model = model              # current model
        self.val_Package(model)

    def val_Package(self, package):
        self.pkg = package              # current package
        for pkg in package.nestedPackage:
            self.val_Package(pkg)
        for elt in package.packagedElement:
            elt_class = elt.__class__
            if elt_class == StateMachine:
                self.val_StateMachine(elt)

    def val_StateMachine(self, stm):
        self.stm = stm                  # current statemachine
        vstm = VStateMachine(stm)
        self.statemachine_d[stm] = vstm
        self.vstm = vstm
        self.reg = None
        self.stv = None
        for reg in stm.region:
            self.val_Region(reg)
        for elt in stm.submachineState:
            pass
        self.stm = None

    def val_Region(self, region):
        # UML 2.4 region constraints:
        # 1. at most one initial vertex
        # 2. at most one deep history vertex
        # 3. at most one shallow history vertex
        self.reg = region               # current region
        vreg = VRegion(region)
        self.region_d[region] = vreg
        if region.statemachiene:
            pass
        nvinit = 0                      # num initial vertices
        nvfini = 0                      # num final vertices
        nvntry = 0                      # num entry pseudostates
        nvexit = 0                      # num exit pseudostates
        nvdeep = 0                      # num deep history
        nvshal = 0                      # num shallow history
        nvterm = 0                      # num termination pseudostates
        nxntry = 0                      # num external entries
        nxexit = 0                      # num external exits
        for vtx in region.subvertex:
            vtx_class = vtx.__class__
            if vtx_class == Pseudostate:
                if vtx.kind == 'initial': nvinit += 1
                elif vtx.kind == 'deepHistory': nvdeep += 1
                elif vtx.kind == 'shallowHistory': nvshal += 1
                elif vtx.kind == 'deepHistory': nvdeep += 1
                elif vtx.kind == 'join': pass
                elif vtx.kind == 'fork': pass
                elif vtx.kind == 'junction': pass
                elif vtx.kind == 'choice': pass
                elif vtx.kind == 'entryPoint': nvntry += 1
                elif vtx.kind == 'exitPoint': nvexit += 1
                elif vtx.kind == 'terminate': nvfini += 1
                else: raise Exception, "pseudostate must have kind"
            elif vtx_class == ConnectionPointReference:
                print "connection point reference"
            elif vtx_class == FinalState:
                pass
            elif vtx_class == State:
                self.val_State(vtx)
        # process transitions
        for trn in region.transition:
            self.val_Transition(trn)
        # check 
        if nvinit == 0 and nxntry == 0:
            print "region does not have legit start"

    def val_State(self, state):
        self.stv = state                # current state vertex
        name = "(noname)"
        if vtx.name == None or len(vtx.name) == 0:
            pname = "(unknown)"
            if vtx.container:
                reg = vtx.container
                if reg.state:
                    pname = reg.state.name
                else:
                    pname = reg.statemachine.name
            v_warn("state, in '%s', has no name" % (pname,))
        else:
            # check name for legit convention
            name = vtx.name
        if vtx.isSubmachineState:
            v_info("state '%s' references submachine" % (name,))
        elif vtx.isSimple:
            pass

    def _region_has_exit(self, region):
        # I think this is the wrong way to do it.  We need state info to 
        # track exits as we descend down the tree.
        for trn in region.transition:
            pass
        for vtx in region.subvertex:
            vtx_class = vtx.__class__
            if vtx_class == Pseudostate:
                if vtx.kind == 'terminate':
                    return True
            elif vtx_class == 'FinalState':
                return True
            elif vtx_class == 'State':
                if vtx.isSubStatemachine:
                    # ugh
                    pass
                elif vtx.isOrthogonal:
                    pass
                elif vtx.isComposite:
                    pass
                else:
                    # isSimple
                    pass

    def val_Transition(self, trn):
        # parent name
        if self.stv:
            pname = self.reg.state.name   # parent name is state name
        else:
            pname = self.reg.statemachine.name # parent name is machine name
        # kind
        if trn.kind == 'internal':
            pass
        elif trn.kind == 'external':
            pass
        elif trn.kind == 'local':
            pass
        else:
            raise Exception, "must have legit kind"
        # source, target kind, name
        src = trn.source
        tgt = trn.target
        sname = '(none)'
        tname = '(none)'
        if src.__class__ == Pseudostate:
            skind = src.kind
            sname = skind
            #if src.kind == 'junction': print ' source is junction'
        elif src.__class__ == State:
            skind = self._skind(src)
            sname = src.name
        else:
            raise Exception
        if tgt.__class__ == Pseudostate:
            tkind = tgt.kind
            tname = tkind
        elif tgt.__class__ == State:
            tkind = self._skind(tgt)
            tname = tgt.name
            #if tgt.kind == 'junction': print ' target is junction'
        else:
            raise Exception
        v_info("trans: %s(%s) -> %s(%s)" % (sname,skind,tname,tkind))
        # triggers
        for trg in trn.trigger:
            if trg.event == None:
                v_warn("trigger w/ no event: " + str(trg))
                continue
            # This should be SignalEvent or TimeEvent
            evt_class = trg.event.__class__
            if evt_class not in (SignalEvent, TimeEvent):
                v_warn(" trigger in '%s' not SignalEvent,TimeEvent" %
                           (pname,))
            if evt_class == SignalEvent:
                v_info(" trigger-event,signal: %s" % (trg.event.signal,))
            elif evt_class == TimeEvent:
                v_info(" trigger-event,timeev: %s" % ("(uml2.TBD)",))
            else:
                v_warn(" trigger-event,???, class: %s" % (evt_class,))
        if trn.guard:
            self.val_Constraint(trn.guard)
        if trn.effect:
            v_info(" effect: %s" % (trn.effect,))

    def _skind(self, state):
        if state.isOrthogonal: return 'ortho'
        if state.isComposite: return 'compo'
        if state.isSimple: return 'simple'
        if state.isSubmachineState: return 'submach'
        raise Exception, "must be BUG in mdreader"

    def val_Event(self, evt):
        # validate event ... valid?
        # SignalEvent: evt.signal = string
        # TimeEvent: tbd
        # ChangeEvent: when ...
        # AnyReceiveEvent ?
        # CallEvent ?
        # how is "else" handled?
        pass

    def val_Constraint(self, con):
        ce = con.constrainedElement      # don't care
        cx = con.context                 # don't care?
        spec = con.specification         # the meat
        spec_class = spec.__class__
        if spec_class == OpaqueExpression:
            if len(spec.body) > 1:
                v_warn("constraint in multiple languages")
            if len(spec.body) == 0:
                v_warn("constraint w/ no meat in spec")
            v_info("constraint spec body: '%s'" % (spec.body[0],))



# --- last line of uanlyz.py ---
