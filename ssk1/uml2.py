# uml2.py
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

# based on "UML Superstructure Specification, v2.0"

# added attributes could be added by analysis engines...

# listing classes in the same order as in the spec is problematic because
# Python doesn't support forward declarations


# === Kernel package ==================

class Element:
    def __init__(self):
        # associations
        self.ownedComment = []          # :Comment[*]
        self.ownedElement = []          # :Element[*]
        self.owner = None               # :Element[0..1]
        # added attributes
        self.xmi_id = None              # could add in reader for debugging
        self.used_el = False            # used in diagram

class NamedElement(Element):
    def __init__(self):
        Element.__init__(self)
        self.name = None

class Namespace(NamedElement):
    def __init__(self):
        NamedElement.__init__(self)
        # associations
        self.elementImport = []		# :ElementImport[*] - 
        self.importedMember = []	# :PackageableElement[*] -
        self.member = []		# :NamedElement[*] -
        self.ownedMember = []		# :NamedElement[*] -
        self.ownedRule = []		# :Constraint[*] - ?
        self.packageImport = []		# :PackageImport[*] - ?

    def getNamesOfMember(self):
        pass

    def membersAreDistinguishable(self):
        pass

    def importMembers(self):
        pass

    def excludeCollisions(self):
        pass

class RedefinableElement(NamedElement):
    def __init__(self):
        NamedElement.__init__(self)

class PackageableElement(NamedElement):
    def __init__(self):
        NamedElement.__init__(self)
        # attributes 
        self.visibility = 'public'	# :VisibilityKind[1]

VisibilityKind = ['public', 'private', 'protected', 'package']

class Type(PackageableElement):
    def __init__(self):
        PackageableElement.__init__(self)

class Classifier(Namespace,RedefinableElement,Type):
    def __init__(self):
        Namespace.__init__(self)
        RedefinableElement.__init__(self)
        Type.__init__(self)
        # attributes
        self.isAbstract = False		# :Boolean[1]
        self.isFinalSpecialization = False # :Boolean[1]
        # associations
        self.attribute = []		# :Property[*]
        self.feature = []               # :Feature[*]
        self.general = []               # :Classifier[*]
        self.generalization = []        # :Generalization[*]
        self.inheritedMember = []       # :NamedElement[*]
        self.redefinedClassifier = []   # :Classifier[*]
        self.package = None		# :Package[0..1]
        self.redefinedClassifier = []	# :Classifier[*]

class Class(Classifier):
    def __init__(self):
        Classifier.__init__(self)
        # associations
        self.nestedClassifier = []	# :Classifier[*]
        self.ownedAttribute = []	# :Property[*]
        self.ownedOperation = []	# :Operation[*]
        self.superClass = None		# :Class

class DataType(Classifier):
    def __init__(self):
        # associations
        self.ownedAttribute = []        # :Property[*]
        self.ownedOperation = []        # :Operation[*]

class Enumeration(DataType):
    def __init__(self):
        self.ownedLiteral = []          # :EnumerationLiteral[*] (use string)

class Package(Namespace,PackageableElement):
    def __init__(self):
        Namespace.__init__(self)
        PackageableElement.__init__(self)
        # attributes
        self.URI = None                 # :String[0..1]
        # associations
        self.nestedPackage = []		# :Package[*] - owned Packages
        self.packagedElement = []       # :PackageableElement[*]
        self.ownedType = []             # :Type[*]
        self.packageMerge = []		# :Package[*] - see 7.3.37
        self.nestingPackage = None	# :Package[0..1]
    
class Relationship(Element):
    def __init__(self):
        Element.__init__(self)
        # associations
        self.relatedElement = []        # :Element[1..*]

class DirectedRelationship(Relationship):
    def __init__(self):
        Relationship.__init__(self)
        # associations
        self.source = []                # :Element[1..*]
        self.target = []                # :Element[1..*]

class TypedElement(NamedElement):
    def __init__(self):
        NamedElement.__init__(self)
        # associations
        self.type = None                # :Type[0..1]
        
class ValueSpecification(PackageableElement,TypedElement):
    def __init__(self):
        PackageableElement.__init__(self)
        TypedElement.__init__(self)

