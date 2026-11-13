from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
f=TTFont('../fonts/Oswald[wght].ttf')
g=instantiateVariableFont(f,{'wght':700},updateFontNames=True)
g.save('fonts/Oswald-Bold-static.ttf')
print([n.toUnicode() for n in g['name'].names if n.nameID in(1,2,4)][:4])
