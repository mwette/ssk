# mdreader.py - parse MagicDraw xml file and generate uml2 tree
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

# todo:
# 1. remove env
# 2. get location information available to all

# That is, this file implements xml.sax parser classes to parse an XML file and
# builds up a UML instance (from classes defined in uml2.py) representing the
# model(s) contained in the document.  Each class here has a "val" member that
# will be assigned to something from uml2.py.  XMI reference id numbers are 
# recorded as the document is read.  After the document has been completely 
# read the refernces by XMI id are replaced by the object (references).
# obj1 = new uml2.Object(id='_123'), xmidict['_123'] = obj1
# obj2 = new uml2.Object(id='_456'), xmidict['_456'] = obj2
# obj2.source = '_123'
# ... document read complete, now dereference ...
# obj2.source = xmidict['_123']
# In some cases we replace uml objects with strings.

# We might want to change the way this works because xml sections are more
# based on entity names rather than entity types.  That is, if system fills in
# object of type Foo named bar1 bar2, then the xml file has <bar1> ...
# and <bar2> ...  We should have a class Foo which parses both.

# Each "init" should generate a val which is external class.

# When we find a member in a xml stream that will reference an external class
# and our current context ref's an external class, then within begEltIn():
#   if tag == "child":
#      el = Child()
#      self.val.child.append(el.val)

import sys
import re
#import traceback
import pdb


debug1 = False
pinfo = False
pwarn = False

# ===== light-weight SAX handler for XMI/XML documents ========================

# \todo REWORD THIS 
# Currently this is combined with XMI file handler.  Right now it seems
# simpler to just combine these.  The idea is to write handlers which
# live at the node of a parse tree and see all branches being generated.
# If there is structure in the parse tree that needs to be dealt with
# (e.g., "a + b" versus "a - b") then the begEltIn needs to work with that.
# That is, a local parse state should be developed...

import xml.sax

# global things each LtWtHdlr needs:
# - place to put stuff (ownedMembers)
# - xmidict

# "env" is carried around as a global dictionary.  The idea is that after
# the tree is generated env from the top node has any global info that is
# desired.  (I am trying to eliminate env. -- Matt)

# XMI documents use references (given as attributes).   This parser
# tracks these references and provides an opportunity to trace through
# the references once the file has been read.  The method deref() can
# be redefined by any node.  This node should always call deref_kids()
# after all local references have been dealt with.

# When the sax document handler parses a xml element with "xmi:id" tag
# it adds the element to the xmi dictionary.

# xmidict is a dictionary with keys being XMI ID's (unicode) and values
# being class instances from uml2.py. 

# UML values must be instantiated in constructors.  For example, this works:
#   el = Constraint(self, tag, attrs)
#   self.val.stateInvariant = el.val

class LtWtHdlr:
    """This class implements a light-weight handler for parsing XML files.
       There is a slight non-symmetry between begEltIn and endEltIn: for a
       LtWtHdlr for <xyz>...</xyz> begEltIn(...,'xyz') will be called in the
       parent, but endEltIn(...,'xyz') will be called in the xyz LtWtHdlr.
       If endEltIn sees it's own tag it should return the parent ("return
       self.parent").
       Element passes environment .env to children.
    """
    tag = 'LtWtHdlr'

    def __init__(self, parent, tag, attrs):
        self.parent = parent
        self.children = []
        self.tag = tag
        self.data = ""
        if parent:
            parent.children.append(self)
        #    self.env = parent.env
        #else:
        #    self.env = {}
        self.val = None			# value

    def begEltIn(self, tag, attrs):
        return None

    def endEltIn(self, tag):
        if tag == self.tag:
            return self.parent		# virtual pop
        else:
            return self

    def charsIn(self, data):
        #self.data += data
        self.data += str(data)  # convert to ascii -- OK?


class XmiElement(LtWtHdlr):
    """
    The XMI dictionary uses XMI tags with unicode strings (as returned
    by the SAX parser).  Strategy: put potential xmi:idrefs in the handler
    instance (i.e., if attrs has source='_123456' then self.source=xxx)
    otherwise stuff information in the vals right away.
    Check: Does xmi element need to have a xmi:id and/or xmi:type?
    """
    tag = 'xmi:Element'

    def __init__(self, parent, tag, attrs):
        LtWtHdlr.__init__(self, parent, tag, attrs)
        if not parent:
            self.xmidict = {}
        else:
            self.xmidict = parent.xmidict

    def xmi_insert_val(self, name):
        if self.xmidict.has_key(name): raise Exception
        self.xmidict[name] = self.val
        if 0: print "xmidict: add key", name

    def xmi_lookup(self, name):
        if self.xmidict.has_key(name):
            return self.xmidict[name]
        else:
            raise Exception

    def deref_kids(self):
        for c in self.children:
            c.deref()

    def deref(self):
        self.deref_kids()

# ... don't really know if this handle for extension is useful ...
extensions = []                         # list of extension classes

def add_extension(extension):
    extensions.append(extension)

class XmiExtension(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)

    def begEltIn(self, tag, attrs):
        el = None
        for ext in extensions:
            if tag == ext.tag:
                el = ext(self, attrs)
        return el


class SkipElement(XmiElement):
    """
    Special handler to skip a tree.
    """
    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.tag = tag

    def begEltIn(self, tag, attrs):
        if tag == self.tag:
            return SkipElement(self, tag, attrs)
        else:
            return None

    def endEltIn(self, tag):
        if tag == self.tag:
            return self.parent
        else:
            return self

# handler has:
#  locator.getLineNumber()
#  locator.getPublicId() 