class OpaqueExpression_inKernel(ValueSpecification):
    def __init__(self):
        # attributes
        self.body = []                  # :String[0..*]
        self.language = []              # :String[0..*]

class Constraint(PackageableElement):
    def __init__(self):
        PackageableElement.__init__(self)
        # associations
        self.constrainedElement = []    # :Element[*]
        self.context = None             # :Namespace[0..1]
        self.specification = None       # :ValueSpecification[0..1]


# === BasicBehaviors package =========

class Behavior(Class):
    def __init__(self):
        Class.__init__(self)
        self.isReentrant = False	# :Boolean[1]

class OpaqueBehavior(Behavior):
    def __init__(self):
        Behavior.__init__(self)
        self.body = ""                  # :String[0..*]
        self.language = ""              # :String[0..*]

class FunctionBehavior(OpaqueBehavior):
    def __init__(self):
        OpaqueBehavior.__init__(self)

class OpaqueExpression(OpaqueExpression_inKernel):
    def __init__(self):
        OpaqueExpression_inKernel.__init__(self)
        # associations
        self.behavior = None            # :Behavoir[0..1]
        self.result = None              # :Parameter[0..1]

# === BasicActivities package =========

# not using this yet
class Activity(Behavior):

    def __init__(self):
        # attributes
        self.isReadOnly = False         # :Boolean
        self.isSingleExecution = False  # :Boolean
        # associations
        self.group = []                 # :ActivityGroup[0..*]
        self.node = []                  # :ActivityNode[0..*]
        self.edge = []                  # :ActivityEdge[0..*]
        self.partition = []             # :ActivityPartition[0..*]
        self.structuredNode = []        # :StructuredActivityNode[0..*]
        self.variable = []              # :Variable[0..*]


# === Communications package ==========

class Trigger(NamedElement):
    def __init__(self):
        NamedElement.__init__(self)
        # associations
        #self.port = []			# :Port[*] - not shown in UML2.4
        self.event = None		# :Event[1]

class Event(PackageableElement):
    def __init__(self):
        PackageableElement.__init__(self)

class MessageEvent(Event):
    def __init__(self):
        Event.__init__(self)

class AnyReceiveEvent(MessageEvent):
    # denoted by event "all"
    def __init__(self):
        MessageEvent.__init__(self)

class Signal(Classifier):
    # I think it will be mistake to use this -- too abstract.
    def __init__(self):
        Classifier.__init__(self)
        # associations
        self.ownedAttribute = []	# :Property[*] - attr's owned by signal

class SignalEvent(MessageEvent):
    def __init__(self):
        MessageEvent.__init__(self)
        # attributes
        self.signal = None		# :Signal[1]

class CallEvent(MessageEvent):
    def __init__(self):
        MessageEvent.__init__(self)
        # attributes
        self.operation = None		# :Operation[1] -> string

class ChangeEvent(Event):
    def __init__(self):
        Event.__init__(self)
        # associations
        self.changeExpression = None	# :Expression[1]



# === Simple Time package ============= lol at the name "Simple Time"

class TimeEvent(Event):
    def __init__(self):
        Event.__init__(self)
        # attributes
        self.isRelative = False         # :Boolean
        # associations
        self.when = None                # :TimeExpression (use string?)


# === Model package ===================

class Model(Package):
    def __init__(self):
        Package.__init__(self)
        # attributes
        self.viewpoint = None		# :String[*] - viewpoint of model


# === StateMachine pacakge =============

class Vertex(NamedElement):
    def __init__(self):
        NamedElement.__init__(self)
        # associations
        self.outgoing = []		# :Transition[0..*]
        self.incoming = []		# :Transition[0..*]
        self.container = None		# :Region[0..1]
        # added attributes (see anlyz.py)
        self.level = -1			# :int - level of state in heirarchy

class ConnectionPointReference(Vertex):
    def __init__(self):
        Vertex.__init__(self)
        # associations
        self.entry = []			# :Pseudostate[1..*]
        self.exit = []			# :Pseudostate[1..*]
        self.state = None		# :State[0..1]

