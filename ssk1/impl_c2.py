# impl_c2.py - C code backend
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

# what to export
# should make all state-methods private and export the machine code

from impl import *
from ssk1 import *
import re, string

def stname(longname):
    #return cname(longname) + "St"
    return "ST_" + cname(longname)

def evname(longname):
    #return cname(longname) + "Ev"
    return "EV_" + cname(longname)

def signame(longname):
    return "SIG_" + cname(longname)

def expand_action(alist):
    #return "send(\"" + text + "\")"
    print alist
    return string.join(alist, "; ")
        
blnks = '                               ';

def inspc(level):
    return blnks[:2*level+2]

default_config = {
    'event_type': 'evt_t'
    }


class C2Impl(Impl):

    def __init__(self, mach, config=default_config):
        Impl.__init__(self, config)
        self.mach = mach
        self.initvals = [0]*mach.root.nslot

    def speccode1s(self, f1, state=None):
        if not state: state = self.mach.root
        for r in state.region:
            self.speccode1r(f1, r)

    def speccode1r(self, f1, region):
        for s in region.state:
            # changed from s.offset to s.id
            #f1.write("#define %s\t\t%d\n" % (stname(s.name), s.id))
            writedef(f1, stname(s.name), s.id)
        for s in region.state:
            if len(s.region) > 0: self.speccode1s(f1, s)

    def dump_spec(self, f1, pmach=None):
        #
        f1.write("/*<subsigs>\n")
        for sig in self.mach.subsigs:
            f1.write(" <sig>%s</sig>\n" % (sig))
            f1.write("</subsigs>\n")
            f1.write("<pubsigs>\n")
            for sig in self.mach.pubsigs:
                f1.write(" <sig>%s</sig>\n" % (sig))
                f1.write("</pubsigs> */\n\n")
        self.speccode1(f1, pmach)
        name = cname(pmach.region.longname)
        f1.write("void %s__init();\n" % (name))
        f1.write("void %s__exec(int *mach_state, int sig);\n" % (name))
        #f1.write("void %s__fini();\n" % (name))
        f1.write("\n")

    def state_body(self, f1, state):
        region = state.region
        lev = state.level
        nd = inspc(lev)
        if len(region) > 0:
            for region in state.region:
                self.region_body(f1, region)
        else:
            if state.otrans:
                f1.write(nd+"switch (evt) {\n")
                for t in state.otrans:
                    # ERROR!!!  There may also be transitions from all parent 
                    # (composite) states !!!
                    f1.write(nd+"case %s:\n" % (t.label))
                    src = state
                    dst = t.target
                    #f1.write(nd+"  /* %d -> %d */\n" % (src.id, dst.id))
                    f1.write(nd+"  /* %s -> %s */\n" % (src.name, dst.name))
                    al = gen_trans_actions(src, t.actions, dst)
                    for a in al:
                        if a: f1.write(nd+"  %s;\n" % (a))
                    code = gen_encoding(src, dst)
                    ix = code.pop(0)
                    for x in code:
                        f1.write(nd+"  mst_next[%d] = %d;\n" % (ix, x))
                        ix = ix + 1
                    f1.write(nd+"  break;\n")
                f1.write(nd+"}\n")
                f1.write(nd+"/* selfloop internal transitions not done */")

    def region_body(self, f1, region):
        lev = region.parent.level
        nd = inspc(lev)
        #
        offset = region.offset
        f1.write(nd+"/* state %s, region %s */\n" % \
                 (region.parent.name, region.name))
        f1.write(nd+"switch (mst_curr[%d]) {\n" % (offset,))
        for state in region.state:
            f1.write(nd+"case %s:\n" % (stname(state.name)))
            self.state_body(f1, state)
            f1.write(nd+"  break;\n")
        f1.write(nd+"}\n")

    def state_init(self, f1, state):
        # fill in body of init routine
        for region in state.region:
            self.region_init(f1, region)

    def region_init(self, f1, region):
        # fill in body of init routine
        if False:
            f1.write("  mst_next[%d] = %d;\n" % \
                     (region.offset, region.initial))
        if True:
            self.initvals[region.offset] = region.initial
        for state in region.state:
            self.state_init(f1, state)

    def dump_body(self, f1, mach=None):
        # Generate the implementation part (.c file) for the statechart.
        if not mach: mach = self.mach
        name = cname(mach.name)
        et = self.config['event_type']
        #
        self.speccode1s(f1)
        #
        #f1.write("#define MACH_SIZE %d\n\n" % (mach.root.nslot))
        writedef(f1, "MACH_SIZE", mach.root.nslot)
        #
        # init
        if False:
            f1.write("void\n%s_init(char *mst)\n{\n" % (name))
        self.state_init(f1, mach.root)
        if False:
            f1.write("}\n\n")
        if True:
            f1.write("static int mst_default[] = { " + \
                     string.join(map(str, self.initvals), ", ") + " };\n\n")
            f1.write("void\n%s_init(char *mst)\n{\n" % (name))
            f1.write("  memcpy(mst, mst_default, sizeof(mst_default));\n")
            f1.write("}\n\n")
        #
        f1.write("void\n%s_exec(char *mst_curr, %s evt, char *mst_next)\n{\n" \
                 % (name, et))
        f1.write("  /* TODO: code to eval all conditions for curr state */\n")
        f1.write("  \n\n")
        self.state_body(f1, mach.root)
        f1.write("  \n\n")
        #f1.write("  mst = mst_next;\n");
        f1.write("}\n\n")
   

# --- last line of impl_c2.py ---
