#!/usr/local/bin/python

"""
This script converts a subset of SVG into an HTML imagemap

Note *subset*.  It only handles <path> elements, for which it only pays
attention to the M and L commands.  Futher, it only notices the "translate"
transform.

It was written to generate the examples in the documentation for maphilight,
and thus is very squarely aimed at handling several SVG maps from wikipedia.
It *assumes* that all the <path>s it will need are inside a <g>.  Any <path>
outside of a <g> will be ignored.

It takes several possible arguments, in the form:
$ svn2imagemap.py FILENAME [x y [group1 group2 ... groupN]]

FILENAME must be the name of an SVG file.  All other arguments are optional.

x and y, if present, are the dimensions of the image you'll be creating from
the SVG.  If not present, it assumes the values of the width and height
attributes in the SVG file.

group1 through groupN are group ids.  If only want particular groups used,
enter their ids here and all others will be ignored.
"""

import os
import re
import sys
import xml.dom.minidom
import math
import string
import parse_path

def toStr(path, width_ratio, height_ratio):
     smoothing = 2.9
     minPixelSize = 8
     minPolygonSides = 4
     ret = '';
     pw_ = 0
     ph_ = 0
     minW = 1000000
     minH = 1000000
     maxW = 0
     maxH = 0
     for p in path:
         pw = p[0]*width_ratio
         ph = p[1]*height_ratio
         # if all of the fields are defined, and there is X difference between at least one value in the coordinate point from the prev
         if (ph is not None and pw is not None and (math.fabs(pw_ - pw) > smoothing or math.fabs(ph_ - ph) > smoothing)):
             if (len(ret) > 0):
                 ret += " , "
             ret += ("%d,%d" % (pw, ph))
             pw_ = pw
             ph_ = ph
             if (pw > maxW):
                 maxW = pw
             if (ph > maxH):
                 maxH = ph
             if (pw < minW):
                 minW = pw
             if (ph < minH):
                 minH = ph

     if (len(string.split(ret,",")) > minPolygonSides*2+1 and ( math.fabs(maxH - minH) > minPixelSize or math.fabs(maxW - minW) > minPixelSize )):
         return ret
     return ""

if len(sys.argv) == 1:
    sys.exit("svn2imagemap.py FILENAME [x y [group1 group2 ... groupN]]")
if not os.path.exists(sys.argv[1]):
    sys.exit("Input file does not exist")
x, y, groups = None, None, None
if len(sys.argv) >= 3:
    x = float(sys.argv[2])
    y = float(sys.argv[3])
    if len(sys.argv) > 3:
        groups = sys.argv[4:]

svg_file = xml.dom.minidom.parse(sys.argv[1])
svg = svg_file.getElementsByTagName('svg')[0]

non_decimal = re.compile(r'[^\d.]+')
make_decimal = lambda x: non_decimal.sub('', x)

raw_width = float(make_decimal(svg.getAttribute('width')))
raw_height = float(make_decimal(svg.getAttribute('height')))
width_ratio = x and (x / raw_width) or 1
height_ratio = y and (y / raw_height) or 1

if groups:
    elements = [g for g in svg.getElementsByTagName('g') if (g.hasAttribute('id') and g.getAttribute('id') in groups)]
    elements.extend([p for p in svg.getElementsByTagName('path') if (p.hasAttribute('id') and p.getAttribute('id') in groups)])
else:
    elements = svg.getElementsByTagName('g')

parsed_groups = {}
for e in elements:
    paths = []
    if e.nodeName == 'g':
        for path in e.getElementsByTagName('path'):
            gelem = path.parentNode
            points = parse_path.get_points(path.getAttribute('d'))
            for pointset in points:
                paths.append([path.getAttribute('id'), pointset, 
                             gelem.getAttribute('title'), gelem.getAttribute('iso'),
                             gelem.getAttribute('alt')])
    else:
        points = parse_path.get_points(e.getAttribute('d'))
        for pointset in points:
            paths.append([e.getAttribute('id'), pointset])
    if e.hasAttribute('transform'):
        print e.getAttribute('id'), e.getAttribute('transform')
        for transform in re.findall(r'(\w+)\((-?\d+.?\d*),(-?\d+.?\d*)\)', e.getAttribute('transform')):
            if transform[0] == 'translate':
                x_shift = float(transform[1])
                y_shift = float(transform[2])
                for path in paths:
                    path[1] = [(p[0] + x_shift, p[1] + y_shift) for p in path[1]]
    
    parsed_groups[e.getAttribute('id')] = paths

out = []
for g in parsed_groups:
    for path in parsed_groups[g]:
        coord = toStr(path[1],width_ratio,height_ratio)
        if (coord != ''):
            out.append('<@renderMap code="%s" coords="%s" title="%s" />' % (path[3],coord,path[2]))

outfile = open(sys.argv[1].replace('.svg', '.html'), 'w')
outfile.write('\n'.join(out))