class Pseudostate(Vertex):
    def __init__(self):
        Vertex.__init__(self)
        # attributes
        self.kind = 'initial'		# :PseudostateKind[1]
        # associations
        self.stateMachine = None	# :Statemachine[0..1]
        self.state = None               # :State[0..1]

PseudostateKind = ['initial', 'deepHistory', 'shallowHistory', 'join', 'fork',
                   'junction', 'choice', 'entryPoint', 'exitPoint', 'terminate']


class Region(Namespace,RedefinableElement):
    def __init__(self):
        Namespace.__init__(self)
        RedefinableElement.__init__(self)
        # associations
        self.statemachine = None	# :StateMachine[0..1]
        self.state = None		# :State[0..1]
        self.transition = []		# :Transition[*]
        self.subvertex = []		# :Vertex[*]
        self.extendedRegion = None	# :Region[0..1]
        self.redfinitionContext = None	# :Classifier[1]
        # added attributes (see anlyz.py)
        self.index = None		# :int - index in state or statemachine
        self.level = -1			# :int - level (same as parent)
        self.longname = None		# :string - long name for region
        self.initstate = None		# :State
        self.nbyte = None		# :int - # bytes to encode region
        self.baseId = 0			# :int - base Id for region
        self.numShallowStates = 0	# :int - num states at first level
        self.numDeepStates = 0		# :int - num states for all levels

    def containingStatemachine(self):
        if self.statemachine:
            return self.statemachine
        else:
            return self.state.containingStatemachine()


class State(Namespace,RedefinableElement,Vertex):
    def __init__(self):
        Namespace.__init__(self)
        RedefinableElement.__init__(self)
        Vertex.__init__(self)
        # attributes
        self.isComposite = False	# :Boolean[1]
        self.isOrthogonal = False	# :Boolean[1]
        self.isSimple = True		# :Boolean[1]
        self.isSubmachineState = False	# :Boolean[1]
        # associations
        self.connection = []		# :ConnectionPointReference[0..*]
        self.connectionPoint = []	# :Pseudostate[0..*]
        self.deferrableTrigger = []	# :Trigger[0..*]
        self.doActivity = None		# :Behavior[0..1]
        self.entry = None		# :Behavior[0..1]
        self.exit = None		# :Behavior[0..1]
        self.redefinedState = None	# :State[0..1]
        self.region = []		# :Region[0..*]
        self.submachine = None		# :StateMachine[0..1]
        self.stateInvariant = None	# :Constraint[0..1]
        self.redefinitionContext = None	# :Classifier[1]
        # added attributes (see anlyz.py)
        self.shallowId = 0		# :int - ident of state in container
        self.deepId = 0			# :int - ident of state in ProxyMach
        self.longname = None		# :string - long name for state

    def containingStatemachine(self):
        return self.container.containingStatemachine()

class FinalState(State):
    def __init__(self):
        State.__init__(self)

class StateMachine(Behavior):
    def __init__(self):
        Behavior.__init__(self)
        # associations
        self.region = []		# :Region[1..]
        self.connectionPoint = []	# :Pseudostate[*]
        self.submachineState = []	# :State[*] \note not in UML2.4B bug?
        self.extendedStateMachine = []	# :StateMachine[*]
        # added attributes (see anlyz.py)
        self.longname = None
        self.pubsigs = []		# :string[*] - list of published sigs
        self.subsigs = []		# :string[*] - list of subscribed sigs
        self.proxy = []			# :ProxyMach - proxy machine tree


class Transition(Namespace,RedefinableElement):
    def __init__(self):
        Namespace.__init__(self)
        RedefinableElement.__init__(self)
        # attributes
        self.kind = 'external'		# :TransitionKind[1]
        # associations
        self.trigger = []		# :Trigger[0..*] ->? string (>1 trig ?)
        self.guard = None		# :Constraint[0..1] ->? string
        self.effect = None		# :Behavior[0..1] ->? string
        self.source = None		# :Vertex[1]
        self.target = None		# :Vertex[1]
        self.replacedTransition = None	# :Transition[0..1]
        self.redefinitionContext = None	# :Classifier[1]
        self.container = None		# :Region[1]

