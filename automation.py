# Author: Tamir Lousky
# Updated: 23Jan2014

bl_info = {    
    "name"        : "Insole 3D Printing",
    "author"      : "Tamir Lousky",
    "version"     : (0, 0, 1),
    "blender"     : (2, 69, 0),
    "category"    : "Object",
    "location"    : "3D View >> Tools",
    "wiki_url"    : "",
    "tracker_url" : "",
    "description" : "Insole preperation automation script"
}

import bpy, bmesh
from mathutils import Color

# Constants
MAX_FACES         = 10000
LENGTH_PERCENTAGE = 0.25

class insole_automation_tools( bpy.types.Panel ):
    bl_idname      = "InsoleAutomationTools"
    bl_label       = "Insole Automation Tools"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    # bl_context     = 'object'

    @classmethod
    def poll( self, context ):
        return True

    def draw( self, context):
        layout = self.layout
        col    = layout.column()

        col.operator( 
            'import_mesh.stl',
            text = 'Import STL file',
            icon = 'IMPORT'
        )

        col.operator( 
            'object.delete_loose',
            text = 'Perform Cleanup',
            icon = 'DRIVER'
        )

        col.operator( 
            'object.decimate_object',
            text = 'Compress model',
            icon = 'MOD_DECIM'
        )

        # Orientation buttons box
        b  = col.box()
        bc = b.column()
        l = bc.label( "Scan orientation buttons" )

        r  = bc.row()        

        r.operator( 
            'object.orient_scan',
            text = 'Front',
            icon = 'AXIS_FRONT'
        ).view = 'FRONT'

        r.operator( 
            'object.orient_scan',
            text = 'Left',
            icon = 'AXIS_SIDE'
        ).view = 'LEFT'

        r.operator( 
            'object.orient_scan',
            text = 'Top',
            icon = 'AXIS_TOP'
        ).view = 'TOP'

        # Center view on object
        r.operator(
            'view3d.view_selected',
            text = 'All',
            icon = 'ALIGN'
        )
        
        b = col.box()
        bc = b.column()
        
        r = bc.row()
        r.operator( 
            'object.flatten_front',
            text = 'Flatten Front',
            icon = 'BRUSH_FLATTEN'
        )
        
        r.operator( 
            'object.preview_flatten',
            text = 'Preview',
            icon = 'PREVIEW_RANGE'
        )        

        r.operator(
            'ed.undo',
            text = 'Undo',
            icon = 'BACK'
        )
        
        bc.prop( context.scene.insole_properties, 'flat_area' )
        bc.prop( context.scene.insole_properties, 'falloff'   )
        
        col.operator( 
            'object.smooth_verts',
            text = 'Smooth object',
            icon = 'MOD_SMOOTH'
        )

        b  = col.box()
        bc = b.column()
        l  = bc.label( "Add outline curve" )
        r  = bc.row()
        
        r.operator( 
            'object.create_and_fit_curve',
            text = 'Right foot',
            icon = 'TRIA_RIGHT'
        ).direction = 'R'

        r.operator( 
            'object.create_and_fit_curve',
            text = 'Left foot',
            icon = 'TRIA_LEFT'
        ).direction = 'L'

        b  = col.box()
        bc = b.column()
        l  = bc.label( "Create Insole" )
        bc.prop( context.scene.insole_properties, 'insole_thickness' )
        bc.operator( 
            'object.create_insole',
            text = 'Create Insole',
            icon = 'MESH_DATA'
        )
        