class XmiDocumentHandler(xml.sax.ContentHandler):
    istr = "." * 60

    def __init__(self, handler):
        # \fix: The need to have LtWtHandler keep track of the handler and also
        # provide something to pass back is a bit of a mess. 
        hdlr = handler                  # XmiElement(LtWtHdlr)
        self.hdlr = hdlr
        self.hchk = hdlr                # check (assert) at end
        #self.env = hdlr.env			# need something to pass back
        self.lvl = 0
        #

    def startElement(self, tag, attrs):
        if debug1: print self.istr[:self.lvl] + "<" + tag
        self.lvl += 1
        #print "%5d hdlr.tag=%s"%(self._locator.getLineNumber(),self.hdlr.tag)
        el = self.hdlr.begEltIn(tag, attrs)
        #try:
        #    el = self.hdlr.begEltIn(tag, attrs)
        #except Exception, e:
        #    print "*** exception: line ", self._locator.getLineNumber()
        #    #traceback.print_stack(None, 3)
        #    #sys.exit(1)
        #    raise e
        if el:
            if 0: print 'got elt:', el, '@', self._locator.getLineNumber()
            # if begEltIn returns an element, then register in xmi dict.
            self.hdlr = el			# new level so new handler
            if attrs.has_key('xmi:id'):
                id = attrs['xmi:id']
                el.xmi_insert_val(id)
                el.xmiId = id			# used for backtracing errors

    def endElement(self, tag):
        if debug1: print self.istr[:self.lvl] + tag + ">"
        self.lvl -= 1
        self.hdlr = self.hdlr.endEltIn(tag)
        if not self.hdlr:
            raise Exception, "no handler from %s at %d" \
		    % (tag, self._locator.getLineNumber())

    def characters(self, data):
        self.hdlr.charsIn(data)
    
    def endDocument(self):
        if pinfo: print "--- mdreader: found document end"
        # contract: at endDocument, handler should be top-level one
        hdlr = self.hdlr
        if hdlr != self.hchk: raise Exception, "unbalanced parse"
        hdlr.endEltIn(hdlr.tag)
        hdlr.deref()
        del self.hdlr
        del self.hchk

    def iprint(self, str):
        print self.istr[:self.lvl] + str


# =============================================================================

import uml2
import mdext


def msgF(msg):
    print '*** mdreader: ' + msg

def msgW(msg):
    print '+++ mdreader: ' + msg

def msgI(msg):
    print '--- mdreader: ' + msg

# Each time an element is detected in the begEltIn method, we may 
# push the element onto the parser stack.  Then el.val should point
# to a UML2 structure appropriate for the element.

#   val - associated UML2 class instance (from uml2.py)

class Behavior(XmiElement):
    """
    Hoping this works ...
    """

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        xtype = self.type = attrs['xmi:type']
        if xtype == 'uml:FunctionBehavior':
            self.val = uml2.FunctionBehavior()
        elif xtype == 'uml:OpaqueBehavior':
            self.val = uml2.OpaqueBehavior()
        elif xtype == 'uml:Activity':
            self.val = uml2.Activity()
        else:
            print '*** mdreader.Behavior: unhandled type', xtype
        if self.val: self.val.name = attrs.get('name', None)

    def begEltIn(self, tag, attrs):
        if self.type == 'uml:FunctionBehavior':
            return self.begEltInFunctionBehavior(tag, attrs)
        elif self.type == 'uml:OpaqueBehavior':
            return self.begEltInOpaqueBehavior(tag, attrs)
        elif self.type == 'uml:Activity':
            return self.begEltInActivity(tag, attrs)
        else:
            print '*** mdreader.Behavior: begEltIn type', self.type
            return SkipElement(self, tag, attrs)

    def endEltIn(self, tag):
        if self.type == 'uml:FunctionBehavior':
            return self.endEltInFunctionBehavior(tag)
        elif self.type == 'uml:OpaqueBehavior':
            return self.endEltInOpaqueBehavior(tag)
        elif self.type == 'uml:Activity':
            return self.endEltInActivity(tag)
        else:
            print '*** mdreader.Behavior: endEltIn type', self.type
            return self

    # Activity =========================
    def begEltInActivity(self, tag, attrs):
        el = None

    def endEltInActivity(self, tag):
        if tag == self.tag: return self.parent
        return self

    # FucntionBehavior ===================
    def begEltInFunctionBehavior(self, tag, attrs):
        el = None
        if tag == 'body':
            self.data = ""

    def endEltInFunctionBehavior(self, tag):
        if tag == self.tag: return self.parent
        if tag == 'body':
            self.val.body = self.data
        return self

    # OpaqueBehavior =====================
    def begEltInOpaqueBehavior(self, tag, attrs):
        el = None
        if tag == 'body':
            self.data = ""

    def endEltInOpaqueBehavior(self, tag):
        if tag == self.tag: return self.parent
        if tag == 'body':
            self.val.body = self.data
        return self


class Constraint(XmiElement):
    """ 
    Need to work on this.
    Don't generate UML state, just copy body to xxx
    """

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = uml2.Constraint()

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'specification':
            el = OpaqueExpression(self, tag, attrs)
            self.val.specification = el.val
        else:
            print "*** mdreader: unhandled tag in <ownedRule>"
        return el

    def endEltIn(self, tag):
        if tag == self.tag: return self.parent
        if tag == 'specification':
            # el = OpaqueExpression ???
            raise Exception
            self.body = self.spec.body
        return self


class TimeExpression(XmiElement):
    """
    This can be involved. (Check out the lol "Simple Time" package in UML.)
    So we just make this a string value hoping it will work.
    """

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = ""

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'expr':
            if attrs['xmi:type'] != 'uml:LiteralString': raise Exception
            exval = attrs['value']
            self.val = exval
        else:
            print "*** mdreader.When: unhandled tag:", tag
        return el


