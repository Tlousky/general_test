import bpy, bmesh

o  = bpy.context.object
bm = bmesh.from_edit_mesh( o.data )

extreme_verts = []

halfX = o.dimensions.x / 2
halfY = o.dimensions.y / 2

x = [ halfX, halfX * -1 ]
x = [ round( p, 2 ) for p in x ]

y = [ halfY, halfY * -1 ]
y = [ round( p, 2 ) for p in y ]

cast_dims = bpy.context.scene.insole_properties.cast_dimensions

for i,v in enumerate(bm.verts):
    if (round( v.co.x, 2) in x or round( v.co.y ) in y or \
    v.co.x == 0.0 and round( v.co.y ) in y or \
    v.co.y == 0.0 and round( v.co.x ) in x or \
    (v.co.y == 0.0 and v.co.x == 0.0) ) and \
    round( v.co.z, 2 ) == round( cast_dims.z / 2, 2 ):
        extreme_verts.append( i )
        #v.select = True

extremes_set = set( extreme_verts )

for f in bm.faces:
    co = f.calc_center_median()
    fverts = set( [ v.index for v in f.verts ] )
    
    if round( co.z, 2 ) == round( cast_dims.z / 2, 2 ):
        common = fverts & extremes_set
        if len( common ) == 0: f.select = True

bm.select_flush( True )