class delete_loose( bpy.types.Operator ):
    """ Delete vertices not-connected to selected one """
    bl_idname      = "object.delete_loose"
    bl_label       = "Delete unconnected vertices"
    bl_description = "Delete vertices not-connected to selected one"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        """ Deletes all the verts that aren't connected to the selected one """
        o     = bpy.context.object
        props = context.scene.insole_properties
        
        # Go to object mode and set origin to geometry
        if o.mode != 'OBJECT': bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.origin_set( type = 'ORIGIN_GEOMETRY' )

        # Find the closest vert to the origin point
        closest_vert_idx = props.find_nearest_vert( o, o.location )
        
        # Go to edit mode and deselect all verts
        bpy.ops.object.mode_set( mode   = 'EDIT'     )
        bpy.ops.mesh.select_all( action = 'DESELECT' )
        
        # Go to object mode and select closest vert to origin
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        o.data.vertices[ closest_vert_idx ].select = True
        
        # Select all verts linked to this one (on the same island or "loose part")
        bpy.ops.object.mode_set(    mode  = 'EDIT' )
        bpy.ops.mesh.select_linked( limit = False  )
        
        # Selecte inverse (all non-connected verts)
        bpy.ops.mesh.select_all( action = 'INVERT' )
        
        # Delete selected vertices
        bpy.ops.mesh.delete( type = 'VERT' )
        
        # Return to object mode
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        # Clear Location (place object on axis origin)
        bpy.ops.object.location_clear()
        
        return {'FINISHED'}
        
class decimate_object( bpy.types.Operator ):
    """ Uses the decimate modifier to reduce poly count """
    bl_idname      = "object.decimate_object"
    bl_label       = "Reduce poly count"
    bl_description = "Uses the decimate modifier to reduce poly count"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        """ Reduces poly count by creating and applying a decimate modifier """
        ## Create decimate modifier and set its properties
        bpy.ops.object.modifier_add( type='DECIMATE' )
        o = context.object

        # Reference last modifier (the decimate mod we just created)
        decimate = o.modifiers[ len( o.modifiers ) - 1 ]

        # Make sure decimate type is set to "collapse"
        if not decimate.decimate_type == 'COLLAPSE':
            decimate.decimate_type = 'COLLAPSE'
        
        ## Calculate and apply ratio to set max face count
        ratio = MAX_FACES / len(o.data.polygons)
        decimate.ratio = ratio

        ## Apply modifier
        # Make sure we're in object mode
        if o.mode != 'OBJECT': bpy.ops.object.mode_set(mode = 'OBJECT')

        # Apply modifier
        bpy.ops.object.modifier_apply(
            apply_as = 'DATA',
            modifier = decimate.name
        )
        
        return {'FINISHED'}

class orient_scan( bpy.types.Operator ):
    """ Quickly orient insole from top, left or front view """
    bl_idname      = "object.orient_scan"
    bl_label       = "Orient Scan" 
    bl_description = "Quickly orient insole from top, left or front view"
    bl_options     = {'REGISTER', 'UNDO'}

    view = bpy.props.StringProperty()
    
    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        """ Orient from selected view """
        o = context.object

        # Switch to requested angle (Front/Left/Top)
        bpy.ops.view3d.viewnumpad( type = self.view )
        
        # Find 3D_View window and its scren space
        for a in bpy.data.window_managers[0].windows[0].screen.areas:
            if a.type == 'VIEW_3D': 
                area = a
                break

        space = area.spaces[0]

        # Switch to orthographic mode if not already in it
        if space.region_3d.view_perspective != 'ORTHO':
            bpy.ops.view3d.view_persportho()
        
        # Make sure 3D manipulator is displayed
        if not space.show_manipulator:
            space.show_manipulator = True

        # Display rotation manipulator
        if not space.transform_manipulators == {'ROTATE'}:
            space.transform_manipulators = {'ROTATE'}
            
        return {'FINISHED'}
            
class smooth_verts( bpy.types.Operator ):
    """ Smooths all vertices on object """
    bl_idname      = "object.smooth_verts"
    bl_label       = "Smooth object vertices"
    bl_description = "Smooths all vertices on object"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        """ Smooths vertices on object """
        o = context.object

        # Go to edit mode
        if o.mode != 'EDIT': bpy.ops.object.mode_set(mode = 'EDIT')

        bm = bmesh.from_edit_mesh(o.data) # Create BMESH from mesh
        
        # Go to vertex selection mode
        bpy.ops.mesh.select_mode(type='VERT')
        
        # Select all vertices
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Run Smooth for 15 iterations
        bpy.ops.mesh.vertices_smooth( repeat = 15 )

        # Back to object mode
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        return {'FINISHED'}
        
