import bpy  
from mathutils import Vector  
  
w = 1 # weight  
coos = [
  {
    "point": [
      -0.6314261555671692, 
      -0.3624125123023987, 
      -4.673041398284283e-10
    ], 
    "lh": {
      "co": [
        -0.3986741602420807, 
        -1.1438326835632324, 
        -6.253572104597538e-10
      ], 
      "type": "ALIGNED"
    }, 
    "rh": {
      "co": [
        -1.147887945175171, 
        1.3715088367462158, 
        -1.165944840675337e-10
      ], 
      "type": "ALIGNED"
    }
  }, 
  {
    "point": [
      -0.31932520866394043, 
      2.391295909881592, 
      -8.734858392145384e-10
    ], 
    "lh": {
      "co": [
        -1.2208094596862793, 
        2.3732688426971436, 
        -1.169804919598505e-09
      ], 
      "type": "ALIGNED"
    }, 
    "rh": {
      "co": [
        0.6398943662643433, 
        2.41047739982605, 
        -5.581890505368392e-10
      ], 
      "type": "ALIGNED"
    }
  }, 
  {
    "point": [
      0.8148716688156128, 
      -0.5427557229995728, 
      9.881843121561928e-10
    ], 
    "lh": {
      "co": [
        1.027264952659607, 
        0.9133864641189575, 
        6.970223287439126e-10
      ], 
      "type": "FREE"
    }, 
    "rh": {
      "co": [
        0.6966830492019653, 
        -1.7818933725357056, 
        9.881843121561928e-10
      ], 
      "type": "FREE"
    }
  }, 
  {
    "point": [
      -0.15875260531902313, 
      -2.6983823776245117, 
      1.64697394611224e-10
    ], 
    "lh": {
      "co": [
        0.8510141968727112, 
        -2.9746973514556885, 
        4.517951346372229e-09
      ], 
      "type": "ALIGNED"
    }, 
    "rh": {
      "co": [
        -0.7176949977874756, 
        -2.5454320907592773, 
        -2.2449857528528128e-09
      ], 
      "type": "ALIGNED"
    }
  }
]

name = 'insole_curve.L'
  
def make_curve( name, cList, scan_obj ):  
    curve = bpy.data.curves.new(name=name, type='CURVE')  
    curve.dimensions = '3D'  
  
    o = bpy.data.objects.new(name, curve)
    o.location = (0,0,0) # place at object origin
    bpy.context.scene.objects.link( o )
  
    polyline = curve.splines.new('BEZIER')  
    polyline.bezier_points.add(len(cList)-1)
    polyline.use_cyclic_u = True

    for num in range(len(cList)):  
        # Set point coordinates
        polyline.bezier_points[num].co = cList[num]['point']

        # Set handles
        p = polyline.bezier_points[num]
        p.handle_left       = cList[num]['lh']['co']
        p.handle_left_type  = cList[num]['lh']['type']
        p.handle_right      = cList[num]['rh']['co']
        p.handle_right_type = cList[num]['rh']['type']
        
    # Equate the dimensions of the curve to the scanned insole object
    o.dimensions = scan_obj.dimensions

MakePolyLine(name, name, coos)