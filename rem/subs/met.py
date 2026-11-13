from fontTools.ttLib import TTFont
f=TTFont('fonts/Oswald-Bold-static.ttf');u=f['head'].unitsPerEm
o=f['OS/2'];h=f['hhea']
print(u,o.sCapHeight/u,h.ascent/u,h.descent/u,o.usWinAscent/u,o.usWinDescent/u, 0x401 in f.getBestCmap())