class flatten_front( bpy.types.Operator ):
    """ Flatten the front (toe) area of the foot """
    bl_idname      = "object.flatten_front"
    bl_label       = "Flatten front of foot"
    bl_description = "Flattens the front of the foot with a smooth transition"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        """ Smooths vertices on object """
        o     = context.object        
        props = context.scene.insole_properties
        
        # To perform flattenning:

        # 1. Go to edit mode and create bmesh object
        if o.mode != 'EDIT': bpy.ops.object.mode_set(mode = 'EDIT')
        bm = bmesh.from_edit_mesh( o.data )

        # Select flat area verts (as defined by flat area property)
        idx = props.select_area( context, 'flat' )
        
        # 5. Activate proportional editing tool.
        context.scene.tool_settings.proportional_edit = 'ENABLED'
        
        # 6. Set proportional size
        context.scene.tool_settings.proportional_size = \
            o.dimensions.y * props.falloff

        # 7. Scale all selected verts to 0 on Z axis.
        bpy.ops.transform.resize(
            value                     = (1, 1, 0), 
            constraint_axis           = (False, False, True), 
            proportional              = 'ENABLED', 
            proportional_edit_falloff = 'SMOOTH',
            proportional_size         = o.dimensions.y * props.falloff
        )

        # 8. Move verts down the Z axis until flat (as high as lowset vert)

        # Find lowest vert
        min_z = 1000
        idx2  = -1

        for v in bm.verts:
            if v.co.z < min_z:
                min_z = v.co.z
                idx2  = v.index

        if idx2 == -1: return {'FAILED'}
        
        # Find current Z value of flat verts
        avg_z = bm.verts[ idx ].co.z # top-y vert is of the same Z as all flats

        translate_distance = min_z - avg_z
        
        bpy.ops.transform.translate(
            value                     = (0, 0, translate_distance), 
            constraint_axis           = (False, False, True), 
            proportional              = 'ENABLED', 
            proportional_edit_falloff = 'SMOOTH',
            proportional_size         = o.dimensions.y * props.falloff
        )        
        
        # 9. Deactivate proportional editing tool.
        context.scene.tool_settings.proportional_edit = 'DISABLED'

        # 10. Go back to object mode.
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        return {'FINISHED'}

class preview_flatten( bpy.types.Operator ):
    """ Flatten the front (toe) area of the foot """
    bl_idname      = "object.preview_flatten"
    bl_label       = "Preview flatenning"
    bl_description = "Preview the flatenning of the insole's front area"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        context.scene.insole_properties.update_materials( context )
        return {'FINISHED'}

