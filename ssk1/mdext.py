# mdext.py - MagicDraw Extensions
#
# Copyright (c) 2010-2013,2018 Matthew R. Wette
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

# xmi:Extension
#  modelExtension
#   ownedDiagram
#    xmi:Extension
#     diagramRepresentation
#      diagram:DiagramRepresentationObject
#       diagramContents
#        binaryObject
#        usedObjects (href=...)
#        usedElements (href=...)


# Inferred from SSKdemo1.mdxml:

class Element:
    def __init__(self):        
        self.elementID = 0              # xmlid of UML element => 
        self.geometry = []              # string list w/ sep ',' or ';'
        self.klass = None
        self.type = None                # string ?
        self.ownedViews = None
        #
        self.xmi_id = None
        self.used_el = False

class OwnedDiagrams:
    def __init__(self):
        self.mdElement = []     # :DiagramPresentationElement[] ???

class OwnedDiagram(Element):    # ???
    def __init__(self):
        Element.__init__(self)

class DiagramPresentationElement(Element):
    def __init__(self):
        Element.__init__(self)
        self.type = ""                  # :String
        self.umlType = ""               # :String
        self.zoomFactor = 1.0           # :Float
        self.diagramOpened = True       # :Boolean
        self.diagramFrameInitialSizeSet = True # :Boolean
        self.requiredFeature = ""              # :String
        self.exporterVersion = ""              # :String
        self.diagramWIndowBounds = ""          # :String (2, 24, 947, 618)
        self.diagramScrollPositionX = ""       # :String (in attr xmi:value)
        self.diagramScrollPositionY = ""       # :String (in attr xmi:value)
        self.maximized = False                 # :Boolean
        self.active = False                    # :Boolean
        self.mdOwnedViews = []                 # :mdElement[]

class OwnedViews:
    def __init__(self):
        self.mdElement = []

class Diagram(Element):
    def __init__(self):
        Element.__init__(self)

class DiagramFrame(Element):
    def __init__(self):
        Element.__init__(self)
        self.compartment = ""

class PseudoState(Element):
    def __init__(self):
        Element.__init__(self)
        self.compartment = ""

class Region(Element):
    def __init__(self):
        Element.__init__(self)

class Split(Element):
    def __init__(self):
        Element.__init__(self)
        self.type = 1                   # ???
        self.lineStyle = 1              # ???
        self.firstShapeID = 0
        self.secondShapeID = 0

class State(Element):
    def __init__(self):
        Element.__init__(self)
        self.compartment = ""
        self.regions = []               # :Element

class Transition(Element):
    def __init__(self):
        Element.__init__(self)
        self.linkFirstEndID = 0
        self.linkSecondEndID = 0
        self.linkNameID = 0
        self.nameVisible = True         # :Boolean

class TextBox(Element):
    def __init__(self):
        Element.__init__(self)
        self.text = ""

#        if tag == 'mdElement':
#            # convert mdElement to UML2 Diagram Interchange format
#            if self.eltclass == 'DiagramPresentationElement':
#               geom = self.geom
#                diag.position = uml2.Point(geom[0], geom[1])
#                diag.size = uml2.Dimension(geom[2], geom[3])
#            elif self.eltclass == 'State':
#                gelt = uml2.GraphNode()
#                self.gelt = gelt
#                geom = self.geom
#                gelt.position = uml2.Point(geom[0], geom[1])
#                gelt.size = uml2.Dimension(geom[2], geom[3])
#                if self.ref:
#                    xmidict = self.xmidict
#                    elt = xmidict[self.ref] # BAD DEREF HERE!
#                    gelt.semanticModel = uml2.CoreSemanticModelBridge()
#                    gelt.semanticModel.element = elt
#                diag.addElement(gelt)

# --- last line of mdext.py ---