TransitionKind = ['external', 'internal', 'local']


# === Protocol StateMachine pacakge ===

class Port:                             # HACK, should inherit Ports.Port
    def __init__(self):
        # merged Port.attributes
        self.isService = None           # :Boolean
        self.isBehavior = None          # :Boolean
        self.isConjugated = None        # :Boolean
        # merged Port.associations
        self.required = []              # :Interface[*]
        self.provided = []              # :Interface[*]
        self.redefinedPort = None       # :Port
        # associations
        self.protocol = None            # :ProtocolStateMachine[0..1]


class ProtocolConformance(DirectedRelationship):
    def __init__(self):
        DirectedRelationship.__init__(self)
        # associations
        self.specificMachine = None     # :ProtocolStateMachine[1]


class ProtocolStateMachine(StateMachine):
    def __init__(self):
        StateMachine.__init__(self)
        # associations
        self.conformance = []           # :ProtocolConformance[*]


class ProtocolTransition(Transition):
    def __init__(self):
        Transition.__init__(self)
        # associations
        self.referred = []              # :Operation[0..*]
        self.postCondition = None       # :Constraint[0..1]
        self.preCondition = None        # :Constraint[0..1]


# === diagrams ... - where does this come from ?

# =========

# From UML Diagram Interchange Format (circa 2003)

class Dimension:

    def __init__(self, width=0.0, height=0.0):
        self.width = width              # :Double
        self.height = height            # :Double

class Point:

    def __init__(self, x=0.0, y=0.0):
        self.x = x                      # :Double
        self.y = y                      # :Double

class BezierPoint(Point):

    def __init__(self):
        Point.__init__(self)
        self.controls = []              # :Point[0..2]

class Property:

    def __init__(self, key=None, value=None):
        self.key = key                  # :String
        self.value = value              # :String

class DiagramLink:

    def __init__(self):
        self.zoom = 1.0                 # :Double
        self.viewport = None            # :Point
        # associations
        self.diagram = None             # :Diagram
        self.graphElement = None        # :GraphElement

class DiagramElement:

    def __init__(self):
        self.isVisible = False		# :Boolean

class GraphElement(DiagramElement):

    def __init__(self):
        DiagramElement.__init__(self)
        self.position = None            # :Point
        # associations
        self.semanticModel = None

class SemanticModelBridge:

    def __init__(self):
        self.presentation = None        # :String

class CoreSemanticModelBridge(SemanticModelBridge):

    def __init__(self, element=None):
        SemanticModelBridge.__init__(self)
        # associations
        self.element = element          # :Element

class GraphEdge(GraphElement):

    def __init__(self):
        GraphElement.__init__(self)
        self.waypoints = []             # :Point[2..*]

class GraphNode(GraphElement):

    def __init__(self):
        GraphElement.__init__(self)
        self.size = None                # :Dimension[0..1]

class Diagram(GraphNode):

    def __init__(self):
        GraphNode.__init__(self)
        self.name = None                # :String
        self.zoom = 1.0                 # :Double
        self.viewport = None            # :Point
        # associations
        self.diagramLink = []           # :DiagramLink[0..*]

    # added
    def addElement(self, element):
        link = DiagramLink()
        link.diagram = self
        link.graphElement = element

class LeafElement(DiagramElement):
  
    def __init__(self):
        DiagramElement.__init__(self)

class TextElement(LeafElement):

    def __init__(self):
        LeafElement.__init__(self)
        self.text = None                # :String

class Image(LeafElement): pass

class GraphicPrimitive(LeafElement):

    def __init__(self):
        LeafElement.__init__(self)

class Polyline(GraphicPrimitive):

    def __init__(self):
        GraphicPrimitive.__init__(self)
        self.waypoints = []             # :Point[2..*]
        self.closed = False             # :Boolean

class Ellipse(GraphicPrimitive): pass

        
# --

class StateFig(GraphNode):

    def __init__(self):
        GraphNode.__init__(self)
        
class FinalStateFig(GraphNode): pass

class TransigionFig(GraphEdge): pass
                   
# --- last line of uml2.py ---