class create_and_fit_curve( bpy.types.Operator ):
    """ Creates a curve outline of the final insole shape, and adds some easy
        adjust hooks to fix the shape and fine-tune it
    """

    bl_idname      = "object.create_and_fit_curve" 
    bl_label       = "Create insole outline"
    bl_description = "Create an outline curve"
    bl_options     = {'REGISTER', 'UNDO'}

    direction = bpy.props.StringProperty()
    
    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def make_curve( self, context, name, cList, scan_obj ):  
        ''' Create curve from list of coordinates and adjust its dimensions
            to fit those of provided object reference 'scan_obj'
        '''

        # Create reference by name to make obj reference persistent
        scan_obj = context.scene.objects[ scan_obj.name ]

        curve = bpy.data.curves.new( name = name, type='CURVE' )
        curve.dimensions = '3D'  
     
        o = bpy.data.objects.new(name, curve)
        o.location = (0,0,0) # place at object origin
        context.scene.objects.link( o )
      
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
            
        return o

    def find_window_space( self, context ):
        # Find 3D_View window and its scren space
        for a in bpy.data.window_managers[0].windows[0].screen.areas:
            if a.type == 'VIEW_3D': 
                area = a
                break
        space = area.spaces[0]
        
        return space
        
    def set_view( self, context ):
        ''' Go to top view and activate rotation manipulator '''

        # Switch to Top view
        bpy.ops.view3d.viewnumpad( type = 'TOP' )
        
        space = self.find_window_space( context )

        # Switch to orthographic mode if not already in it
        if space.region_3d.view_perspective != 'ORTHO':
            bpy.ops.view3d.view_persportho()
        
        # Make sure 3D manipulator is displayed
        if not space.show_manipulator:
            space.show_manipulator = True

        # Display rotation manipulator
        if not space.transform_manipulators == {'ROTATE'}:
            space.transform_manipulators = {'ROTATE'}

    def create_hooks( self, context, o ):
        ''' Create a hook for each bezier point on curve '''

        # Select by name to make reference persistent
        o = context.scene.objects[ o.name ] 
        
        # Select curve
        bpy.ops.object.select_all( action = 'DESELECT' ) # deselect all
        o.select = True                   # Select curve
        context.scene.objects.active = o  # Make it the active object

        hooks = []
        # Iterate over points on curve 
        for i in range( len( o.data.splines[0].bezier_points ) ):
            # Go to edit mode
            if o.mode != 'EDIT': bpy.ops.object.mode_set(mode = 'EDIT')
        
            # Select point
            bpy.ops.curve.select_all( action = 'DESELECT' )
            p = o.data.splines[0].bezier_points[ i ]
            p.select_control_point = True

            # Snap cursor to selected point
            bpy.ops.view3d.snap_cursor_to_selected()

            # Go to object mode
            bpy.ops.object.mode_set(mode = 'OBJECT')

            # Create spherical empty and set a reasonable draw size
            bpy.ops.object.empty_add( type = 'SPHERE' )

            empties = [ 
                e.name for e in context.scene.objects if 'Empty' in e.name 
            ]
            empties.sort()

            empty = context.scene.objects[ empties[-1] ]
            empty.empty_draw_size = 10
            
            hooks.append( empties[-1] )

            # Select both empty (first), then curve
            bpy.ops.object.select_all( action = 'DESELECT' ) # deselect all
            empty.select = True
            o.select     = True
            context.scene.objects.active = o
            
            # Go to edit mode
            bpy.ops.object.mode_set(mode = 'EDIT')
            
            # Create hook modifier for the selected point
            bpy.ops.curve.select_all( action = 'DESELECT' )
            p = o.data.splines[0].bezier_points[ i ]
            p.select_control_point = True
            p.select_left_handle   = True
            p.select_right_handle  = True
            
            bpy.ops.object.hook_add_selob()

        # Go to object mode
        bpy.ops.object.mode_set(mode = 'OBJECT')            

        # Parent all empties to curve
        bpy.ops.object.select_all( action = 'DESELECT' ) # deselect all
        for h in hooks: 
            context.scene.objects[ h ].select = True
        o.select = True
            
        bpy.ops.object.parent_set( type = 'OBJECT', keep_transform = True )

        bpy.ops.object.select_all( action = 'DESELECT' ) # deselect all
        o.select = True

        # Set manipulator to transform
        space = self.find_window_space( context )
        if not space.transform_manipulators == {'ROTATE'}:
            space.transform_manipulators = {'ROTATE'}
            
    def execute( self, context ):
        """ Create curve and fit it to foot scan """
        o     = context.scene.objects[ context.object.name ]
        props = context.scene.insole_properties
        name  = 'insole_curve.' + self.direction
        
        # 1. create curve
        curve = self.make_curve( 
            context, name, right_foot_insole_curve_coordinates, o 
        ) 

        bpy.ops.object.select_all( action = 'DESELECT' )
        curve.select = True                   # Select curve
        context.scene.objects.active = curve  # Make it the active object
   
        # Equate the dimensions of the curve to the scanned insole object
        curve.dimensions = ( o.dimensions.x, o.dimensions.y, 0 )

        # Curve is right foot by default. To get left foot, we must flip it.
        if self.direction == 'L':
            bpy.ops.transform.resize( value = (-1,1,1) ) # Flip in X axis

        # Apply transformations on curve and scan
        for obj in o, curve:
            bpy.ops.object.select_all( action = 'DESELECT' ) # deselect all
            obj.select = True                   # Select object
            context.scene.objects.active = obj  # Make it the active object

            # Apply transformations
            bpy.ops.object.transform_apply( 
                location = True, 
                rotation = True, 
                scale    = True 
            )
            
        # Find heighest vertex and rearmost vertex on scan
        scan_coos = [ v.co * o.matrix_world for v in o.data.vertices ]
        scan_zs = [ c.z for c in scan_coos ]
        scan_ys = [ c.y for c in scan_coos ]
        scan_zs.sort()
        scan_ys.sort()
        
        smallest_y = scan_ys[0]
        heighest_z = scan_zs[-1]
                 
        # Make sure Z location is above scan object
        curve.location.z = heighest_z
        
        # Find rearmost point on curve
        smallest_y_curve = 10000
        for p in curve.data.splines[0].bezier_points:
            global_co = p.co * curve.matrix_world
            if global_co.y < smallest_y:
                smallest_y_curve = global_co.y
        
        diff = smallest_y - smallest_y_curve
       
        # Move curve on y axis so that rear points will match
        bpy.ops.transform.translate( value = (0, diff, 0) )

        self.set_view( context ) # Top view to adjust curve rotation
        
        # Create hooks on each of the curve's points
        self.create_hooks( context, curve )
        
        return {'FINISHED'}

