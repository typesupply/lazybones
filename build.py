# -*- coding: utf8 -*-

from AppKit import *
import os
from mojo.extensions import ExtensionBundle

name = "Lazy Bones"
version = "0.1"
developer = "Type Supply"
developerURL = "http://typesupply.com"
roboFontVersion = "3.2"
pycOnly = False
menuItems = [
    dict(
        path="menu_showForCurrentGlyph.py",
        preferredName="Add To Current Glyph",
        shortKey=(NSCommandKeyMask | NSShiftKeyMask | NSControlKeyMask, "v")
    ),
    dict(
        path="menu_showDefaults.py",
        preferredName="Edit Constructions",
        shortKey=""
    )
]


basePath = os.path.dirname(__file__)
sourcePath = os.path.join(basePath, "source")
libPath = os.path.join(sourcePath, "code")
licensePath = os.path.join(basePath, "license.txt")
requirementsPath = os.path.join(basePath, "requirements.txt")
extensionFile = "%s.roboFontExt" % name
buildPath = os.path.join(basePath, "build")
extensionPath = os.path.join(buildPath, extensionFile)

B = ExtensionBundle()
B.name = name
B.developer = developer
B.developerURL = developerURL
B.version = version
B.launchAtStartUp = False
B.mainScript = "main.py"
B.html = os.path.exists(os.path.join(sourcePath, "documentation", "index.html"))
B.requiresVersionMajor = roboFontVersion.split(".")[0]
B.requiresVersionMinor = roboFontVersion.split(".")[1]
B.addToMenu = menuItems
if os.path.exists(licensePath):
    with open(licensePath) as license:
        B.license = license.read()
if os.path.exists(requirementsPath):
    with open(requirementsPath) as requirements:
        B.requirements = requirements.read()


print("building extension...", end=" ")
v = B.save(extensionPath, libPath=libPath, pycOnly=pycOnly)
print("done!")
print()
print(B.validationErrors())