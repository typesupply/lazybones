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
*dotlessi = i ^ i
*dotlessj = j ^ j
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
*periodcentered = colon ^ colon

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
""".strip()

# don't register defaults until more constructions are in place
# registerExtensionDefaults({defaultsKey : defaultConstructions})

if __name__ == "__main__":
    showConstructionForCurrentGlyph()
