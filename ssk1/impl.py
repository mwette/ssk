# impl.py - implementations (back end)
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

# Notes on implemenntations.
# We might want to wrap all actions as scheduled actions as in
# void foo(arg, t, sch) {
#   action_in_statechart(foo, etc)
# }
# Then we don't need to call these directly from the statemachine but
# can return a list of actions.
#
# idea (bad?): for inState() use a table that indexed by full state and
# provides bitmask for 

import re

def deepest_common_region(st1, st2):
    """
    Find parent region common to st1 and st2 that is deepest in the
    hierarchy.
    This is also called the least common ancestor (LCA) in UML2.  However,
    in UML2 the LCA can be a state if the transition crosses regions of an
    orthogonal state.  We don't allow transitions to cross regions, do we?
    """
    if st1.level > st2.level:
        while st1.level > st2.level:
            st1 = st1.parent.parent
    elif st2.level > st1.level:
        while st2.level > st1.level:
            st2 = st2.parent.parent
    reg1 = st1.parent; reg2 = st2.parent
    while reg1 != reg2:
        reg1 = reg2.parent.parent
        reg2 = reg2.parent.parent
    return reg1

def writedef(f1, name, val):
    tabs = '\t\t\t\t\t\t\t'
    # print in clean format
    l = len(name)
    nt = (32 - l - 1)/8
    f1.write("#define %s%s%s\n" % (name, tabs[:nt], str(val)))

class Impl:

    def __init__(self, config):
        self.config = config

    def dump_spec(self, f1):
        pass

    def dump_body(self, f1):
        pass

    def Xinterp_action(self, action):
        # interpret action
        # parse
        pass


def cname(longname):
    name = longname
    name = re.sub('\.', '_', name)
    name = re.sub('\[(\d)\]', '_\\1', name)
    return name


def lcname(longname):
    name = cname(longname)
    return name[:1].lower() + name[1:]


def name_genC(n0):
    "generate C codeable name"
    print "n0=", n0
    n1 = re.sub(' ', '_', n0)
    n2 = re.sub('-', '_', n1)
    return n2

def gen_trans_actions(src, tract, dst):
    # generate list of all actions to make state transition
    # src: source state
    # tract: list of actions for the transaction
    # dst: destination state
    r = deepest_common_region(src, dst)
    up = []
    while src.parent != r:
        up.append(src.a_ex)
        src = src.parent.parent
    up.append(src.a_ex)
    dn = []
    while dst.parent != r:
        dn.insert(0, dst.a_en)
        dst = dst.parent.parent
    dn.insert(0, dst.a_en)
    res = []; res.extend(up); res.extend(tract); res.extend(dn)
    return res

# === state encoding =======

def follow_trans(src, dst):
    xl = []; nl = []                    # eXit list, eNter list
    r = deepest_common_region(src, dst)
    while src.parent != r:
        # exit state
        xl.append((src.a_ex, src.parent.parent))
        src = src.parent.parent
    while dst.parent != r:
        nl.insert(0, (dst.a_en, dst))
        dst = dst.parent.parent

def gen_encoding(src, dst):
    """
    This routine computes the change in state encoding.  The first element is
    the offset; remaining elements are the values to be added.
    result = [offset, <id>, <id>, <id>, 0, 0, 0]
    I'm not sure this works with orthogonal regions.
    """
    # compute offset
    r = deepest_common_region(src, dst)
    code = [r.offset]                   # code change for dst state
    so = src.parent.offset              # src offset
    do = dst.parent.offset              # dst offset
    while dst.parent != r:
        code.insert(1, dst.index)
        dst = dst.parent.parent
    code.insert(1, dst.index)
    #print "so,do=", so, do
    while do < so:
        do = do + 1
        code.append(0)
    #print "res=", res
    #print ""
    return code

import pdb

def gen_initial(ss):
    #pdb.set_trace()
    def r_init(code, r):
        s0 = r.state[r.initial-1]
        if len(s0.region) == 0:
            code[r.offset] = s0.id
        else:
            s_init(code, s0)
    def s_init(code, s):
        for r in s.region:
            r_init(code, r)
    code = ss.nslot * [0]
    s_init(code, ss.root)
    return code

def collect_otrans(state):
    """
    Collect outgoing transitions from (leaf) state and all parents.
    The problem is how to collect these.
    This should return something like the following, where
    res = [[['labA',guard,actions,dst], ['labA',guard,actions,dst]],
           [['labA',guard,actions,dst], [guard,...]],
          ]
    """
    def cmp(a,b): 
        if a.label == None: return -1
        if a.label <= b.label: return 1
        return -1
    res = []
    while state.id != 0:
        res1 = []
        for t in state.otrans:
            res1.append(t)
        res1.sort(cmp)
        #print res1
        res.append(res1)
        state = state.parent.parent
    return res

def collect_leaves(mach):
    """
    This routine collects all leaf (aka simple) states.
    """
    def inR(region):
        l = []
        for s in region.state:
            if len(s.region) == 0:
                l.append(s)
            else:
                l.extend(inS(s))
        return l
    def inS(state):
        l = []
        for r in state.region:
            l.extend(inR(r))
        return l
    return inS(mach.root)

        
# --- last line of impl.py ---