class create_insole_from_curve( bpy.types.Operator ):
    """ Create mesh insole object from curve and scan """
    bl_idname      = "object.create_insole"
    bl_label       = "Create Insole"
    bl_description = "Create Insole from Scan and Outline"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        props = context.scene.insole_properties
        scn   = context.scene
        cname = [ o.name for o in scn.objects if 'insole_curve' in o.name ].pop()
        c     = context.scene.objects[ cname ] # Create reference by object name
        
        # Select curve object and set it as active
        bpy.ops.object.select_all( action = 'DESELECT' )
        c.select = True        # Select curve
        scn.objects.active = c # Set curve as active object

        # Apply modifiers on curve        
        for m in c.modifiers: 
            bpy.ops.object.modifier_apply( modifier = m.name )

        # Delete all type = 'EMPTY' objects
        bpy.ops.object.select_all( action = 'DESELECT' )
        for e in [ e for e in scn.objects if e.type == 'EMPTY' ]:
            e.select = True        # Select empty
        bpy.ops.object.delete()    # Delete selected objects

        # Select curve object and set it as active
        bpy.ops.object.select_all( action = 'DESELECT' )
        c.select = True        # Select curve
        scn.objects.active = c # Set curve as active object

        # Reference scan object
        scan = [ o for o in scn.objects if o.type == 'MESH' ].pop()
        
        # Convert curve to mesh
        bpy.ops.object.convert( target = 'MESH' )

        # Go to edit mode, vertex selection mode and select all verts 
        bpy.ops.object.mode_set( mode   = 'EDIT'   )
        bpy.ops.mesh.select_mode( type  = 'VERT'   )
        bpy.ops.mesh.select_all( action = 'SELECT' )
        
        # Perform grid fill
        bpy.ops.mesh.fill_grid()

        # Extrude down on z to bottom of scan + insole_thickness
        coos   = [ c.co * scan.matrix_world for c in scan.data.vertices ]
        z_coos = [ c.z for c in coos ]
        z_coos.sort()
        lowest_z  = z_coos[0]
        extrude_z = ( c.location.z - lowest_z + props.insole_thickness ) * -1
        
        bpy.ops.mesh.extrude_region_move( 
            TRANSFORM_OT_translate={"value":(0, 0, extrude_z )} 
        )
        
        # Go to object mode
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        
        # Create boolean modifier with correct settings
        # Apply boolean modifier and delete (or hide) other object

        return {'FINISHED'}
        