class Region(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = uml2.Region()
        val = self.val
        if parent.type == 'uml:State':
            val.state = parent.val
        elif parent.type == 'uml:StateMachine':
            val.statemachine = parent.val
        else:
            print "region has unknown parent class: " + parent.typ

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'subvertex':
            el = Vertex(self, tag, attrs)
            el.val.container = self.val	# vertex contained in this region
            self.val.subvertex.append(el.val)
        elif tag == 'transition':
            el = Transition(self, tag, attrs)
            el.val.container = self.val	# transition contained in this region
            self.val.transition.append(el.val)
        else:
            print "Region: unknown tag?"
        return el

    def deref(self):
        self.deref_kids()


class Trigger(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = uml2.Trigger()
        self.event = attrs.get('event', None)
        #print "T:", attrs['xmi:id'], self.val
        if self.event == None:
            #print "mdreader.Trigger: no event", attrs['xmi:id']
            pass

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'event':
            raise Exception, "need go get event"
        else:
            print "unhandled tag \"" + tag + "\" in " + self.tag
        return el

    def deref(self):
        if self.event: self.val.event = self.xmidict[self.event]
        self.deref_kids()


class Transition(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = uml2.Transition()
        val = self.val
        if attrs.has_key('visibility'): val.visibility = attrs['visibility']
        if attrs.has_key('kind'): val.kind = str(attrs['kind'])
        if attrs.has_key('name'): val.name = str(attrs['name'])
        #
        # idrefs ...
        self.source = attrs.get('source', None)
        self.target = attrs.get('target', None)
        self.trigger = []
        self.guard = attrs.get('guard', None)
        self.effect = attrs.get('effect', None)

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'source':
            self.source = attrs['xmi:idref']
        elif tag == 'target':
            self.target = attrs['xmi:idref']
        elif tag == 'trigger':
            el = Trigger(self, tag, attrs)
            el.event = attrs.get('event', None)
            self.val.trigger.append(el.val)
        elif tag == 'ownedRule':
            el = Constraint(self, tag, attrs)
            self.val.ownedRule.append(el.val)
        elif tag == 'effect':
            el = Behavior(self, tag, attrs)
            if self.effect:
                print '+++ mdreader: Transition: effect attr and element'
            self.val.effect = el.val    # added 121007
        elif tag == 'guard':
            el = Guard(self, tag, attrs)
        else:
            print "*** mdreader: unhandled tag \"" + tag + "\" in " + self.tag
        return el

    def deref(self):
        val = self.val
        xmidict = self.xmidict
        if self.source: self.val.source = xmidict[self.source]
        if self.target: self.val.target = xmidict[self.target]
        for trg in self.trigger: val.trigger.append(xmidict[trg])
        if self.guard: val.guard = xmidict[self.guard] # MD17: now ownedRule
        if self.effect: val.effect = xmidict[self.effect]
        self.deref_kids()


# States show up as subvertex tags.  Note that MD10 does not provide
# the isComposite property.  One must deduce this from regions living
# underneath.

class Vertex(XmiElement):
    """
    Internal transitions show up as transitions with type='internal'
    """

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        xtype = attrs['xmi:type']
        self.type = xtype
        self.submachine = False
        if attrs.has_key('outgoing'):
            self.outgoing = str(attrs['outgoing']).split(',')
        else:
            self.outgoing = []
        if attrs.has_key('incoming'):
            self.incoming = str(attrs['incoming']).split(',')
        else:
            self.incoming = []
        if xtype == 'uml:State':
            # states are simple by default
            val = uml2.State()
            if attrs.has_key('submachine'):
                self.submachine = attrs['submachine']
                val.isSimple = False
                val.isSubmachineState = True
                #print "state is submachine:", val
        elif xtype == 'uml:Pseudostate':
            val = uml2.Pseudostate()
            if attrs.has_key('kind'): val.kind = str(attrs['kind'])
            #val.stateMachine = XXX	# \todo track statemachine
            #val.stateMachine.connectionPoint.append(val)
        elif xtype == 'uml:FinalState':
            val = uml2.FinalState()	# final state isa State
        else:
            print "class Vertex: typ=", xtype
            val = None
        val.container = self.parent.val	# parent relationship
        self.val = val
        if attrs.has_key('name'):
            val.name = str(attrs.get('name'))
            #print "class Vertex: ", val.name
        else:
            pass
            #print "class Vertex: ", attrs

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'region':
            # A Composite state has at least one region.
            # An orthogonal state has at least two regions.
            #print "entering " + self.type + "/region"
            #if self.val.name: print "state/region with name", self.val.name
            self.val.isSimple = False
            if self.val.isComposite == True:
                self.val.isOrthogonal = True
            else:
                self.val.isComposite = True
            if len(self.val.region) > 0: # orthogonal if more than one region
                self.val.isOrthogonal = True
            el = Region(self, tag, attrs)
            self.val.region.append(el.val) # append region
        elif tag == 'outgoing':
            # not used in MD17 (was used in MD10)
            self.outgoing.append(attrs['xmi:idref'])
        elif tag == 'incoming':
            # not used in MD17 IMO
            self.incoming.append(attrs['xmi:idref'])
        elif tag == 'stateInvariant':
            el = Constraint(self, tag, attrs)
            self.val.stateInvariant = el.val
        elif tag == 'entry':        # \todo: fix kludge using name
            xtype = attrs.get('xmi:type', None)
            if not xtype: raise Exception
            if xtype == 'uml:FunctionBehavior':
                v = uml2.FunctionBehavior()
            else:
                raise Exception
            v.body = attrs.get('name', None)
            self.val.entry = v
        elif tag == 'exit':        # \todo: fix kludge using name
            # tags: xmi:type, name, xmi:id, ...
            xtype = attrs.get('xmi:type', None)
            if not xtype: raise Exception
            if xtype == 'uml:FunctionBehavior':
                v = uml2.FunctionBehavior()
            elif xtype == 'uml:Activity':
                v = uml2.Activity()
            else:
                pdb.set_trace()
                raise Exception
            v.body = attrs.get('name', None)
            self.val.exit = v
        elif tag == 'doActivity':        # \todo: fix kludge using name
            # tags: xmi:type, name, xmi:id, ...
            xtype = attrs.get('xmi:type', None)
            if not xtyp: raise Exception
            if xtype == 'uml:FunctionBehavior':
                v = uml2.FunctionBehavior()
            else:
                raise Exception
            v.body = attrs.get('name', None)
            self.val.doActivity = v
        elif tag == 'connection':
            #This is inside <subvertex>...
            #<connection xmi:type='uml:ConnectionPointReference' xmi:id='...'
            # visibility='public'>
            # <entry xmi:idref='...'/>
            #</connection>
            el = ConnectionPointReference(self, tag, attrs)
            if self.type != 'uml:State': raise Exception
            self.val.connection.append(el.val)
        elif tag == 'xmi:Extension':
            pass
        elif tag == 'modelExtension':
            pass
        elif tag.startswith("diagram"):
            pass
        elif tag == 'ownedDiagram':
            pass
        elif tag == 'binaryObject':
            pass
        elif tag.startswith("used"):
            pass
        else:
            print "subvertex.begEltIn: unhandled tag:", tag
        return el

    def endEltIn(self, tag):
        if tag == self.tag: return self.parent
        if tag == 'stateInvariant':
            self.val.stateInvariant = self.stateInvariant.body
            print "--- mdreader: got stateInvariant:", self.val.stateInvariant
        return self

    def deref(self):
        val = self.val
        xmidict = self.xmidict
        for ref in self.outgoing: val.outgoing.append(xmidict[ref])
        for ref in self.incoming: val.incoming.append(xmidict[ref])
        if self.submachine:
            self.val.submachine = xmidict[self.submachine]
        self.deref_kids()



class ConnectionPointReference(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = uml2.ConnectionPointReference()
        self.entry = []
        self.exit = []

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'entry':
            if attrs.has_key('xmi:idref'):
                self.entry.append(attrs['xmi:idref'])
            else:
                raise Exception
        elif tag == 'exit':
            if attrs.has_key('xmi:idref'):
                self.entry.append(attrs['xmi:idref'])
            else:
                raise Exception
        else:
            print "connection.begEltIn: unhandled tag:", tag
        return el

    def deref(self):
        val = self.val
        xmidict = self.xmidict
        for ref in self.entry:
            val.entry.append(xmidict[ref])
        self.deref_kids()


class OpaqueExpression(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = uml2.OpaqueExpression()

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'body':
            self.data = ""
        elif tag == 'language':
            # ignore
            pass
        else:
            print "*** mdreader: unhandled tag in <specifiation>"
        return el

    def endEltIn(self, tag):
        if tag == self.tag: return self.parent
        if tag == 'body':
            self.val.body.append(self.data)
        return self


class Classifier(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        xtype = attrs['xmi:type']
        if xtype == 'uml:Signal':
            self.val = uml2.Signal()
            self.val.name = attrs['name']
            self.val.visibility = 'public'
        else: 
            if peror: print '*** mdreader: unhandled Classifier', xtype

class OwnedMember(XmiElement):          # :NamedElement
    """ <ownedMember> seems to be a grab-bag for anything.  It works like a
        dynamic type item.  From another perspective, Packages have a named
        list of ownedMembers ...
        Q: Are ownedMembers PackageableELements?  If so then should have a name.
        Also use this to handle "packagedElement"
    """

    def __init__(self, parent, tag, attrs):
        raise Exception


class PackagedElement(XmiElement):      # :PackageableElement
    """
    This appears with MD17.  It seems replace ownedMember from MD10.
    packagedElement is a member of the Package class, where it is a list
    of, well, packaged elements.  I think of it as this way:
    <package><packagedElement typ="elt"> ... </package>
    similar to
    <package><elt>...</elt>...</package>
    but first form is like using factory methods.
    Another option for paring is to provide <package> handlers and change
    the tag.  But I think this needs to happen at time <packagedElement> is
    seen.  i.e., if tag == "packagedElement".. if typ="uml:Signal" :
    el = Signal(parent, attrs, tag="packagedElement")
    """

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        xtype = attrs['xmi:type']
        self.type = xtype

        if xtype == 'uml:Package':
            # self.val set in initKlass
            self.initPackage(parent, tag, attrs)
        elif xtype == 'uml:StateMachine':
            self.initStateMachine(parent, tag, attrs)
        elif xtype == 'uml:Signal':
            self.initSignal(parent, tag, attrs)
        elif xtype == 'uml:FunctionBehavior':
            self.initFunctionBehavior(parent, tag, attrs)
        elif xtype == 'uml:Enumeration':
            self.initEnumeration(parent, tag, attrs)
        elif xtype == 'uml:SignalEvent':
            self.initSignalEvent(parent, tag, attrs)
        elif xtype == 'uml:TimeEvent':
            self.initTimeEvent(parent, tag, attrs)
        elif xtype == 'uml:LiteralBoolean':
            pass
        elif xtype == 'uml:Profile':
            # used for extensions (e.g., SysML, C++ coder)
            pass
        elif xtype == 'uml:Class':
            print "+++ mdreader: not handling class yet"
        else:
            print "*** mdreader.PackagedElement: unknown 'xmi:type':", xtype
            sys.exit(1)
        if self.val: parent.val.packagedElement.append(self.val)

    def begEltIn(self, tag, attrs):
        # In here we may see almost any element.
        el = None
        if self.type == 'uml:Package':
            return self.begEltInPackage(tag, attrs)
        elif self.type == 'uml:StateMachine':
            return self.begEltInStateMachine(tag, attrs)
        elif self.type == 'uml:Signal':
            raise Exception
        elif self.type == 'uml:FunctionBehavior':
            return self.begEltInFunctionBehavior(tag, attrs)
        elif self.type == 'uml:Enumeration':
            return self.begEltInEnumeration(tag, attrs)
        elif self.type == 'uml:SignalEvent':
            return self.begEltInSignalEvent(tag, attrs)
        elif self.type == 'uml:TimeEvent':
            return self.begEltInTimeEvent(tag, attrs)
        elif self.type == 'uml:Class':
            return self.begEltInClass(tag, attrs)
        elif self.type == 'uml:Profile':
            return None
        else:
            print "in PackagedElement, type=", self.type, ", unknown tag:", tag
        return el

    def endEltIn(self, tag):
        if self.type == 'uml:Package':
            return self.endEltInPackage(tag)
        # skip Enumeration
        # skip Signal
        if self.type == 'uml:SignalEvent':
            return self.endEltInSignalEvent(tag)
        if self.type == 'uml:StateMachine':
            return self.endEltInStateMachine(tag)
        if self.type == 'uml:TimeEvent':
            return self.endEltInTimeEvent(tag)
        return XmiElement.endEltIn(self, tag)

    def deref(self):
        val = self.val
        if self.type == 'uml:StateMachine':
            self.derefStateMachine()
        if self.type == 'uml:SignalEvent':
            self.derefSignalEvent()
        self.deref_kids()

    # Package =============================
    def initPackage(self, parent, tag, attrs):
        self.val = uml2.Package()

    def begEltInPackage(self, tag, attrs):
        el = None
        if tag == 'packagedElement':
            el = PackagedElement(self, tag, attrs)
        elif tag == 'xmi:Extension':
            # \todo just skip for now
            el = SkipElement(self, tag, attrs)
        elif tag == 'ownedComment':
            el = SkipElement(self, tag, attrs)
        else:
            print '*** mdreader.PackagedElement.begEltInPackage:', tag
        return el

    def endEltInPackage(self, tag):
        return XmiElement.endEltIn(self, tag)

    # Class ===============================
    def initClass(self, parent, tag, attrs):
        pass

    def begEltInClass(self, tag, attrs):
        el = None
        if tag == 'ownedAttribute':
            pass
        else:
            print '*** mdreader.PackagedElement.begEltInClass: unknown:', tag
        return el

    # Enumeration =========================
    def initEnumeration(self, parent, tag, attrs):
        self.val = uml2.Enumeration()

    def begEltInEnumeration(self, tag, attrs):
        el = None
        if tag == 'ownedLiteral':
            #<ownedLiteral xmi:type='uml:EnumerationLiteral' xmi:id='...'
            # name='ScMode' visibility='public'/>
            self.val.ownedLiteral.append(attrs['name'])
            # but can be structured with classifier, so skip
            el = SkipElement(self, tag, attrs)
        return el

    # FunctionBehavior ====================
    def initFunctionBehavior(self, parent, tag, attrs):
        if attrs.has_key('xmi:idref'): raise Exception, "need to handle this"
        self.val = uml2.FunctionBehavior()
        #self.val.name = attrs.get('name', '(mdreader BUG)')

    def begEltInFunctionBehavior(self, tag, attrs):
        el = None
        if tag == 'body':
            self.data = ""
        return el

    def endEltInFunctionBehavior(self, tag, attrs):
        el = None
        if tag == 'body':
            self.val.body = self.data
        return el

    # Signal ==============================
    def initSignal(self, parent, tag, attrs):
        if attrs.has_key('xmi:idref'): raise Exception, "need to handle this"
        self.val = uml2.Signal()
        self.val.name = attrs.get('name', '(mdreader BUG)')

    # SignalEvent =========================
    def initSignalEvent(self, parent, tag, attrs):
        self.val = uml2.SignalEvent()
        parent.val.packagedElement.append(self.val)
        self.signal = signal = attrs.get('signal', None)
        self.val.name = name = attrs.get('name', None)
        # This belongs in the validator:
        if name and not signal:
            print '+++ SignalEvent should have Signal, not name:', name

    def begEltInSignalEvent(self, tag, attrs):
        el = None
        raise Exception, "unhandled tag " + tag
        return el

    def endEltInSignalEvent(self, tag):
        return XmiElement.endEltIn(self, tag)

    def derefSignalEvent(self):
        if self.signal:
            self.val.signal = self.xmidict[self.signal]
        #self.deref_kids() - handled in self.deref()

    # StateMachine ========================
    def initStateMachine(self, parent, tag, attrs):
        self.val = uml2.StateMachine()
        if attrs.has_key('name'):
            self.val.name = attrs['name']
        if attrs.has_key('vibibility'):
            self.val.visibility = attrs['visibility']
        if attrs.has_key('isReentrant'):
            self.val.isReentrant = attrs['isReentrant']

    def begEltInStateMachine(self, tag, attrs):
        el = None
        if tag == 'xmi:Extension':
            if pinfo: print "--- mdreader: in uml:StateMachine:", tag
            if not attrs['extender'].startswith('MagicDraw'):
                el = SkipElement(self, tag, attrs)
            else:
                el = MagicdrawExtension(self, tag, attrs)
        elif tag == 'submachineState':
            # <submachineState xmi:idref='...'/>
            # This seems to be used in statemachines to identify that the
            # statemachine is used as a submachine state.
            if not attrs.has_key('xmi:idref'): raise Exception
            self.val.submachineState.append(attrs['xmi:idref'])
        elif tag == 'nestedClassifier':
            if attrs['xmi:type'] != 'uml:Signal': raise Exception
            v = uml2.Signal()
            v.name = attrs['name']
            self.xmidict[attrs['xmi:id']] = v
            self.val.nestedClassifier.append(v) # so GAG how do I find this?
        elif tag == 'region':
            el = Region(self, tag, attrs)
            self.val.region.append(el.val)
        elif tag == 'connectionPoint':
            if attrs['xmi:type'] != 'uml:Pseudostate':
                raise Exception
            v = uml2.Pseudostate()
            v.name = attrs.get('name', None)
            v.kind = attrs['kind']
            v.stateMachine = self.val
            v.state = None
            self.xmidict[attrs['xmi:id']] = v
            self.val.connectionPoint.append(v)
        elif tag == 'ownedComment':
            el = SkipElement(self, tag, attrs)
        else:
            if pwarn: print '+++ todo: begEltInStateMachine:', tag
        return el

    def endEltInStateMachine(self, tag):
        return XmiElement.endEltIn(self, tag)

    def derefStateMachine(self):
        xmidict = self.xmidict
        idlist = self.val.submachineState
        smlist = []
        for idref in idlist:
            smlist.append(xmidict[idref])
        self.val.submachineState = smlist
        #self.deref_kids() - handled in self.deref()

    # TimeEvent ===========================
    def initTimeEvent(self, parent, tag, attrs):
        self.val = uml2.TimeEvent()
        parent.val.packagedElement.append(self.val)

    def begEltInTimeEvent(self, tag, attrs):
        el = None
        if tag == 'when':
            el = TimeExpression(self, tag, attrs)
        return el

    def endEltInTimeEvent(self, tag):
        return XmiElement.endEltIn(self, tag)


class Model(XmiElement):                # :Model
    """
    Model derived from Package, but Package is used
    """
  
    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        val = uml2.Model()
        self.val = val
        #self.env['model'] = val

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'ownedMember':
            el = OwnedMember(self, tag, attrs)
        elif tag == 'packagedElement': # MD17, replaces ownedMember from MD10
            el = PackagedElement(self, tag, attrs)
        return el


# --- diagrams ---------------------------------------------------------------

# Needs a bit of work still.
# I need to connect everything (eltElt and deref not done ???).
# I need to generate a routine to convert to UML Diag Int Format.

# element classes:
# State Transition TextBox TextBoxWithIcon PseudoState Split Region

# State: elementID geometry <regions>
# Transition: elementID linkFirstEndId linkSecondEndID geometry linkNameID
# TextBox: geometry (visible=false | text)

# Region: ???

class oldProperties(XmiElement):

    def __init__(self, parent=None, tag='properties', attrs={}):
        XmiElement.__init__(self, parent, tag, attrs)
        self.props = []

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'mdElement':
            el = Element(self, tag, attrs)
            self.props.append(el)
        return el

def parse_geometry(str):
    s1 = str.strip().split(';')
    if len(s1) == 1:
        # simple array
        s2 = s1[0].split(',')
        res = map(lambda s: int(s.strip()), s2)
    else:
        if len(s1[-1]) == 0:
            s1 = s1[0:-1]
        res = map(lambda sa: map(lambda s: int(s.strip()), sa.split(',')), s1)
    return res

class MdElement(XmiElement): # check if this survives to 17.0.2
    
    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.eclass = str(attrs['elementClass'])
        eclass = self.eclass
        if eclass == 'Diagram':
            self.val = mdext.Diagram()
        elif eclass == 'DiagramFrame':
            self.val = mdext.DiagramFrame()
        elif eclass == 'DiagramPresentationElement':
            self.val = mdext.DiagramPresentationElement()
        elif eclass == 'PseudoState':
            self.val = mdext.PseudoState()
        elif eclass == 'Region':
            self.val = mdext.Region()
        elif eclass == 'Split':
            self.val = mdext.Split()
        elif eclass == 'State':
            self.val = mdext.State()
        elif eclass == 'Transition':
            self.val = mdext.Transition()
        elif eclass == 'TextBox':
            self.val = mdext.TextBox()
        elif eclass == 'Split':
            self.val = mdext.Split()
        else:
            print '*** mdreader: unknown mdElement class:', eclass
        # self .ref , .link1, .link2, .linkN

    def begEltIn(self, tag, attrs):
        el = None
        eclass = self.eclass
        # handle generic tags
        if tag == 'elementID':
            self.val.elementID = attrs['xmi:idref']
        elif tag == 'geometry':
            self.data = ""
        elif tag == 'compartment':
            pass
        elif tag == 'mdOwnedViews':
            el = OwnedViews(self, tag, attrs)
            self.val.ownedViews = el.val
        elif tag == 'type':
            self.data = ''
            if attrs.has_key('xmi:value'): 
                self.val.type = attrs['xmi:value']
        elif tag == 'text':
            self.data = ''
        elif tag == 'diagramWindowBounds':
            self.data = ''
        # class-specific stuff
        elif eclass == 'Diagram':
            el = self.begEltInDiagram(tag, attrs)
        elif eclass == 'DiagramPresentationElement':
            el = self.begEltInDiagramPresentationElement(tag, attrs)
        elif eclass == 'Region':
            el = self.begEltInRegion(tag, attrs)
        elif eclass == 'Split':
            el = self.begEltInSplit(tag, attrs)
        elif eclass == 'State':
            el = self.begEltInState(tag, attrs)
        elif eclass == 'Transition':
            el = self.begEltInTransition(tag, attrs)
        else:
            print '*** mdreader.mdElement: unhandled tag:', tag, \
                '\n                             or class:', eclass
        return el

    def endEltIn(self, tag):
        if tag == 'geometry':
            self.val.geometry = parse_geometry(self.data)
        elif tag == 'type':
            if not self.val.type: self.val.type = self.data
        elif tag == 'text':
            self.val.text = self.data
        return LtWtHdlr.endEltIn(self, tag)

    # Diagram =========================
    def begEltInDiagram(self, tag, attrs):
        el = None
        if tag == 'mdElement':
            el = Element(self, tag, attrs)
        else:
            print '*** mdreader: unhandled tag in Diagram:', tag
        return el

    # DiagramPresentationElement ======
    def begEltInDiagramPresentationElement(self, tag, attrs):
        el = None
        if tag == 'mdElement':
            el = Element(self, tag, attrs)
        else:
            #print '*** mdreader: unhandled tag in DiagramPresElt:', tag
            el = SkipElement(self, tag, attrs)
        return el

    # Region ==========================
    def begEltInRegion(self, tag, attrs):
        el = None
        if tag == 'mdOwnedViews':
            el = OwnedViews(self, tag, attrs)
            self.val.ownedViews = el.val
        elif tag == 'mdElement':
            el = Element(self, tag, attrs)
        else:
            print '*** mdreader: unknown tag in begEltInRegion:', tag
            el = SkipElement(self, tag, attrs)
        return el

    # Split ===========================
    def begEltInSplit(self, tag, attrs):
        el = None
        if tag == 'lineStyle':
            ltype = str(attrs.get('xmi:value', ""))
        elif tag == 'firstShapeID':
            pass
        elif tag == 'secondShapeID':
            pass
        else:
            print '*** mdreader: unknown tag in begEltInSplit:', tag
            el = SkipElement(self, tag, attrs)
        return el

    # State ===========================
    def begEltInState(self, tag, attrs):
        el = None
        if tag == 'regions':
            # hack: just skip
            pass
        elif tag == 'mdElement':
            el = Element(self, tag, attrs)
        else:
            print '*** mdreader: unknown tag in begEltInRegion:', tag
            el = SkipElement(self, tag, attrs)
        return el

    # Text Box ========================

    # Transition ======================
    def begEltInTransition(self, tag, attrs):
        el = None
        if tag == 'linkFirstEndID':
            self.link1 = attrs['xmi:idref']
        elif tag == 'linkSecondEndID':
            self.link2 = attrs['xmi:idref']
        elif tag == 'linkNameID':
            self.linkN = attrs['xmi:idref']
        elif tag == 'compartment':
            pass
        elif tag == 'nameVisible':
            pass
        elif tag == 'ownedViews':
            el = OwnedViews(self, tag, attrs)
            self.val.ownedViews = el.val
        elif tag == 'properties':
            el = SkipElement(self, tag, attrs)
            msgW('skipping properties in diagram transition')
        else:
            msgF('unknown tag in diagram transition:' + tag)
            el = SkipElement(self, tag, attrs)
        return el

    def deref(self):
        xmidict = self.xmidict
        if self.val.elementID:
            self.val.elementID = xmidict[self.val.elementID]
        self.deref_kids()


class oldElementContainer(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.elts = []

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'mdElement':
            el = Element(self, tag, attrs)
            self.elts.append(el)
        return el

    def deref(self):                    # hack to get around xmielement ...
        # self.deref_kids()?
        pass

class MdOwnedViews(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = mdext.OwnedViews()

    def begEltIn(self, tag, attrs):
        if tag == 'mdElement':
            el = MdElement(self, tag, attrs)
        else:
            el = SkipElement(self, tag, attrs)
            print '*** mdreader: OwnedViews.begEltIn, unknown tag:', tag
        return el

# 17.0.2: states, transitions and pseudostates

uzob = []
uzel = []

class MdUsedObjects(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        id = attrs['href'][1:]
        #print '--- usedObjects:', attrs['href'][1:]
        uzob.append(id)

class MdDiagramContents(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'binaryObject':
            el = SkipElement(self, tag, attrs)
        elif tag == 'usedObjects':
            el = MdUsedObjects(self, tag, attrs)
        elif tag == 'usedElements':
            self.data = ''
        return el

    def endEltIn(self, tag):
        if tag == 'usedElements':
            id = self.data
            #print '--- usedElements:', id
            uzel.append(id)
        if tag == self.tag:
            return self.parent
        else:
            return self

class MdDiagram1(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)

    def begEltIn(self, tag, attrs):
        # so many goddammed layers
        el = None
        if tag == 'diagramContents':
            el = MdDiagramContents(self, tag, attrs)
        else:
            if pwarn: print '+++ mdreader: unhandled tag in MdDiagram1:', tag
        return el

class MdDiagramRepresentation(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = None

    def begEltIn(self, tag, attrs):
        el = None
        #pdb.set_trace()
        if tag == 'diagram:DiagramRepresentationObject':
            el = MdDiagram1(self, tag, attrs)
        return el

class MdOwnedDiagram(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)
        self.val = mdext.OwnedDiagram()

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'diagramRepresentation':
            el = MdDiagramRepresentation(self, tag, attrs)
        elif tag == 'xmi:Extension':
            el = MagicdrawExtension(self, tag, attrs)
        else:
            print '+++ mdreader: MdOwnedDiagram skipping:', tag
            el = SkipElement(self, tag, attrs)
        return el

class MdModelExtension(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'ownedDiagram':
            el = MdOwnedDiagram(self, tag, attrs)
        elif tag == 'event':
            if pinfo: print "--- mdreader: modelExtension tag: event"
            el = SkipElement(self, tag, attrs)
        else:
            if pwarn: print '+++ mdreader: MdModelExtension skipping tag:', tag
            el = SkipElement(self, tag, attrs)
        return el

    def deref(self):
        xmidict = self.xmidict
        self.deref_kids()
        # check for UML elements not in diagram: states, transitions
        for i in uzel:
            val = xmidict[i]
            if val != None:
                #pdb.set_trace()
                val.used_el = True

# ========================================

#add_extension(MdOwnedDiagrams)

class MagicdrawExtension(XmiElement):

    def __init__(self, parent, tag, attrs):
        XmiElement.__init__(self, parent, tag, attrs)

    def begEltIn(self, tag, attrs):
        el = None
        if tag == 'mdOwnediagrams':
            # pre 17.0.2?
            el = SkipElement(self, tag, attrs)
        elif tag == 'modelExtension':
            el = MdModelExtension(self, tag, attrs)
        elif tag == 'diagramRepresentation':
            el = MdDiagramRepresentation(self, tag, attrs)
        else:
            # skip
            if pinfo: print "--- mdreader: skipping top-level extension", tag
            el = SkipElement(self, tag, attrs)
        return el


class MagicdrawFileHdlr(XmiElement):
    # base handler, referenced from mdmain.py 
  
    def __init__(self):
        XmiElement.__init__(self, None, "", {})
        self.model = None
        self.extns = []
        self.warn = False
        self.info = False

    def begEltIn(self, tag, attrs):
        if tag == 'uml:Model':
            el = Model(self, tag, attrs)
            self.model = el.val
        elif tag == 'xmi:exporter':
            el = SkipElement(self, tag, attrs)
        elif tag == 'xmi:exporterVersion':
            el = SkipElement(self, tag, attrs)
        elif tag == 'xmi:Extension':
            el = MagicdrawExtension(self, tag, attrs)
            if el.val: self.extns.append(el.val)
        elif tag in ('xmi:XMI', 'xmi:Documentation',
                     'MagicDraw_Profile:DiagramInfo'):
            # skip
            el = None
        elif tag == 'c___ANSI_profile:C__Namespace':
            el = SkipElement(self, tag, attrs)
        elif tag == 'MagicDraw_Profile:Info':
            el = SkipElement(self, tag, attrs)
        elif tag == 'MagicDraw_Profile:TODO_Owner':
            el = SkipElement(self, tag, attrs)
        else:
            el = None
            print '*** mdreader: unknown top-level element:', tag
        return el

    def endEltIn(self, tag):
        if tag == self.tag:
            # If I call patchup here it fails, but if I call it after
            # parse completes it works.  Go figure.
            #self.patchup()
            return self.parent
        else:
            return self

    # This is to fill in stuff to connect the uml structure together, stuff
    # that might be left out of the xml file.  For example, in MD17 transitions
    # have source and target defined but the source/target vertices don't have
    # the corresponding incoming and outgoing transitions defined.
    def patchup(self):
        self.pu_Package(self.model)

    def pu_Package(self, package):
        if self.info: print "--- cl_package:", package
        for pkg in package.nestedPackage:
            self.pu_Package(pkg)
        for elt in package.packagedElement:
            elt_class = elt.__class__
            if elt_class == uml2.Transition:
                pass
                #print " clean transition:"
            if elt_class == uml2.StateMachine:
                self.pu_StateMachine(elt)

    def pu_StateMachine(self, stm):
        # statemachine issues:
        #  [vertex] <---> [trans]
        if self.info: print " clean statemachine", stm.name
        for reg in stm.region:
            self.pu_Region(reg)
        for elt in stm.submachineState:
            if not elt.isSubmachineState:
                print "*** error"; raise Exception
            if elt.submachine != stm:
                print "*** error: submachine != stm"  
                raise Exception
        if len(stm.connectionPoint) > 0:
            # This statemachine has connection points and can be referenced
            # in a submachine state.
            pass #print "pu_StateMachine: check connection points"
            
    def pu_Region(self, region):
        "Patch up Region."
        if region.statemachine == None and region.state == None:
            print "*** region needs to be in state or statemachine"
        if region.statemachine != None and region.state != None:
            print "*** region can't be in state and statemachine"
        for trn in region.transition:
            src = trn.source
            if not trn.source:
                pdb.set_trace()
            if trn not in src.outgoing:
                if self.warn:
                    print "+++ add trn to outgoing from", src.name, \
                        ":", trn.trigger[0].event.signal.name
                    #pdb.set_trace()
                src.outgoing.append(trn)
            tgt = trn.target
            if trn not in tgt.incoming:
                if self.warn:
                    print "+++ add trn to incoming from", tgt.name, \
                        ":", trn.trigger[0].event.signal.name
                    #pdb.set_trace()
                tgt.incoming.append(trn)
        for vtx in region.subvertex:
            if vtx.container != region:
                print "*** region error"
            if vtx.__class__ == uml2.Pseudostate:
                if vtx.kind in ('entryPoint', 'exitPoint'):
                    # stateMachine where the point is defined
                    if vtx.stateMachine == None:
                        pdb.set_trace()
                        print " ???"

# --- last line of ssk/mdreader.py ---

