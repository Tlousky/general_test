import bpy, json

def encode_bezier_curve( obj ):
    spline = obj.data.splines[0] # Assume 1 spline per object
    
    points = []
    
    for bp in spline.bezier_points:
        points.append({
            'point' : list( bp.co ),
            'lh'    : {
                'co'   : list( bp.handle_left ),
                'type' : bp.handle_left_type
            },
            'rh'    : {
                'co'   : list( bp.handle_right ),
                'type' : bp.handle_right_type
            }
        })

    textblock = obj.name + '_ecoded_points'
    if not textblock in bpy.data.texts.keys():
        bpy.data.texts.new( textblock )

    bpy.data.texts[ textblock ].clear() # Clear text block
        
    bpy.data.texts[ textblock ].write(  # Write curve data to text block
        json.dumps( points, indent = 2 )
    )
    
encode_bezier_curve( bpy.context.object )