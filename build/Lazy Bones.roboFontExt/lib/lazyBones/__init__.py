import weakref
import vanilla
import ezui
from copy import deepcopy
from mojo.UI import CurrentFontWindow, CurrentGlyphWindow, StatusInteractivePopUpWindow
from mojo.roboFont import AllFonts, CurrentFont, CurrentGlyph
from glyphConstruction import GlyphConstructionBuilder, ParseGlyphConstructionListFromString, parseGlyphName
from mojo.extensions import registerExtensionDefaults, setExtensionDefault, getExtensionDefault

___all__ = """
showConstructionForCurrentGlyph
showConstructionsForCurrentFont
showConstructionDefaults
guessConstructionForGlyphName
guessConstructionsForGlyphNames
buildGlyphFromConstruction
""".strip().splitlines()


# -----
# Glyph
# -----

def showConstructionForCurrentGlyph():
    """
    Show the construction editor for the current glyph.
    """
    glyph = CurrentGlyph()
    if glyph is None:
        return
    data = guessConstructionForGlyphName(glyph.name, glyph.layer)
    if data is not None:
        construction = data["construction"]
        decompose = data["decompose"]
        clear = data["clear"]
        LazyBonesGlyphEditorController(
            glyph,
            construction=construction,
            decompose=decompose,
            clear=clear
        )
    else:
        vanilla.dialogs.message(
            "No construction available for %s." % glyph.name,
            "Define one in the preferences so that you can be lazy in the future."
        )

class LazyBonesGlyphEditorController(ezui.WindowController):

    def build(self,
            glyph=None,
            construction=None,
            decompose=True,
            clear=True
        ):
        self.glyph = glyph
        content = """
        [__] @constructionField

        [ ] Clear Outline @clearCheckbox
        [ ] Decompose Components @decomposeCheckbox

        =---=

        (Cancel) @cancelButton
        (Build) @buildButton
        """
        buttonWidth = 80
        descriptionData = dict(
            constructionField=dict(
                value=construction
            ),
            clearCheckbox=dict(
                value=clear
            ),
            decomposeCheckbox=dict(
                value=decompose
            ),
            cancelButton=dict(
                width=buttonWidth,
                keyEquivalent=".",
                keyEquivalentModifiers=["command"]
            ),
            buildButton=dict(
                width=buttonWidth
            )
        )
        self.w = ezui.EZPopUp(
            content=content,
            descriptionData=descriptionData,
            controller=self,
            parent=CurrentGlyphWindow().getGlyphView(),
            size=(350, "auto"),
            defaultButton="buildButton"
        )

    def started(self):
        self.w.open()

    def cancelButtonCallback(self, sender):
        self.w.close()

    def buildButtonCallback(self, sender):
        construction = self.w.getItemValue("constructionField")
        clear = self.w.getItemValue("clearCheckbox")
        decompose = self.w.getItemValue("decomposeCheckbox")
        buildGlyphFromConstruction(
            self.glyph,
            construction=construction,
            clear=clear,
            decompose=decompose
        )
        self.w.close()


# ----
# Font
# ----

def showConstructionsForCurrentFont():
    """
    Show the construction editor for the current font.
    """
    font = CurrentFont()
    if font is None:
        return
    LazyBonesFontSheet(font)

constructionTableCaptionTemplate = "glyphs selected for construction."