class insole_props( bpy.types.PropertyGroup ):
    def find_nearest_vert( self, obj, point):
        """ Find the closest vert on the mesh to provided point """

        closest_vert      = -1
        smallest_distance = 10000

        for v in obj.data.vertices:
            pt1 = v.co * obj.matrix_world # convert to global coordinates
            pt2 = point
            distance = \
                abs(pt1.x - pt2.x) + abs(pt1.y - pt2.y) + abs(pt1.z - pt2.z)

            if distance < smallest_distance:
                smallest_distance = distance
                closest_vert      = v.index
            
        return closest_vert

    def select_area( self, context, area_type = 'flat', mat_idx = -1 ):
        ''' Select the flat area as defined by the % in the flat area property '''

        o     = context.object
        props = context.scene.insole_properties

        # 1. Go to edit mode and create bmesh object
        if o.mode != 'EDIT': bpy.ops.object.mode_set(mode = 'EDIT')
        bm = bmesh.from_edit_mesh( o.data )
        
        # 2. Find the vertex with the highest Y value
        max_y = -10000
        idx   = -1
        for v in bm.verts:
            if v.co.y > max_y:
                max_y = v.co.y
                idx   = v.index

        if idx == -1: return {'FAILED'}
                
        # 3. Store y dimensions of insole. Find 25% of this value. flat_dist.
        flat_dist = o.dimensions.y * props.flat_area
        mid_size  = o.dimensions.y * props.falloff / 2
        
        # 4. Select all vertices that are up to flat_dist from top-y vert.
        flat_y = bm.verts[idx].co.y - flat_dist
        mid_y  = flat_y - mid_size

        
        # Go to vertex selection mode and deselect all verts
        bpy.ops.mesh.select_mode( type   = 'VERT'     )
        bpy.ops.mesh.select_all(  action = 'DESELECT' )
        
        # Select all vertices located above minimum Y value
        orig_verts = mid_verts = flat_verts = 0
        if area_type == 'flat':
            for v in bm.verts:
                if v.co.y > flat_y: 
                    v.select = True
                    flat_verts += 1
        elif area_type == 'mid':
            for v in bm.verts:
                if v.co.y < flat_y and v.co.y > mid_y: 
                    v.select = True
                    mid_verts += 1
        else: # Select all unchanged ('orig') vertices
            for v in bm.verts:
                if v.co.y < mid_y: 
                    v.select = True
                    orig_verts += 1
        
        # Paint verts if material slot index provided
        # TODO: move this back to update_materials
        if mat_idx != -1:
            o.active_material_index = mat_idx
            bpy.ops.object.mode_set(mode ='OBJECT')
            bpy.ops.object.mode_set(mode ='EDIT')
            bpy.ops.object.material_slot_assign()
        
        return idx

    def update_materials( self, context ):
        ''' Update visual preview of flattenning effect '''

        o = context.object

        materials = {
            'flat' : 'flat_front_insole.mat',
            'mid'  : 'transition_insole.mat',
            'orig' : 'unchanged_insole.mat'
        }

        colors = { 
            'flat' : Color( ( 1.0, 0.0, 0.0 ) ), # Pure red
            'mid'  : Color( ( 0.5, 0.25, 0  ) ), # Yellow
            'orig' : Color( ( 0.0, 0.0, 1.0 ) )  # Pure blue
        }

        # First make sure all 3 materials exist in file data
        mat_refs = {}
        for m in materials:
            if materials[ m ] not in bpy.data.materials.keys():
                bpy.ops.material.new()

                # Find last material
                last_new_mat   = ''
                for k in bpy.data.materials.keys():
                    if 'Material' in k and k > last_new_mat: last_new_mat = k

                mat               = bpy.data.materials[ last_new_mat ]
                mat.name          = materials[ m ]
                mat.diffuse_color = colors[ m ]
                mat.use_shadeless = True
                mat_refs[ m ] = mat # Create reference in dictionary
            else:
                mat_refs[ m ] = bpy.data.materials[ materials[ m ] ]

        bpy.ops.object.mode_set(mode ='OBJECT')

        for m in mat_refs:
            # Find current material's index in active object's material slots
            mi = -1 # Value if material not found on object
            for i, ms in enumerate( o.material_slots ):
                if ms.material and ms.material.name == mat_refs[ m ].name:
                    mi = i
            if mi == -1:
                # Check if there's an empty slot
                slot = empty_slot = False
                for ms in o.material_slots:
                    if not ms.material:
                        slot = empty_slot = ms
                        break

                if not empty_slot: # No empty slot? then add a slot
                    bpy.ops.object.material_slot_add()
                    slot = o.material_slots[-1]

                # Assign material to slot
                slot.material = mat_refs[ m ]
                for i, ms in enumerate( o.material_slots ):
                    if ms.material and ms.material.name == mat_refs[ m ].name:
                        mi = i
                
            self.select_area( context, m, mi ) # Select current area's vertices
            
        bpy.ops.object.mode_set(mode ='OBJECT')

    flat_area = bpy.props.FloatProperty(
        description = "Percentage of scan to be flattened, from front to back",
        name        = "Flat Area",
        subtype     = 'FACTOR',
        default     = 0.25,
        min         = 0.0,
        max         = 1.0,
        update      = update_materials
    )

    falloff = bpy.props.FloatProperty(
        description = "Falloff area of flattenning tool",
        name        = "Flat Falloff",
        subtype     = 'FACTOR',
        default     = 0.25,
        min         = 0.0,
        max         = 1.0,
        update      = update_materials
    )
    
    insole_thickness = bpy.props.FloatProperty(
        description = "Insole thickness",
        name        = "Insole thickness",
        subtype     = 'FACTOR',
        default     = 10,
        min         = 0.0,
        max         = 100.0
    )

