# impl_pml.py - Promella backend for running with SPIN
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

# my custom version ...
#
# what to export
# should make all state-methods private and export the machine code

from impl import *
from ssk1 import *
import re, string
import pdb

def stname(longname):
    return "ST_" + cname(longname)

def evname(longname):
    return "EV_" + cname(longname)

def signame(longname):
    return "SIG_" + cname(longname)

def expand_action(alist):
    return string.join(alist, "; ")
        
blnks = '                               ';

def inspc(level):
    return blnks[:3*level+3]

def dump_multiple(f1, stchlist):
    labels = ["none"]
    for stch in stchlist:
        for tran in stch.trans:
            if tran.label:
                if tran.label not in labels:
                    labels.append(tran.label)
    f1.write("mtype = { _NONE,")
    for l in labels: f1.write(" %s," % (l,))
    f1.write(" }\n")
    for stch in stchlist:
        impl = PmlImpl(stch)
        impl.dump_body(f1)

class PmlImpl(Impl):

    def __init__(self, mach, config=None):
        Impl.__init__(self, config)
        self.mach = mach

    def dump_spec(self, f1):
        # need to dump #defines for state, labels
        pass

    def dump_body(self, f1, mach=None):
        # Generate the implementation part (.c file) for the statechart.
        if not mach: mach = self.mach
        name = cname(mach.name)
        #pdb.set_trace()
        lvs = collect_leaves(mach)
        for l in lvs:
            f1.write("#define %-24s\t%d\n" % (l.name, l.id))
        f1.write("\n")
        #
        f1.write("active proctype %s_exec(chan %s)\n{\n" % (name,name))
        f1.write("   byte evt, st\n")
        f1.write("\n")
        init = gen_initial(mach)
        f1.write("   st = %d\n" % (init[0],))
        f1.write("   evt = NONE\n")
        f1.write("loop:\n")
        f1.write("   if\n")
        f1.write("   :: atomic { (evt == NONE) && nempty(%s) } -> %s?evt\n" %
                 (name,name))
        f1.write("   :: else\n")
        f1.write("   fi\n")
        # NEED TO DEAL WITH ORTHOGONAL STATES - THIS ONLY DOES ONE STATE !!!
        #f1.write("   st = mstC[0]\n")
        f1.write("   if\n")
        sl = collect_leaves(mach)
        for s in sl: self.state_body(f1, s)
        f1.write("   fi\n")
        f1.write("   goto loop\n")
        f1.write("}\n\n")

    def state_body(self, f1, state):
        # not set up for orthogonal regions yet
        region = state.region
        lev = state.level
        f1.write("   :: st == " + state.name + " ->\n")
        nd = "      "
        # NEEDS WORK: labeled vs. non-labeled AND leaf vs parents
        ot = collect_otrans(state) # does not get loop-transitions yet
        f1.write(nd+"if\n")
        for tl in ot:
            lab = None
            for t in tl:
                if t.label:
                    if t.guard:
                        f1.write(nd+":: (evt == %s) && (%s) ->\n" %
                                 (t.label,t.guard))
                    else:
                        f1.write(nd+":: evt == %s ->\n" % (t.label,))
                elif t.guard:
                    f1.write(nd+":: %s ->\n" % (t.guard,))
                else:
                    f1.write(nd+":: 1 ->\n")
                for a in t.actions:
                    f1.write(nd+"   %s\n" % (a,))
                if t.label: f1.write(nd+"   evt = NONE\n")
                f1.write(nd+"   st = %s\n" % (t.target.name,))
        f1.write(nd+"fi\n")
                    
   

# --- last line of impl_pml.py ---