class LazyBonesFontSheet(ezui.WindowController):

    def build(self,
            font=None
        ):
        self.font = font
        self.originalConstructions = ConstructionsLoader(font.defaultLayer).constructions
        content = f"""
        |---| @constructionTable
        !- 0 {constructionTableCaptionTemplate} @constructionTableCaption
        =---=
        [ ] Show Existing Glyphs @showExistingGlyphsCheckbox
        (Build In Current Font) @buildButton
        (Build In All Fonts) @buildInAllFontsButton
        (Cancel) @cancelButton
        """
        buttonWidth = 150
        descriptionData = dict(
            constructionTable=dict(
                columnDescriptions = [
                    dict(
                        title="Name",
                        identifier="name",
                        editable=False,
                        width=100
                    ),
                    dict(
                        title="Construction",
                        identifier="construction",
                        editable=True
                    ),
                    dict(
                        title="Decompose",
                        identifier="decompose",
                        editable=True,
                        cellDescription=dict(
                            cellType="Checkbox"
                        ),
                        width=80
                    ),
                    dict(
                        title="Clear",
                        identifier="clear",
                        editable=True,
                        cellDescription=dict(
                            cellType="Checkbox"
                        ),
                        width=80
                    )
                ]
            ),
            constructionTableCaption=dict(
                alignment="center",
                width="fill"
            ),
            showExistingGlyphsCheckbox=dict(
                gravity="leading"
            ),
            cancelButton=dict(
                keyEquivalent=".",
                keyEquivalentModifiers=["command"]
            ),
            buildButton=dict(
                width=buttonWidth
            ),
            buildInAllFontsButton=dict(
                width=buttonWidth
            )
        )
        self.w = ezui.EZSheet(
            content=content,
            descriptionData=descriptionData,
            controller=self,
            parent=CurrentFontWindow().w,
            size=(700, 300),
            defaultButton="buildButton"
        )
        self.populateconstructionTable()

    def started(self):
        self.w.open()

    def showExistingGlyphsCheckboxCallback(self, sender):
        self.populateconstructionTable()

    def cancelButtonCallback(self, sender):
        self.w.close()

    def buildButtonCallback(self, sender):
        fonts = [self.font]
        try:
            self._build(fonts)
        finally:
            self.w.close()

    def buildInAllFontsButtonCallback(self, sender):
        fonts = AllFonts()
        try:
            self._build(fonts)
        finally:
            self.w.close()

    def populateconstructionTable(self):
        skip = []
        if not self.w.getItemValue("showExistingGlyphsCheckbox"):
            for glyph in self.font.defaultLayer:
                if len(glyph) or len(glyph.components):
                    skip.append(glyph.name)
        constructions = [
            deepcopy(value)
            for key, value in sorted(self.originalConstructions.items())
            if key not in skip
        ]
        self.w.setItemValue("constructionTable", constructions)

    def constructionTableSelectionCallback(self, sender):
        count = len(sender.getSelectedIndexes())
        t = constructionTableCaptionTemplate
        if count == 1:
            t = t.replace("glyphs", "glyph")
        self.w.setItemValue(
            "constructionTableCaption",
            str(count) + " " + t
        )

    def _build(self, fonts):
        constructionTable = self.w.getItem("constructionTable")
        selectedConstructions = constructionTable.getSelectedItems()
        if selectedConstructions:
            selectedConstructions = {
                item["name"] : item
                for item in selectedConstructions
            }
            modifiedConstructions = {}
            for name, item in selectedConstructions.items():
                og = self.originalConstructions[name]
                if item != og:
                    modifiedConstructions[name] = item
            progressBar = self.startProgress(
                text="Building...",
                maxValue=len(selectedConstructions) * len(fonts),
                parent=self.w
            )
            try:
                for font in fonts:
                    constructions = {}
                    loader = ConstructionsLoader(font.defaultLayer)
                    for name, data in loader.constructions.items():
                        if name in selectedConstructions:
                            constructions[name] = data
                    for name, data in modifiedConstructions.items():
                        constructions[name] = data
                    for name, data in constructions.items():
                        progressBar.setText(f"Building {name}...")
                        glyph = font.defaultLayer.newGlyph(name, clear=False)
                        buildGlyphFromConstruction(
                            glyph,
                            construction=data["construction"],
                            decompose=data["decompose"],
                            clear=data["clear"]
                        )
                        progressBar.increment()
            finally:
                progressBar.close()

# --------
# Defaults
# --------

def showConstructionDefaults():
    vanilla.dialogs.message("LOL! This doesn't work yet.")

# -------------
# Constructions
# -------------

def guessConstructionForGlyphName(glyphName, layer):
    """
    Guess the construction for the given glyph name
    using the layer for variable calculations.
    """
    construction = guessConstructionsForGlyphNames([glyphName], layer)[glyphName]
    return construction

def guessConstructionsForGlyphNames(glyphNames, layer):
    """
    Guess the constructions for the given glyph names
    using the layer for variable calculations. This will
    return a dictionary of form:

    ```
    {
        "name" : "glyph name",
        "construction" : "construction string",
        "decompose" : boolean,
        "clear" : boolean
    }
    ```
    """
    loader = ConstructionsLoader(layer)
    constructions = {
        glyphName : loader.guessConstructionForGlyphName(glyphName)
        for glyphName in glyphNames
    }
    return constructions


class ConstructionsLoader:

    def __init__(self, layer):

        self.layer = layer
        self.constructions = loadConstructions(layer)

    def guessConstructionForGlyphName(self, name):
        data = None
        if name in self.constructions:
            data = self.constructions[name]
        elif "." in name:
            base, suffix = name.split(".", 1)
            if base in self.constructions:
                data = self.constructions[base]
        return data

def buildGlyphFromConstruction(
        glyph,
        construction,
        clear=True,
        decompose=False
    ):
    """
    Build the glyph with the given construction.
    """
    glyph.prepareUndo("Lazy Bones")
    if clear:
        glyph.clear()
    layer = glyph.layer
    postContructionFunction = None
    if "# >>>" in construction:
        construction, postContructionFunction = construction.split("# >>>")
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
    if postContructionFunction is not None:
        postContructionFunction = postContructionFunction.strip()
        function = postContructionFunctions[postContructionFunction]
        function(glyph)
    glyph.performUndo()

