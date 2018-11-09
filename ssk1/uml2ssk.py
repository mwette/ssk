# uml2ssk.py - convert uml2 to simple statechart
#
# Copyright (C) 2005-2013,2018 Matthew R. Wette
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

import sys
import pdb                              # debugging
import ssk1
import uml2

# Variables beginning in "u" are UML constructs.
# Variables beginning in "x" are translated constructs (in ssk).

# \todo
# * internal transitions (e[g]/a)

# Notes:
#    1. a model can contain several state machines and signals

# Todos:
#    1. we need to expand substatemachines
#    2. check for normal transition notation (guard etc)

# for debugging - so we only print warning once
nskip_Signal = 0
nskip_Enumeration = 0
nskip_TimeEvent = 0

def msgF(msg):
    print "*** uml2ssk: " + msg

def msgW(msg):
    print "+++ uml2ssk: " + msg

def msgI(msg):
    return None
    print "--- uml2ssk: " + msg


# in transition effects, we only allow these:
ssk_allowed_effects = ( uml2.OpaqueBehavior, uml2.FunctionBehavior)
allow_activity = True

class UMLtranslator:

    def __init__(self):
        #self.stc = ssk1.StateChart()    # statechart
        self.model = None
        self.stmd = {}                  # dict of state machines in UML model
        # for converting state machine
        self.reset()

    def reset(self):
        self.stc = None                 # current statechart
        self.sdict = {}			# ustate -> xstate dictionary
        self.rdict = {}                 # uregion -> xregion dictionary
        self.trans = []                 # transitions (first u, then x?)
        self.inits = []                 # initial states

    # --- user routines ---
    def set_model(self, u_model):
         # UML/XMI says 1 model per file (but file also has extensions)
        self.model = u_model
        self.find_all_stms()

    def find_stm(self, stmname):
        return self.find_stm_in_pkg(stmname, self.model)
        #return self.stmd.get(stmname, None)

    def find_all_stms(self):
        self.stmd = {}
        return self.find_stms_in_pkg(self.model)

    def translate_stm(self, ustm):
        #self.xl_Model(self.model)
        self.xl_StateMachine(ustm)

    # --- internal routines ---
    def find_stm_in_pkg(self, stmname, pkg):
        for elt in pkg.packagedElement:
            eclass = elt.__class__
            if eclass == uml2.StateMachine:
                if elt.name == stmname: return elt
            elif eclass == uml2.Package:
                stm = self.find_stm_in_pkg(stmname, elt)
                if stm: return stm
        for p in pkg.nestedPackage:
            stm = self.find_stm_in_pkg(stmname, p)
            if stm: return stm
        return None

    def find_stms_in_pkg(self, pkg):
        for elt in pkg.packagedElement:
            if elt.__class__ == uml2.StateMachine:
                if self.stmd.has_key(elt.name): raise Exception
                self.stmd[elt.name] = elt
        for p in pkg.nestedPackage:
            self.find_stms_in_pkg(p)

    def infuse_substatemachine(self, ustate):
        # should be called "expand_substatemachine"
        # maybe set up a map of connection points to new statemachine entries
        submach = ustate.submachine
        print "infuse_ssm: ", submach.name
        print "st.conn:", ustate.connection
        print "st.cpts:", ustate.connectionPoint
        print "st.incm:", ustate.incoming
        print "st.outg:", ustate.outgoing
        print ""
        # For each entry:
        # 1. If there is no connection point then entry is to initial state.
        #    Check to make sure there is a default.
        # 2. If there is a connection point, then name consistency matters.
        # For each exit:
        # 1. If there is no connection point then exit is from final state.
        #
        # generate replacement state
        

    def xl_Model(self, umodel):
        # Model is package plus visibility
        self.xl_Package(umodel)

    def xl_Package(self, upackage):
        global nskip_Signal, nskip_Enumeration, nskip_TimeEvent
        # translate Package: nestedPackage[], packagedElement[], ...
        # to start, just try packagedElements ...
        for pkg in upackage.nestedPackage:
            self.xl_Package(pkg)
        for elt in upackage.packagedElement:
            elt_class = elt.__class__
            if elt_class == uml2.StateMachine:
                self.xl_StateMachine(elt)
            elif elt_class == uml2.Signal:
                # element which is referenced in machine
                nskip_Signal += 1
                if nskip_Signal == 1:
                    print " --- uml2ssk: skipping Signal"
            elif elt_class == uml2.Enumeration:
                # element which is referenced in machine
                nskip_Enumeration += 1
                if nskip_Enumeration == 1:
                    print " --- uml2ssk: skipping Enumeration"
            elif elt_class == uml2.TimeEvent:
                # element which is referenced in machine
                nskip_TimeEvent += 1
                if nskip_TimeEvent == 1:
                    print " --- uml2ssk: skipping timeevent"
            else:
                msgF("unhandled class:" + str(elt_class))
                raise Exception
        
    def xl_StateMachine(self, umach):
        msgI("processing state machine: " + umach.name)
        stc = ssk1.StateChart()
        self.stc = stc
        xstate = ssk1.State()		# add root state
        xstate.index = 0
        stc.root = xstate
        #xstate.level 
        if umach.name:
            stc.name = umach.name
            xstate.name = stc.name
            xstate.fullname = xstate.name
        for uregion in umach.region:
            #print "uregion:", uregion
            self.xl_Region(uregion, xstate)
        # Translate transitions. (TBD)
        for utrans in self.trans:
            #print "utrans:", utrans
            self.xl_Transition(utrans)

    def xl_Region(self, uregion, xparent):
        " uml.region, ssk.parent"
        xregion = ssk1.Region(xparent)
        init_defined = False
        self.rdict[uregion] = xregion
        xparent.region.append(xregion)
        xregion.index = len(xparent.region) - 1
        xregion.name = '_' + str(xregion.index)
        xregion.fullname = xparent.fullname + '.' + xregion.name
        for uvertex in uregion.subvertex:
            #print "processing uvertex", uvertex.__class__
            if isinstance(uvertex, uml2.FinalState):
                msgF("region %s has FinalState" % (xregion.name))
                raise Exception
            elif isinstance(uvertex, uml2.State):
                self.xl_State(uvertex, xregion)
            elif isinstance(uvertex, uml2.Pseudostate):
                if uvertex.kind == 'initial':
                    # need to cache initial
                    self.inits.append(uvertex)
                    init_defined = True
                elif uvertex.kind == 'deepHistory':
                    # add to region dhist list
                    self.xl_Pseudostate(uvertex, xregion)
                else:
                    msgF("unhandled PseudoState kind:" + uvertex.kind)
                    #pdb.set_trace()
                    #raise Exception
                    continue
            else:
                print " --- region has " + uvertex.kind + " Pseudostate"
        for utrans in uregion.transition:
            # Don't process transitions until after all states done
            self.trans.append(utrans)
        # check
        if not init_defined:
            msgF("initial state not defined in region %s" \
                 % (xregion.fullname,))

    def xl_Pseudostate(self, upseudo, xparent):
        stc = self.stc
        xstate = ssk1.State(xparent)
        xparent.state.append(xstate)
        xstate.index = len(xparent.state) - 1
        if upseudo.name != None:
            xstate.name = ustate.name
        elif upseudo.kind == 'deepHistory':
            xstate.name = '_DH_' # deep history
        elif upseudo.kind == 'shallowHistory':
            xstate.name = '_SH_' # shallow history
        else:
            xstate.name = '_' + str(xstate.index)
        xstate.fullname = xparent.fullname + '.' + xstate.name
        self.sdict[upseudo] = xstate
        if upseudo.kind == 'deepHistory':
            xparent.dhist = xstate.index
        elif upseudo.kind == 'deepHistory':
            xparent.shist = xstate.index
        else:
            msgF("unhandled pseudostate: " + upseudo.kind)
            raise Exception
            
    def xl_State(self, ustate, xparent):
        " uml.state, ssk.parent (region)"
        stc = self.stc
        xstate = ssk1.State(xparent)
        xparent.state.append(xstate)
        xstate.index = len(xparent.state) - 1
        if ustate.name != None:
            xstate.name = ustate.name
        else:
            xstate.name = '_' + str(xstate.index)
        xstate.fullname = xparent.fullname + '.' + xstate.name
        self.sdict[ustate] = xstate
        if ustate.isSimple:
            #print "simple state"
            pass
        elif ustate.isOrthogonal:
            # need isOrthongonal before isComposite
            #print "orthog"
            for reg in ustate.region:
                self.xl_Region(reg, xstate)
        elif ustate.isComposite:
            #print "composite"
            self.xl_Region(ustate.region[0], xstate)
        elif ustate.isSubmachineState:
            #print "substatemachine"
            self.infuse_substatemachine(ustate)
            #raise Exception, "*** uml2ssk: can't handle SubmachineState (yet)"
        else:
            msgF("coding error")
            raise Exception
        if ustate.stateInvariant:
            # we can ignore this for now
            #raise Exception, ustate.stateInvariant
            #print ' --- state: invariant'
            pass
        if ustate.entry:
            #print ' --- state: entry'
            pass
        if ustate.exit:
            #print ' --- state: exit'
            pass
        if ustate.doActivity:
            msgF("HANDLE DO_ACTIVITY")
            raise Exception

    def xl_Transition(self, utrans):
        """
        This is done after all regions,states have been processed.
        ISSUES:
        If we have a transition from an orthogonal state then we (may) need
        to generate a pseudostate to handle the exit cleanly.
        """
        # Make sure that transitions don't have double-triggers (prefix-closed).
        stc = self.stc                  # SSC statechart
        sdict= self.sdict               # ustate->xstate dictionary
        # Find target.  First, because if initial trans, need to know where.
        if not utrans.target:
            msgF("trans has no target")
            raise Exception
        if not sdict.has_key(utrans.target):
            print utrans.target
            pdb.set_trace()
            msgF("trans target not found")
            raise Exception
        if isinstance(utrans.target, uml2.Pseudostate):
            if utrans.target.kind not in ('deepHistory', 'shallowHistory'):
                msgF("target is unsupported Pseudostate")
                raise Exception
        uregion = utrans.target.container
        xregion = self.rdict[uregion]
        xtarget = sdict[utrans.target]
        # Find source.
        if not utrans.source:
            msgF("trans has no source")
            raise Exception
        if isinstance(utrans.source, uml2.Pseudostate):
            if utrans.source.kind == 'initial':
                # add this initial state to the region
                if xregion.initial != 0:
                    msgF("initial state already defined")
                    raise Exception
                # region initial state is index of target 
                xregion.initial = xtarget.index
                # Make sure we don't have an associated activity.
                if len(utrans.trigger) > 0:
                    msgF("initial transition has trigger")
                    raise Exception
            else:
                msgF("unhandled source Pseudostate")
                raise Exception
        else:
            if not sdict.has_key(utrans.source):
                msgF("trans source not found")
                raise Exception
            xsource = sdict[utrans.source]
            #print "xsource=", xsource, "  xtarget=", xtarget
            label = None
            guard = None
            action = None
            if len(utrans.trigger) > 1:
                msgF("multiple triggers on transition")
                raise Exception
            elif len(utrans.trigger) == 1:
                utrig = utrans.trigger[0]
                #print "have Trigger:", utrig.event
                event = utrig.event
                if isinstance(event, uml2.SignalEvent):
                    #pdb.set_trace()
                    label = event.signal.name
                    #print " label =", label
                elif isinstance(event, TimeEvent):
                    msgW("TimeEvent may need more work")
                    label = "(TimeEvent: %s)" % (event.when)
                else:
                    msgW("unknown trigger" + str(utrig.event))
                    raise Exception
            if utrans.guard:
                uguard = utrans.guard
                if isinstance(uguard, str):
                    msgW("guard is string?")
                    guard = uguard
                elif isinstance(uguard, uml2.Constraint):
                    # use spec body else name
                    if uguard.name:
                        msgI("guard.name=" + str(uguard.name))
                        guard = guard.name
                    if uguard.specification:
                        spec = uguard.specification
                        if isinstance(spec, uml2.OpaqueExpression):
                            if len(spec.body) != 1:
                                raise Exception, "OpaqueExpr. w/o body"
                            # array is used to express in many languages
                            guard = spec.body[0]
            if utrans.effect:
                # ssk will use if OpagueB', use name, if FtnB', use body
                #pdb.set_trace()
                # check effect:
                if allow_activity and isinstance(utrans.effect, uml2.Activity):
                    action = utrans.effect.name
                elif not isinstance(utrans.effect, ssk_allowed_effects):
                    print "+++ illegal effect type:", utrans.effect
                    print "    allowed types: OpaqueBehavior, FunctionBehavior"
                    print "    using name:", utrans.effect.name
                    # HACK: name is action
                    action = utrans.effect.name
                elif utrans.effect.body:
                    action = utrans.effect.body
                else:
                    # HACK: name is action
                    action = utrans.effect.name
            #
            xtrans = ssk1.Transition()
            stc.trans.append(xtrans)
            xtrans.source = xsource
            xtrans.target = xtarget
            xtrans.label = label
            xtrans.guard = guard
            if action: xtrans.actions = [action]



from impl_c2 import C2Impl
from impl_pml import PmlImpl

def uml_to_ssk(model, machname):
    # Given UML model, statemach name, and diagram-flag return  (ssk,diag|None).
    
    xl = UMLtranslator()
    xl.set_model(model)
    ustm = xl.find_stm(machname)
    if ustm == None: 
        print '*** uml_to_ssk: statemachine not found:', machname
        print xl.stmd.keys()
        raise Exception, "statemachine not found"
    #
    xl.translate_stm(ustm)
    #
    stc = xl.stc                        # ssk statechart
    #az = ssk1.analyze_chart(stc)
    #
    if False:
        f1 = open("demo.xml", 'w')
        stc.print2(f1)
        f1.close()
    #
    if False:
        f1 = open("demo.c", 'w')
        impl = C2Impl(stc)
        impl.bodycode(f1)
        f1.close()
    #
    if False:
        az.flatten()
        f1 = open("demoF.xml", "w")
        stc.print2(f1)
        f1.close()
    #
    if False:
        f1 = open("demoF.c", 'w')
        impl = C2Impl(stc)
        impl.bodycode(f1)
        f1.close()
    #
    return xl.stc


# --- last line of uml2ssk.py ---
