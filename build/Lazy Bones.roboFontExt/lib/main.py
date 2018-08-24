import vanilla
from mojo.UI import CurrentGlyphWindow, StatusInteractivePopUpWindow
from mojo.roboFont import CurrentGlyph
from glyphConstruction import GlyphConstructionBuilder, ParseGlyphConstructionListFromString, parseGlyphName
from mojo.extensions import registerExtensionDefaults, setExtensionDefault, getExtensionDefault

# ---------
# Interface
# ---------

# defaults

def showConstructionDefaults():
    vanilla.dialogs.message("LOL! This doesn't work yet.")

# Pop Up Window

def showConstructionForCurrentGlyph():
    glyph = CurrentGlyph()
    if glyph is None:
        return
    constructions = StarterConstructions(glyph.layer)
    construction, decompose = constructions.guessConstructionForGlyphName(glyph.name)
    if construction is not None:
        StarterConstructionPopUpWindow(glyph, construction, decompose)
    else:
        vanilla.dialogs.message(
            "No construction available for %s." % glyph.name,
            "Define one in the preferences so that you can be lazy in the future."
        )

class StarterConstructionPopUpWindow(object):

    def __init__(self, glyph, construction, decompose):
        self.glyph = glyph

        width = 350
        height = 120
        editorWindow = CurrentGlyphWindow()
        (editorX, editorY, editorW, editorH), screen = getGlyphEditorRectAndScreen(editorWindow)
        x = editorX + ((editorW - width) / 2)
        y = editorY + ((editorH - height) / 2)
        self.w = StatusInteractivePopUpWindow((x, y, width, height), screen=screen)

        self.w.constructionEditor = vanilla.EditText((15, 15, -15, 22), construction)
        self.w.decomposeCheckBox = vanilla.CheckBox((15, 45, -15, 22), "Decompose", value=decompose)

        self.w.open()

        self.w.line = vanilla.HorizontalLine((15, -45, -15, 1))
        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelButtonCallback)
        self.w.okButton = vanilla.Button((-85, -35, 70, 20), "OK", callback=self.okButtonCallback)

        self.w.setDefaultButton(self.w.okButton)
        self.w.cancelButton.bind(".", ["command"])
        self.w.getNSWindow().makeFirstResponder_(self.w.constructionEditor.getNSTextField())

        self.w.open()

    # ---------
    # Callbacks
    # ---------

    def okButtonCallback(self, sender):
        buildGlyphFromConstruction(
            self.glyph,
            self.w.constructionEditor.get(),
            self.w.decomposeCheckBox.get()
        )
        self.w.close()

    def cancelButtonCallback(self, sender):
        self.w.close()


def getGlyphEditorRectAndScreen(editorWindow):
    screen = editorWindow.w.getNSWindow().screen()
    nsWindow = editorWindow.w.getNSWindow()
    scrollView = editorWindow.getGlyphView().enclosingScrollView()
    rectInWindowCoords = scrollView.convertRect_toView_(scrollView.frame(), None)
    rectInScreenCoords = nsWindow.convertRectToScreen_(rectInWindowCoords)
    (screenX, screenY), (screenWidth, screenHeight) = screen.frame()
    (x, y), (w, h) = rectInScreenCoords
    y = -(y + h)
    return (x, y, w, h), screen

# -------------
# Constructions
# -------------

class StarterConstructions(object):

    def __init__(self, layer):
        self.layer = layer
        self.constructions = loadConstructions(layer)

    def guessConstructionForGlyphName(self, name):
        construction = None
        decompose = False
        if name in self.constructions:
            construction, decompose = self.constructions[name]
        elif "." in name:
            base, suffix = name.split(".", 1)
            if base in self.constructions:
                construction, decompose = self.constructions[base]
        return construction, decompose


def buildGlyphFromConstruction(glyph, construction, decompose):
    glyph.prepareUndo("Lazy Bones")
    layer = glyph.layer
    if decompose:
        construction = "*null = " + construction
    else:
        construction = "null = " + construction
    built = GlyphConstructionBuilder(construction, layer.font.naked())
    # name = built.name
    glyph.unicode = built.unicode
    glyph.note = built.note
    #dest.markColor = built.mark
    glyph.width = built.width
    if glyph.unicode is None:
        glyph.autoUnicodes()
    built.drawPoints(glyph.getPointPen())
    glyph.performUndo()

def loadConstructions(layer):
    text = getVariables(layer)
    text += defaultConstructions
    # text += getExtensionDefault(defaultsKey)
    constructions = {}
    for construction in ParseGlyphConstructionListFromString(text):
        name, construction = parseGlyphName(construction)
        if name is None:
            continue
        name = name.strip()
        construction = construction.strip()
        decompose = False
        if name.startswith("*"):
            name = name[1:]
            decompose = True
        constructions[name] = (construction, decompose)
    return constructions

variableTemplate = """
$overshootUpper = {overshootUpper}
$overshootLower = {overshootLower}
"""

def getVariables(layer):
    variables = {
        "overshootUpper" : 0,
        "overshootLower" : 0
    }
    if "O" in layer:
        bounds = layer["O"].bounds
        if bounds is not None:
            variables["overshootUpper"] = bounds[1]
    if "o" in layer:
        bounds = layer["o"].bounds
        if bounds is not None:
            variables["overshootLower"] = bounds[1]
    return variableTemplate.format(**variables)


# --------
# Defaults
# --------

defaultsKey = "com.typesupply.LazyBones.constructions"

defaultConstructions = """
*a = u + n ^ u
*b = h + o ^ n, o
*c = e ^ e
*d = b @ ~none, none ^ b', b'
*e = o ^ o
*f = n ^ n
*g = b @ ~none, ~`xHeight - ascender - {overshootLower}` ^ b', b'
*h = n ^ n
*i = n ^ n
*j = i + f @ ~center, ~`descender+{overshootLower}` ^ i
*k = h + v ^ h
*l = i ^ i
*m = n & n ^ n, n
*n = o ^ o
*o = n ^ n
*p = b @ none, ~`xHeight - ascender - {overshootLower}` ^ b, b
*q = b @ ~none, ~`xHeight - ascender - {overshootLower}` ^ b', b'
*r = n
*s = o ^ o
*t = f @ none, ~{overshootLower} ^ f
*u = n @ ~0, ~{overshootLower} ^ n', n'
*v = n ^ n
*w = v & v ^ v, v
*x = v ^ v
*y = v + j ^ v
*z = f ^ f
""".strip()

# don't register defaults until more constructions are in place
# registerExtensionDefaults({defaultsKey : defaultConstructions})

if __name__ == "__main__":
    showConstructionForCurrentGlyph()