def loadConstructions(layer):
    text = getVariables(layer)
    text += defaultConstructions
    # text += getExtensionDefault(defaultsKey)
    constructions = {}
    for construction in ParseGlyphConstructionListFromString(text):
        if not construction:
            continue
        name, construction = parseGlyphName(construction)
        if name is None:
            continue
        name = name.strip()
        construction = construction.strip()
        decompose = False
        if name.startswith("*"):
            name = name[1:]
            decompose = True
        constructions[name] = dict(
            name=name,
            construction=construction,
            decompose=decompose,
            clear=True
        )
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

# --------------------------
# Post Contruction Functions
# --------------------------

def deleteSmallestContour(glyph):
    smallest = None
    height = None
    for contour in glyph:
        if not contour.bounds:
            continue
        h = contour.bounds[3]
        if height is None:
            height = h
            smallest = contour
            continue
        if h > height:
            height = h
            smallest = contour
    if smallest is not None:
        glyph.removeContour(smallest)

def deleteBottomContour(glyph):
    lowest = None
    bottom = None
    for contour in glyph:
        if not contour.bounds:
            continue
        b = contour.bounds[1]
        if bottom is None:
            bottom = b
            lowest = contour
            continue
        if b < bottom:
            bottom = b
            lowest = contour
    if lowest is not None:
        glyph.removeContour(lowest)

postContructionFunctions = dict(
    deleteSmallestContour=deleteSmallestContour,
    deleteBottomContour=deleteBottomContour
)

# --------
# Defaults
# --------

defaultsKey = "com.typesupply.LazyBones.constructions"

