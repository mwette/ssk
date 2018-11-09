# sskP.py - ssk printers
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

class SskWriter:

    blnks = '                               '

    def istr(self, lev, isiz=2):
        "indent string"
        return self.blnks[:isiz*lev]

    def __init__(self, ss, *args):
        self.ss = ss

    def write(self):
        ss = self.ss
        self.write_header()
        if ss.root: self.write_state(ss.root, 1)
        for tran in ss.trans: self.w_trans(tran, 1)
        self.write_trailer()

    def write_state(self, state, il=0):
        self.w_state(state, il)
        for region in state.region:
            self.write_region(region, il+1)
        self.w_end_state(state, il)

    def write_region(self, region, il=0):
        self.w_region(region, il)
        for state in region.state:
            self.write_state(state, il+1)
        self.w_end_region(region, il)

    def write_header(self, il=0):
        self.w_header(il)

    def write_trailer(self, il=0):
        self.w_trailer(il)
        
    def w_state(self, state, il=0):
        pass

    def w_end_state(self, state, il=0):
        pass

    def w_region(self, region, il=0):
        pass

    def w_end_region(self, region, il=0):
        pass

    def w_trans(self, trans, il=0):
        pass

class SskTextWriter(SskWriter):

    def __init__(self, ss):
        self.ss = ss
        self.f1 = sys.stdout

    def w_header(self, il=0):
        ss = self.ss
        f1 = self.f1
        f1.write('Statechart:\n')
        f1.write('  .name: %s\n' % ss.name)

    def w_trailer(self, il=0):
        pass
        
    def w_state(self, state, il=0):
        s = self.istr(il)
        f1 = self.f1
        f1.write(s+ 'State:\n')
        f1.write(s+ '  .name: %s\n' % (state.name,))
        f1.write(s+ '  .id: %d\n' % (state.id,))
        f1.write(s+ '  .index: %d\n' % (state.index,))
        f1.write(s+ '  .a_en: %s\n' % (str(state.a_en),))
        f1.write(s+ '  .a_ex: %s\n' % (str(state.a_ex),))
        f1.write(s+ '  .a_do: %s\n' % (str(state.a_do),))

    def w_region(self, region, il=0):
        f1 = self.f1
        s = self.istr(il)
        f1.write(s+'Region:n')
        #write s+ '  .name:', region.name
        #write s+ '  .id:', region.id
        f1.write(s+'  .initial: %d\n' (region.initial,))
        f1.write(s+'  .offset: %d\n' (region.offset,))
        #write s+ '  .nslot:', region.nslot

    def w_trans(self, trans, il=0):
        f1 = self.f1
        s = self.istr(il)
        f1.write(s + "Transition:\n")
        if trans.source: f1.write(s+"  .src: %s\n"% (trans.source.name,))
        if trans.target: f1.write(s+"  .dst: %s\n" % (trans.target.name,))
        if trans.label: f1.write(s+"  .label: %s\n" % (trans.label,))
        if trans.guard: f1.write(s+"  .guard: %s\n" % (trans.guard,))
        for a in trans.actions: f1.write(s+"  .action: %s\n" % (a,))

class SskXmlWriter(SskWriter):

    def __init__(self, ss, f1):
        self.ss = ss
        self.f1 = f1

    def w_header(self, il=0):
        ss = self.ss
        f1 = self.f1
        b = ""
        f1.write(b+"<statechart>\n")
        f1.write(b+" <name>%s</name>\n" % (ss.name,))
        f1.write(b+" <nslot>%d</nslot>\n" % (ss.nslot,))
        f1.write(b+" <maxid>%d</maxid>\n" % (ss.maxid,))

    def w_trailer(self, il=0):
        f1 = self.f1
        b = ""
        f1.write(b+"</statechart>\n")
        
    def w_state(self, state, il=0):
        f1 = self.f1
        b = self.istr(il,1)
        f1.write(b+"<state>\n")
        f1.write(b+" <name>%s</name>\n" % (state.name,))
        f1.write(b+" <id>%d</id>\n" % (state.id,))
        f1.write(b+" <index>%d</index>\n" % (state.index,))
        f1.write(b+" <offset>%d</offset>\n" % (state.offset,))
        f1.write(b+" <nslot>%d</nslot>\n" % (state.nslot,))

    def w_end_state(self, state, il=0):
        f1 = self.f1
        b = self.istr(il,1)
        f1.write(b+"</state>\n")

    def w_region(self, region, il=0):
        f1 = self.f1
        b = self.istr(il,1)
        f1.write(b+"<region")
        if region.dhist is not None: f1.write(" dhist=\"%s\"" % region.dhist)
        if region.shist is not None: f1.write(" shist=\"%s\"" % region.shist)
        f1.write(">\n")
        #if region.name: f1.write(b+" <name>%s</name>\n" % (region.name,))
        #f1.write(b+" <id>%d</id>\n" % (region.id,))
        f1.write(b+" <initial>%d</initial>\n" % (region.initial,))
        f1.write(b+" <offset>%d</offset>\n" % (region.offset,))
        f1.write(b+" <nslot>%d</nslot>\n" % (region.nslot,))

    def w_end_region(self, region, il=0):
        f1 = self.f1
        b = self.istr(il,1)
        f1.write(b+"</region>\n")

    def w_trans(self, trans, il=0):
        f1 = self.f1
        b = self.istr(il,1)
        f1.write(b+"<transition>\n")
        if trans.source:
            f1.write(b+" <source>%d</source>\n" % (trans.source.id,))
        if trans.target:
            f1.write(b+" <target>%d</target>\n" % (trans.target.id,))
        if trans.label:
            f1.write(b+" <label>%s</label>\n" % (trans.label,))
        if trans.guard:
            f1.write(b+" <guard>%s</guard>\n" % (trans.guard,))
        for a in trans.actions:
            f1.write(b+" <action>%s</action>\n" % (a,))
        f1.write(b+"</transition>\n")


# --- last line of sskP.py ---