right_foot_insole_curve_coordinates = [
  {
    "point": [ -0.6314261555671692, -0.3624125123023987, 0 ], 
    "lh": {
      "co"   : [ -0.3986741602420807, -1.1438326835632324, 0 ], 
      "type" : "ALIGNED"
    }, 
    "rh": {
      "co"   : [ -1.147887945175171, 1.3715088367462158, 0 ],
      "type" : "ALIGNED"
    }
  }, 
  {
    "point": [ -0.31932520866394043, 2.391295909881592, 0 ], 
    "lh": {
      "co"   : [ -1.2208094596862793, 2.3732688426971436, 0 ], 
      "type" : "ALIGNED"
    }, 
    "rh": {
      "co"   : [ 0.6398943662643433, 2.41047739982605, 0 ], 
      "type" : "ALIGNED"
    }
  }, 
  {
    "point": [ 0.8148716688156128, -0.5427557229995728, 0 ], 
    "lh": {
      "co"   : [ 1.027264952659607, 0.9133864641189575, 0 ], 
      "type" : "FREE"
    }, 
    "rh": {
      "co"   : [ 0.6966830492019653, -1.7818933725357056, 0 ], 
      "type" : "FREE"
    }
  }, 
  {
    "point": [ -0.15875260531902313, -2.6983823776245117, 0 ], 
    "lh": {
      "co"   : [ 0.8510141968727112, -2.9746973514556885, 0 ], 
      "type" : "ALIGNED"
    }, 
    "rh": {
      "co"   : [ -0.7176949977874756, -2.5454320907592773, 0 ], 
      "type" : "ALIGNED"
    }
  }
]
    
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.insole_properties = bpy.props.PointerProperty( 
        type = insole_props
    )

def unregister():
    bpy.utils.unregister_module(__name__)