defaultConstructions = """
# ---------
# Uppercase
# ---------

*A = V + H ^ V
*B = R ^ R
*C = G ^ G
*D = E + O ^ O
*E = H ^ H
*F = E ^ E
*G = O ^ O
*H = O ^ O
*I = H & H
*J = I ^ I
*K = H + V ^ H
*L = F ^ F
*M = H ^ H
*N = H ^ H
*O = H
*P = R ^ R
*Q = O ^ O
*R = H ^ H
*S = O ^ O
*T = F ^ F
*U = H ^ H
*V = H ^ H
*W = V & V ^ V, V
*X = V ^ V
*Y = I + V ^ V
*Z = L ^ L
*AE = A & E ^ A, E
Eth = D + hyphen ^ D
Oslash = O + slash @ center, none ^ O
*Thorn = P ^ P
Hbar = H + emdash @ center, none ^ H
IJ = I & J ^ I, J
Lslash = L + hyphen ^ L
*Eng = N + J ^ N
*OE = D & E ^ D', E
Tbar = T + hyphen @ center, none ^ T
Dcroat = Eth ^ Eth

# ---------
# Lowercase
# ---------

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
*germandbls = f & s ^ f, s
*ae = a & e ^ a, e
*eth = o ^ o
*oslash = o + slash @ center, none ^ o
*thorn = p ^ p
dcroat = d + hyphen ^ d
hbar = h + hyphen ^ h
*dotlessi = i ^ i # >>> deleteSmallestContour
*dotlessj = j ^ j # >>> deleteSmallestContour
ij = i & j ^ i, j
lslash = l + hyphen @ center, none ^ l
*eng = n + j ^ n
*oe = o & e ^ o, e
tbar = t + hyphen @ center, none ^ t

# ---------
# Ligatures
# ---------

*f_b = f & b ^ f, b
*f_f = f & f ^ f, f
*f_h = f & h ^ f, h
*f_i = f & i ^ f, i
*f_j = f & j ^ f, j
*f_k = f & k ^ f, k
*f_l = f & l ^ f, l
*f_f_b = f_f & f_b ^ f, b
*f_f_h = f_f & f_h ^ f, h
*f_f_i = f_f & f_i ^ f, i
*f_f_j = f_f & f_j ^ f, j
*f_f_k = f_f & f_k ^ f, k
*f_f_l = f_f & f_l ^ f, l

# -----------
# Punctuation
# -----------

*period = comma ^ comma
*comma = period ^ period
*colon = period + period @ none, xHeight ^ period
*semicolon = comma + colon ^ colon
*exclam = period ^ period
*question = period + two ^ two
exclamdown = exclam @ ~none, ~none ^ exclam', exclam'
questiondown = question @ ~none, ~none ^ question', question'
ellipsis = period & period & period ^ period, period
*periodcentered = colon ^ colon # >>> deleteBottomContour

*hyphen = t ^ t
*endash = hyphen ^ hyphen
*emdash = endash ^ endash
*bullet = hyphen ^ hyphen
*underscore = endash @ none, 0 ^ space

*parenleft = bar ^ bar
parenright = parenleft @ ~none, none ^ parenleft', parenleft'
*bracketleft = parenleft ^ parenleft
bracketright = bracketleft @ ~none, none ^ bracketleft', bracketleft'
*braceleft = bracketleft ^ bracketleft
braceright = braceleft @ ~none, none ^ braceleft', braceleft'

*bar = slash ^ slash
*brokenbar = bar + hyphen ^ bar
*slash = bar ^ bar
backslash = slash @ ~none, none ^ slash', slash'

*asterisk = exclam ^ exclam
*dagger = asterisk ^ asterisk
*daggerdbl = dagger + dagger @ none, ~none ^ dagger
*asciicircum = v @ none, ~capHeight ^ v
*asciitilde = hyphen ^ hyphen

# -------------------
# Letter Like Symbols
# -------------------

*at = d ^ O
*ampersand = zero ^ zero
*section = dollar ^ dollar
*paragraph = P @ ~none, none ^ P', P'
*trademark = T & M ^ T, M
*servicemark = S & trademark ^ S, trademark
*registered = R + O ^ O
*copyright = C + O ^ O
*Pcircle = copyright + P ^ copyright

*ordfeminine = a ^ a
*ordmasculine = o ^ o

# ------
# Quotes
# ------

*quotesingle = exclam ^ exclam
quotedbl = quotesingle & quotesingle ^ quotesingle, quotesingle
*quoteleft = comma @ none, capHeight ^ comma
quoteright = quoteleft @ ~none, ~none ^ quoteleft', quoteleft'
quotedblleft = quoteleft & quoteleft ^ quoteleft, quoteleft
quotedblright = quotedblleft @ ~none, ~none ^ quotedblleft', quotedblleft'
quotesinglbase = quoteright @ none, 0 ^ quoteright
quotedblbase = quotedblright @ none, 0 ^ quotedblright
*guilsinglleft = hyphen ^ hyphen
guilsinglright = guilsinglleft @ ~none, ~none ^ guilsinglleft', guilsinglleft'
guillemotleft = guilsinglleft & guilsinglleft ^ guilsinglleft, guilsinglleft
guillemotright = guillemotleft @ ~none, ~none ^ guillemotleft', guillemotleft'

# -------
# Figures
# -------

*zero = O & o ^ O, o
*one = I & l ^ I, l
*two = S @ ~none, none + L ^ S
*three = C @ ~none, none ^ C
*four = one ^ one
*five = two ^ two
*six = three ^ three
*seven = one ^ one
*eight = three ^ three
*nine = six @ ~none, ~none ^ six', six'

*dollar = S + bar @ center, none ^ S
*cent = c + bar @ center, none ^ c
*sterling = two @ ~none, none ^ two
*yen = Y + equal @ center, none ^ Y
*Euro = C + equal ^ C
*won = W + emdash @ center, none ^ W
*florin = f ^ f

*numbersign = hyphen + slash ^ slash
*percent = zero & slash ^ zero, slash
perthousand = percent & percent ^ percent, percent
*fraction = percent ^ percent

*minus = hyphen ^ hyphen
*plus = minus ^ minus
*plusminus = plus + minus ^ plus
*multiply = plus ^ plus
*divide = plus ^ plus
*equal = minus ^ minus
notequal = equal + slash ^ equal
*approxequal = equal ^ equal
*less = v ^ plus
greater = less @ ~none, none ^ less', less'
*lessequal = less + equal ^ equal
greaterequal = lessequal @ ~none, none ^ lessequal', lessequal'

*degree = o ^ o

# -------
# Accents
# -------

*macron = macron ^ macron
*circumflex = macron ^ macron
*caron = macron ^ macron
*grave = macron ^ macron
*dieresis = macron ^ macron
*acute = macron ^ macron
*breve = macron ^ macron
*dotaccent = macron ^ macron
*ring = macron ^ macron
*ogonek = macron ^ macron
*tilde = macron ^ macron
*cedilla = acute ^ acute
*hungarumlaut = cedilla ^ cedilla
*commaaccent = comma ^ comma
commaaccent.flipped = commaaccent @ ~none, ~none ^ commaaccent
acute.ascender = acute ^ acute
commaaccent.ascender = commaaccent ^ commaaccent

# ------
# Spaces
# ------

*uni2009 = space ^ space * 0.45
*uni00A0 = space
""".strip()

# don't register defaults until more constructions are in place
# registerExtensionDefaults({defaultsKey : defaultConstructions})
