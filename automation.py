# Author: Tamir Lousky

bl_info = {    
    "name"        : "Insole 3D Printing",
    "author"      : "Tamir Lousky",
    "version"     : (0, 0, 2),
    "blender"     : (2, 69, 0),
    "category"    : "Object",
    "location"    : "3D View >> Tools",
    "wiki_url"    : "",
    "tracker_url" : "",
    "description" : "Insole preperation automation script"
}

import bpy, bmesh, json, math
from mathutils    import Color

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

        # File Imports
        b = col.box()
        bc = b.column()
        
        r = bc.row()

        # Import STL
        r.operator(
            'object.import_insole_stl',
            text = 'Import STL file',
            icon = 'IMPORT'
        )

        # Import OBJ
        r.operator(
            'import_scene.obj',
            text = 'Import OBJ file',
            icon = 'IMPORT'
        )

        # Cleanups
        b = col.box()
        bc = b.column()
               
        # Reduce polycount
        r = bc.row()
        r.operator( 
            'object.decimate_object',
            text = 'Compress model',
            icon = 'MOD_DECIM'
        )

        r.prop( context.scene.insole_properties, 'decimate_faces' )
        
        # Clean mesh
        r = bc.row()
        r.operator( 
            'object.perform_cleanup',
            text = 'Perform Cleanup',
            icon = 'DRIVER'
        )

        # Clear materials
        r.operator( 
            'object.clear_materials',
            text = 'Clear materials',
            icon = 'MATERIAL'
        )

        # Orientation buttons box
        b  = col.box()
        bc = b.column()
        l = bc.label( "Scan orientation" )

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

        # Twist correction props and operators
        b  = col.box()
        bc = b.column()
        l  = bc.label( "Fix twisted foot areas" )
       
        bc.prop( context.scene.insole_properties, 'twist_area' )
        
        ta = context.scene.insole_properties.twist_area
        r  = bc.row()
        
        if ta == 'Front':
            r.prop( context.scene.insole_properties, 'flat_area'          )
            r.prop( context.scene.insole_properties, 'falloff'            )
        else:
            r.prop( context.scene.insole_properties, 'heel_area'          )
            r.prop( context.scene.insole_properties, 'heel_twist_falloff' )
        
        bc.prop( context.scene.insole_properties, 'twist_angle' )
        
        # Flatten Front props and operators
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

        r = col.row()        
        r.operator( 
            'object.smooth_verts',
            text = 'Smooth',
            icon = 'MOD_SMOOTH'
        )

        r.operator( 
            'object.fill_insole_holes',
            text = 'Fill holes',
            icon = 'MESH_CIRCLE'
        )

        r.operator( 
            'object.quick_remove_excess',
            text = 'Remove excess',
            icon = 'BORDER_LASSO'
        )
        
        # Create curves and Trim Insole
        b  = col.box()
        bc = b.column()
        l  = bc.label( "Add outline curve" )
        r  = bc.row()

        r.operator( 
            'object.create_and_fit_curve',
            text = 'Left foot',
            icon = 'LOOP_BACK'
        ).direction = 'L'
        
        r.operator( 
            'object.create_and_fit_curve',
            text = 'Right foot',
            icon = 'LOOP_FORWARDS'
        ).direction = 'R'

        r  = bc.row()        
        r.operator( 
            'object.trim_insole',
            text = 'Trim Insole',
            icon = 'CURVE_DATA'
        )

        r.operator(
            'ed.undo',
            text = 'Undo',
            icon = 'BACK'
        )
        
        # Final Insole creation params and operators
        b  = col.box()
        bc = b.column()

        bc.label( "Create finished Insole" )
        r = bc.row()

        r.operator( 
            'object.create_insole',
            text = 'Create Insole',
            icon = 'PARTICLES'
        )

        r.prop( context.scene.insole_properties, 'insole_thickness' )
        
        r = bc.row()
        r.operator( 
            'export_mesh.stl',
            text = 'Save',
            icon = 'SAVE_AS'
        )

        r.operator(
            'ed.undo',
            text = 'Undo',
            icon = 'BACK'
        )

        # Create Cast
        s = col.separator()
        b  = col.box()
        bc = b.column()

        bc.label( "Create CNC cast from two Insoles" )

        # Cast block dimensions
        bc.prop( context.scene.insole_properties, 'cast_dimensions' )
        
        # Create cast operator
        bc.operator(
            'object.create_insole_cast',
            text = 'Create CNC Cast',
            icon = 'MOD_CAST'
        )

        
class import_insole_stl( bpy.types.Operator ):
    """ Import insole STL file and perform preliminary cleanup and adjustments """
    bl_idname      = "object.import_insole_stl"
    bl_label       = "Import STL"
    bl_description = "Import foot scan STL file and prepare preliminary mesh"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        return True # Always available

    def execute( self, context ):
        """ Launch import STL command, then run preperations and adjust view """
        props = context.scene.insole_properties

        # bpy.ops.import_mesh.stl( 'INVOKE_DEFAULT'  ) # Open file import dialog
        
        o = bpy.context.object
        
        # After import, the imported mesh becomes selected and active
        # 1. Move origin to geometry
        if o.mode != 'OBJECT': bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.origin_set( type = 'ORIGIN_GEOMETRY' )

        # 2. Clear transformation
        bpy.ops.object.location_clear()

        # 3. Center view
        bpy.ops.view3d.view_selected()

        # 4. Launch cleanup operator
        bpy.ops.object.perform_cleanup()    

        return {'FINISHED'}

    def invoke( self, context, event ):
        options = (
            'INVOKE_DEFAULT', 
            'INVOKE_REGION_WIN', 
            'INVOKE_REGION_CHANNELS', 
            'INVOKE_REGION_PREVIEW', 
            'INVOKE_AREA', 
            'INVOKE_SCREEN', 
            'EXEC_DEFAULT', 
            'EXEC_REGION_WIN', 
            'EXEC_REGION_CHANNELS', 
            'EXEC_REGION_PREVIEW', 
            'EXEC_AREA', 
            'EXEC_SCREEN'
        )

        bpy.ops.import_mesh.stl( 'INVOKE_DEFAULT'  ) # Open stl import dialog
        
        # self.execute( context )
        
        return {'RUNNING_MODAL'}

class perform_cleanup( bpy.types.Operator ):
    """ Delete vertices not-connected to selected one """
    bl_idname      = "object.perform_cleanup"
    bl_label       = "Perform Cleanup"
    bl_description = "Perform various cleanups and corrections"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

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
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def execute( self, context ):
        """ Reduces poly count by creating and applying a decimate modifier """
        ## Create decimate modifier and set its properties
        bpy.ops.object.modifier_add( type='DECIMATE' )
        o     = context.object
        props = context.scene.insole_properties
        
        # Reference last modifier (the decimate mod we just created)
        decimate = o.modifiers[ len( o.modifiers ) - 1 ]

        # Make sure decimate type is set to "collapse"
        if not decimate.decimate_type == 'COLLAPSE':
            decimate.decimate_type = 'COLLAPSE'
        
        ## Calculate and apply ratio to set max face count
        ratio = props.decimate_faces / len(o.data.polygons)
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
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

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
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

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
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def execute( self, context ):
        """ Smooths vertices on object """
        o     = context.object        
        props = context.scene.insole_properties
        
        # Apply transformations to avoid weird issues with operator
        bpy.ops.object.transform_apply( 
            location = True, 
            rotation = True, 
            scale    = True 
        )

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
 
        # 11. Perform cleanup post flattenning
        bpy.ops.object.perform_cleanup()
 
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
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def execute( self, context ):
        context.scene.insole_properties.update_materials( context )
        return {'FINISHED'}

class clear_materials( bpy.types.Operator ):
    """ Clear all materials assigned to active object """
    bl_idname      = "object.clear_materials"
    bl_label       = "Clear materials"
    bl_description = "Clear all materials assigned to object"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def execute( self, context ):
        for i in range( len( context.object.material_slots ) ):
            bpy.ops.object.material_slot_remove()

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
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

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

        bpy.ops.object.clear_materials()

        # Add hooks to front of mesh using the operator
        bpy.ops.object.create_front_controls()
        
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

class create_front_controls( bpy.types.Operator ):
    """ Create empties for easy control over front """
    bl_idname      = "object.create_front_controls"
    bl_label       = "Create Front Controls"
    bl_description = "Create controls for easy tranformation of front"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def create_lattice( self, context ):
        obj   = context.scene.objects[ context.object.name ]
        props = context.scene.insole_properties

        bpy.ops.view3d.snap_cursor_to_center()
        
        # Create lattice
        bpy.ops.object.add( type='LATTICE' )
        
        lattice = context.scene.objects[ context.object.name ]

        # Scale to insole object's dimensions
        lattice.scale = obj.dimensions

        # Find rearmost point of lattice
        rear = 10000
        pidx = -1
        for i,p in enumerate( lattice.data.points ):
            co = p.co * lattice.matrix_world
            if co.y < rear: 
                rear = co.y
                pidx = i
            
        # Find distance between it and the rearmost point on the insole
        bpy.ops.object.select_all( action = 'DESELECT' )
        obj.select = True
        context.scene.objects.active = obj

        idx          = props.select_area( context, 'heel' )
        rear_vert_co = obj.data.vertices[ idx ].co * obj.matrix_world
        
        lattice_rear_co = lattice.data.points[ pidx ].co * lattice.matrix_world
        diff = rear_vert_co.y - lattice_rear_co.y
       
        # Translate lattice to fit position of rearmost point on insole
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        bpy.ops.object.select_all( action = 'DESELECT' )
        lattice.select = True
        context.scene.objects.active = lattice

        bpy.ops.transform.translate(
            value            = ( 0, diff, 0 ), 
            constraint_axis  = ( False, True, False )
        )
        
        # Divide lattice 
        lattice.data.points_u = 3
        lattice.data.points_v = 4
        lattice.data.points_w = 2
        
        # Remove inner lattice points
        lattice.data.use_outside = True

        # Add lattice modifier to insole
        bpy.ops.object.select_all( action = 'DESELECT' )
        obj.select = True
        context.scene.objects.active = obj
        
        bpy.ops.object.modifier_add( type = 'LATTICE' )
        
        # Bind lattice modifier to created lattice
        obj.modifiers[-1].object = lattice
        
        return obj, lattice

    def select_lattice( self, context, lattice ):
        ''' Select lattice object '''

        bpy.ops.object.mode_set( mode = 'OBJECT' )
        bpy.ops.object.select_all( action = 'DESELECT' )
        lattice.select = True
        context.scene.objects.active = lattice        

    def select_lattice_points( self, context, lattice, cat ):
        ''' Select the points of the provided category
            ( front-center / front-left / front-right )
        '''

        # Go to edit mode
        bpy.ops.object.mode_set( mode = 'EDIT' )
        
        # Deselect all lattice points
        bpy.ops.lattice.select_all( action = 'DESELECT' )
        
        if cat == 'center':
            lattice.data.points[10].select = True
            lattice.data.points[22].select = True
        if cat == 'right':
            lattice.data.points[11].select = True
            lattice.data.points[23].select = True
        if cat == 'left':
            lattice.data.points[9].select  = True
            lattice.data.points[21].select = True

        '''
        for i,p in enumerate( lattice.data.points ):
            # See if this point as at the front, left, right or center
            front  = p.co.y ==  0.5
            left   = p.co.x == -0.5
            right  = p.co.x ==  0.5
            center = p.co.x ==  0.0
            if front:
                if cat == 'center' and center or \
                   cat == 'right'  and right  or \
                   cat == 'left'   and left:  
                    p.select = True
        '''
                    
    def create_empties( self, context, obj, lattice ):
        self.select_lattice( context, lattice )

        hooks = {}
        for cat in [ 'center', 'right', 'left' ]:
            hook         = self.create_empty( context, lattice, cat )
            hook.name    = cat
            hooks[ cat ] = hook
            
            self.hook_lattice_to_empty( context, hook, lattice, cat )
            
        return hooks

    def create_empty( self, context, lattice, cat ):
        # Select points
        self.select_lattice_points( context, lattice, cat )

        # Move cursor to selected
        bpy.ops.view3d.snap_cursor_to_selected()
        
        bpy.ops.object.mode_set( mode = 'OBJECT' )

        # Create cubic empty and set a reasonable draw size
        bpy.ops.object.empty_add( type = 'CUBE' )

        empties = [ 
            e.name for e in context.scene.objects if 'Empty' in e.name 
        ]
        empties.sort()

        empty = context.scene.objects[ empties[-1] ]
        empty.empty_draw_size = 10

        return empty
        
    def hook_lattice_to_empty( self, context, empty, lattice, cat ):

        # Select both empty (first), then lattice
        bpy.ops.object.select_all( action = 'DESELECT' ) # deselect all
        empty.select   = True
        lattice.select = True
        context.scene.objects.active = lattice
        
        # Go to edit mode
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        # Create hook modifier for the selected point
        self.select_lattice_points( context, lattice, cat )
        
        bpy.ops.object.hook_add_selob()
            
    def execute( self, context ):
        ''' Operator's main function '''

        # Go to top ortho view
        bpy.ops.object.orient_scan( view = 'TOP' )
        
        # Create lattice
        obj, lattice = self.create_lattice( context )
        
        # create empties
        hooks = self.create_empties( context, obj, lattice )
        
        # select top empty
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        bpy.ops.object.select_all( action = 'DESELECT' )
        
        hooks[ 'center' ].select = True
        context.scene.objects.active = hooks[ 'center' ]
        
        lattice.hide = True
        
        return {'FINISHED'}
        
class create_insole_from_curve( bpy.types.Operator ):
    """ Create mesh insole object from curve and scan """
    bl_idname      = "object.trim_insole"
    bl_label       = "Create Insole"
    bl_description = "Create Insole from Scan and Outline"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def clear_bottom_verts( self, context, c ):
        ''' Deletes the bottom vertices after boolean opearation '''
        c.select                     = True
        context.scene.objects.active = c
        
        if c.mode != 'EDIT': bpy.ops.object.mode_set( mode = 'EDIT' )

        bpy.ops.mesh.select_all( action = 'DESELECT' )
        bm = bmesh.from_edit_mesh( c.data ) # Create BMESH object
        
        lowest_z = 10000
        lz_idx   = -1
        
        # Find lowest vert
        for v in bm.verts:
            if v.co.z < lowest_z:
                lowest_z = v.co.z
                lz_idx   = v.index
                
        # Select all the verts at the same height
        for v in bm.verts:
            if round( v.co.z, 2 ) == round( bm.verts[ lz_idx ].co.z, 2 ):
                v.select = True
                
        bm.select_flush( True ) # Flush selected
        
        bpy.ops.mesh.delete()   # Delete dselected (bottom) verts

        # Go to object mode
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        
    def execute( self, context ):
        props = context.scene.insole_properties
        scn   = context.scene
        cname = [ o.name for o in scn.objects if 'insole_curve' in o.name ].pop()
        c     = context.scene.objects[ cname ] # Create reference by object name

        # Reference scan object
        scan = [ o for o in scn.objects if o.type == 'MESH' ].pop()
        
        # Select curve object and set it as active
        bpy.ops.object.select_all( action = 'DESELECT' )
        c.select = True        # Select curve
        scn.objects.active = c # Set curve as active object

        # Apply modifiers on curve        
        for m in c.modifiers: 
            bpy.ops.object.modifier_apply( modifier = m.name )
            
        # Apply modifiers on mesh object
        bpy.ops.object.select_all( action = 'DESELECT' )
        scan.select = True        # Select curve
        scn.objects.active = scan # Set curve as active object
        for m in scan.modifiers:
            bpy.ops.object.modifier_apply( modifier = m.name )

        # Delete all type = 'EMPTY' or 'LATTICE' objects
        types = [ 'EMPTY', 'LATTICE' ]
        bpy.ops.object.select_all( action = 'DESELECT' )
        for e in [ e for e in scn.objects if e.type in types ]:
            if e.hide: e.hide = False # Unhide hidden objects
            e.select = True           # Select empty / lattice
        bpy.ops.object.delete()       # Delete selected objects

        # Select curve object and set it as active
        bpy.ops.object.select_all( action = 'DESELECT' )
        c.select = True        # Select curve
        scn.objects.active = c # Set curve as active object

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

        # Recalculate normals on both objects
        for obj in c, scan:
            bpy.ops.object.mode_set( mode = 'OBJECT' )
            
            bpy.ops.object.select_all( action = 'DESELECT' )
            obj.select         = True # Select obj
            scn.objects.active = obj  # Set scan as active object

            # Go to edit mode, vertex selection mode and select all verts
            bpy.ops.object.mode_set( mode   = 'EDIT'   )
            bpy.ops.mesh.select_mode( type  = 'VERT'   )
            bpy.ops.mesh.select_all( action = 'SELECT' )
            
            bpy.ops.mesh.normals_make_consistent() # Recalculate normals
        
        # Go to object mode
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        
        # Create boolean modifier on curve
        bpy.ops.object.select_all( action = 'DESELECT' )
        c.select = True        # Select curve
        scn.objects.active = c # Set scan as active object
        
        m = c.modifiers.new( 'insole_boolean', 'BOOLEAN' )
        m.operation = 'DIFFERENCE'
        m.object    = scan

        # Apply boolean modifier and delete (or hide) other object
        bpy.ops.object.modifier_apply( modifier = 'insole_boolean' )
        
        # Delete now useless converted curve
        bpy.ops.object.select_all( action = 'DESELECT' )
        scan.select = True        # Select curve
        scn.objects.active = scan # Set curve as active object
        bpy.ops.object.delete()

        self.clear_bottom_verts( context, c ) # Clear bottom vertices

        # Perform cleanup post trimming
        bpy.ops.object.perform_cleanup()
        
        return {'FINISHED'}

class fill_holes( bpy.types.Operator ):
    """ Create empties for easy control over front """
    bl_idname      = "object.fill_insole_holes"
    bl_label       = "Fill Holes"
    bl_description = "Fill holes in the insole mesh"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def find_next_linked_vert( self, context, edges, selected, loop, i ):
        loop.append( i )
        # Remove documented verts from lookup verts
        the_rest = selected - set( loop )

        for j in the_rest:
            shared_edges = [ 
                e for e in edges if j in edges[e] and i in edges[e]
            ]

            if len( shared_edges ) > 0:
                # Then the lookup vert and this vert have a common edge.
                # And if so, call this function again with this vert
                self.find_next_linked_vert( 
                    context, edges, selected, loop, j 
                )

        return loop

    def execute( self, context ):
        ''' Select non-manifold geometry and beauty fill holes '''
        o = context.object

        # 1. Go to edit mode and create bmesh object
        if o.mode != 'EDIT': bpy.ops.object.mode_set(mode = 'EDIT')

        # Go to vertex selection mode and deselect all verts
        bpy.ops.mesh.select_mode( type  = 'VERT'     )
        bpy.ops.mesh.select_all( action = 'DESELECT' )

        # Select non manifold geometry (outline verts)
        bpy.ops.mesh.select_non_manifold()
        # This selects all the inner holes and the outer rim loop
        # Must deselect he outer rim or it will be filled as well

        bm = bmesh.from_edit_mesh( o.data )        

        edges = { 
            e.index : [ v.index for v in e.verts ] for e in bm.edges if e.select
        }

        selected_verts = [ v.index for v in bm.verts if v.select ]

        # Find the vert with the highest Y value (which must be on the rim)
        max_y     = -10000
        topy_vert = -1
        for i in selected_verts:
            co = bm.verts[i].co * o.matrix_world
            if co.y > max_y:
                max_y = co.y
                topy_vert = i

        selected_set = set( selected_verts )
        loop_verts = []

        # Call recursive function with the highest-y vert as first input
        # to find the outer-rim loop
        loop = self.find_next_linked_vert( 
            context, edges, selected_set, loop_verts, topy_vert 
        )

        # Select the inner holes' verts
        for i in loop:
            bm.verts[ i ].select = False

        bm.select_flush( False )

        # Fill holes and triangulate
        bpy.ops.mesh.fill()
        bpy.ops.mesh.quads_convert_to_tris()

        bpy.ops.object.mode_set(mode = 'OBJECT')

        return {'FINISHED'}

class remove_excess( bpy.types.Operator ):
    """ Clear all materials assigned to active object """
    bl_idname      = "object.quick_remove_excess"
    bl_label       = "Remove Excess"
    bl_description = "Launch tools for quick removal of excess geometry"
    bl_options     = {'REGISTER'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def execute( self, context ):
        # Go to edit mode and deselect all verts
        bpy.ops.object.mode_set( mode   = 'EDIT'     )

        # Go to vertex selection mode
        bpy.ops.mesh.select_mode(type='VERT')

        # Deselect all verts
        bpy.ops.mesh.select_all( action = 'DESELECT' )
        
        ## Set view to wirefame mode
        # Find 3D View area in default screen
        area_3dv = [ 
            a for a in bpy.data.screens["Default"].areas if a.type == 'VIEW_3D' 
        ].pop()

        # Find 3D View space in 3D View Area
        space_3dv = [ s for s in area_3dv.spaces if s.type == 'VIEW_3D' ].pop()
        
        # Set shading mode to wireframe
        space_3dv.viewport_shade = 'WIREFRAME'
        
        # Go to circular selection mode
        bpy.ops.view3d.select_circle()
        
        return {'FINISHED'}
        
class create_insole( bpy.types.Operator ):
    """ Create mesh insole object from cleaned mesh """
    bl_idname      = "object.create_insole"
    bl_label       = "Create Insole"
    bl_description = "Create Finished Insole from Cleaned Mesh"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def cleanup_and_repair_heel( self, context ):
        props = context.scene.insole_properties
        o     = context.object

        # Go to edit mode, vertex selection mode and select all verts
        bpy.ops.object.mode_set( mode   = 'EDIT'   )
        bpy.ops.mesh.select_mode( type  = 'VERT'   )
        bpy.ops.mesh.select_all( action = 'SELECT' )


        # Extrude down on z to bottom of scan + insole_thickness
        coos   = [ c.co * o.matrix_world for c in o.data.vertices ]
        z_coos = [ c.z for c in coos ]
        z_coos.sort()
        lowest_z  = z_coos[0]
        extrude_z = ( o.location.z - lowest_z + props.insole_thickness ) * -1
        
        bpy.ops.mesh.extrude_region_move( 
            TRANSFORM_OT_translate = { "value":(0, 0, extrude_z ) }
        )

        # Flatten extruded area
        bpy.ops.transform.resize( 
            value             = ( 1, 1, 0),
            constraint_axis   = ( False, False, True )
        )
        
        bpy.ops.mesh.normals_make_consistent() # Recalculate normals

    def execute( self, context ):
        ''' Preview the aread of the heel to be and the straightening line '''
        o = context.object
        
        self.cleanup_and_repair_heel( context )

        if o.mode != 'OBJECT': bpy.ops.object.mode_set(mode = 'OBJECT')

        # Remove all the objects materials
        context.scene.objects.active = o
        for i in range( len( o.material_slots ) ):
            bpy.ops.object.material_slot_remove()
        
        bpy.ops.object.perform_cleanup()
        
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

    def select_area( self, context, area_type = 'flat' ):
        ''' Select the flat area as defined by the % in the flat area property '''

        o     = context.object
        props = context.scene.insole_properties

        # 1. Go to edit mode and create bmesh object
        if o.mode != 'EDIT': bpy.ops.object.mode_set(mode = 'EDIT')
        bm = bmesh.from_edit_mesh( o.data )
        
        # 2. Find the vertex with the highest Y value
        max_y = -10000
        min_y = 10000
        idx   = -1
        idx2  = -1
        for v in bm.verts:
            if v.co.y > max_y:
                max_y = v.co.y
                idx   = v.index
            if v.co.y < min_y:
                min_y = v.co.y
                idx2  = v.index

        if idx == -1 or idx == -2: return {'FAILED'}
                
        # 3. Store y dimensions of insole. Find 25% of this value. flat_dist.
        flat_dist = o.dimensions.y * props.flat_area
        mid_size  = o.dimensions.y * props.falloff / 2
        
        # 4. Select all vertices that are up to flat_dist from top-y vert.
        flat_y = bm.verts[idx].co.y - flat_dist
        mid_y  = flat_y - mid_size

        # Define heel selection area
        heel_size = o.dimensions.y * props.heel_area
        heel_y    = bm.verts[idx2].co.y + heel_size

        # Define heel falloff area
        heel_falloff_y = heel_y + o.dimensions.y * props.heel_twist_falloff
        
        # Go to vertex selection mode and deselect all verts
        bpy.ops.mesh.select_mode( type   = 'VERT'     )
        bpy.ops.mesh.select_all(  action = 'DESELECT' )
        
        # Select all vertices located above minimum Y value
        nonheel_verts = heel_verts = orig_verts = mid_verts = flat_verts = 0
        if area_type == 'flat':
            for v in bm.verts:
                if v.co.y > flat_y: 
                    v.select = True
                    flat_verts += 1
        elif area_type == 'mid':
            for v in bm.verts:
                if v.co.y <= flat_y and v.co.y >= mid_y: 
                    v.select = True
                    mid_verts += 1
        elif area_type == 'heel':
            for v in bm.verts:
                if v.co.y < heel_y: 
                    v.select = True
                    heel_verts += 1
        elif area_type == 'heel_mid':
            for v in bm.verts:
                if v.co.y >= heel_y and v.co.y <= heel_falloff_y:
                    v.select = True
                    mid_verts += 1
        elif area_type == 'non_heel':
            for v in bm.verts:
                if v.co.y > heel_falloff_y:
                    v.select = True
                    nonheel_verts += 1
        else: # Select all unchanged ('orig') vertices
            for v in bm.verts:
                if v.co.y < mid_y: 
                    v.select = True
                    orig_verts += 1

        if area_type == 'heel':
            return idx2
        else:
            return idx

    def create_materials( self, context, materials, colors ):
        ''' Make sure provided materials exist in file data, and create 
            them if they don't. Return references to material objects.
        '''

        o     = context.object
        props = context.scene.insole_properties

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
        
        return mat_refs

    def assign_materials( self, context, mat_refs ):
        ''' Assignes the materials specified in mat_refs to the relevant area '''

        o     = context.object
        props = context.scene.insole_properties

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
            
            self.select_area( context, m ) # Select current area's vertices
            
            o.active_material_index = mi
            bpy.ops.object.mode_set( mode = 'OBJECT' )
            bpy.ops.object.mode_set( mode = 'EDIT' )
            bpy.ops.object.material_slot_assign()

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

        # Ensure materials exist in scene data or create them
        mat_refs = self.create_materials( context, materials, colors )

        bpy.ops.object.mode_set(mode ='OBJECT')

        self.assign_materials( context, mat_refs )  # Assing materials

        bpy.ops.object.mode_set(mode ='OBJECT')

    def update_heel_materials( self, context ):
        o = context.object

        materials = {
            'heel'     : 'heel__insole.mat',
            'heel_mid' : 'heel_mid_insole.mat',
            'non_heel' : 'non_heel_insole.mat'
        }

        colors = { 
            'heel'     : Color( ( 1.0, 0.0, 0.0 ) ), # Pure red
            'heel_mid' : Color( ( 0.5, 0.25, 0  ) ), # Yellow
            'non_heel' : Color( ( 0.0, 0.0, 1.0 ) )  # Pure blue
        }

        # Ensure materials exist in scene data or create them
        mat_refs = self.create_materials( context, materials, colors )

        bpy.ops.object.mode_set(mode ='OBJECT')

        self.assign_materials( context, mat_refs )  # Assing materials

        bpy.ops.object.mode_set(mode ='OBJECT')

    def proportional_transform( 
        self, context, area, vector, action = 'translate'
    ):
        ''' performs a proportional transformation of a group of vertices '''

        o       = context.object
        falloff = self.falloff
        
        self.select_area( context, area ) # select area

        constraint_axis = tuple( [ x != 0 for x in vector ] )
        
        if action == 'translate':
            bpy.ops.transform.translate(
                value                     = vector, 
                constraint_axis           = constraint_axis,
                proportional              = 'ENABLED', 
                proportional_edit_falloff = 'SMOOTH',
                proportional_size         = o.dimensions.y * self.prop_falloff
            )
            
        elif action == 'rotate':
            twist_amount = vector[1] - self.cumulative_twist

            bpy.ops.transform.rotate(
                value                     = twist_amount, 
                axis                      = ( 0.0, 1.0, 0.0 ),
                constraint_axis           = ( False, True, False ),
                proportional              = 'ENABLED', 
                proportional_edit_falloff = 'SMOOTH',
                proportional_size         = o.dimensions.y * self.prop_falloff
            )
            
            self.cumulative_twist += twist_amount
            
        bpy.ops.object.mode_set(mode ='OBJECT') # Return to object mode

    def update_twist_area( self, context ):
        ''' rotate front or heel area (twist_area) proportionally.
            uses twist_angle as proportional size
        '''
        o       = context.object
        falloff = self.prop_falloff

        # Reset twist property values
        self.cumulative_twist = 0.0
        self.twist_angle      = 0.0
        
        if self.twist_area == 'Heel':
            self.update_heel_materials( context )
        elif self.twist_area == 'Front':
            self.update_materials( context )
            
    def update_twist( self, context ):
        ''' rotate front or heel area (twist_area) proportionally.
            uses twist_angle as proportional size
        '''
        o       = context.object
        vector  = ( 0, self.twist_angle, 0 )

        area_dict = { 'Front' : 'flat', 'Heel' : 'heel' }

        # If front is used, then the flat falloff is used and it must be synced
        # with the ordinary proportional falloff
        if area_dict == 'Front': 
            self.prop_falloff = self.falloff
        elif area_dict == 'Heel':
             self.falloff = self.heel_twist_falloff
        
        self.proportional_transform( 
            context, area_dict[ self.twist_area ], vector, 'rotate'
        )
        
    def update_empty( self, context ):
        ''' updates when the empty is moved and with it, the area '''
        pass
        
    decimate_faces = bpy.props.IntProperty(
        description = "Number of faces to keep",
        name        = "Resolution",
        default     = 30000,
        min         = 10000,
        max         = 40000
    )

    flat_area = bpy.props.FloatProperty(
        description = "Percentage of scan to be flattened, from front to back",
        name        = "Flat Area",
        subtype     = 'FACTOR',
        default     = 0.25,
        min         = 0.0,
        max         = 1.0,
        update      = update_materials
    )

    heel_area = bpy.props.FloatProperty(
        description = "Percentage of scan defining the heel area",
        name        = "Heel Area",
        subtype     = 'FACTOR',
        default     = 0.25,
        min         = 0.0,
        max         = 1.0,
        update      = update_heel_materials
    )

    heel_factor = bpy.props.FloatProperty(
        description = "Straightening factor for the top of the heel",
        name        = "Heel Straightening Factor",
        subtype     = 'DISTANCE',
        default     = 4.0,
        min         = 0.0,
        max         = 100.0
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

    twist_area = bpy.props.EnumProperty(
        name    = "Area",
        items   = [('Front', 'Front', ''), ('Heel', 'Heel', '')], 
        default = 'Front',
        update  = update_twist_area
    )

    twist_angle = bpy.props.FloatProperty(
        description = "Twist angle",
        name        = "Angle",
        subtype     = 'ANGLE',
        default     = 0,
        min         = -180.0,
        max         = 180.0,
        update      = update_twist
    )

    heel_twist_falloff = bpy.props.FloatProperty(
        description = "Falloff area for heel twist amendments",
        name        = "Falloff",
        subtype     = 'FACTOR',
        default     = 0.25,
        min         = 0.0,
        max         = 1.0,
        update      = update_heel_materials
    )
    
    cumulative_twist = bpy.props.FloatProperty(
        description = "Twist angle",
        name        = "Angle",
        subtype     = 'ANGLE',
        default     = 0.0
    )

    prop_falloff = bpy.props.FloatProperty(
        description = "Falloff area for proportional transformations",
        name        = "Falloff",
        subtype     = 'FACTOR',
        default     = 0.25,
        min         = 0.0,
        max         = 1.0
    )

    # Cast dimensions
    cast_dimensions = bpy.props.FloatVectorProperty(
        name        = "Cast Dimensions", 
        description = "XYZ Dimensions of the cast block", 
        default     = ( 240.0, 330.0, 40.0 ),
        min         = 0.0,
        precision   = 2,
        subtype     = 'XYZ',
        unit        = 'LENGTH', 
        size        = 3
    )
    
class create_insole_cast( bpy.types.Operator ):
    """ Create CNC cast out of two selected insole objects """
    bl_idname      = "object.create_insole_cast"
    bl_label       = "Create Cast"
    bl_description = "Clear CNC cast from imported Insoles"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with exactly two selected MESH type objects '''
        selobjs         = context.selected_objects
        selected_meshes = [ o for o in selobjs if o.type == 'MESH' ]

        return len( selected_meshes ) == 2

    insole_R = bpy.props.StringProperty()
    insole_L = bpy.props.StringProperty()
    cast     = bpy.props.StringProperty()
    
    def create_cast_block( self, context ):
        """ Create box cast block """
        
        props = context.scene.insole_properties
        
        # Find and assign left and right insole properties
           
        obj_names = [ o.name for o in context.selected_objects ]
        for oname in obj_names:
            o = context.scene.objects[ oname ]        

            bpy.ops.object.mode_set( mode = 'OBJECT' )
                   
            bpy.ops.object.select_all( action = 'DESELECT' )
            
            o.select = True
            context.scene.objects.active = o
            
            bpy.ops.object.mode_set(  mode = 'EDIT' )
            bpy.ops.mesh.select_mode( type = 'VERT' )

            bm = bmesh.from_edit_mesh( o.data )

            # Find min and max X values
            minX =  10000
            maxX = -10000
            for v in bm.verts:
                co = v.co * o.matrix_world
                if co.x < minX: minX = co.x
                if co.x > maxX: maxX = co.x

            # A right insole is one where the distance between the origin and 
            # the leftmost (minX) vertex is larger than the distance to the 
            # rightmost (maxX) vert. The left insole is opposite.
            if abs( o.location.x - minX ) > abs( o.location.x - maxX ):
                self.insole_R = o.name
            else:
                self.insole_L = o.name

        # Create cast block
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        bpy.ops.mesh.primitive_cube_add()

        # Store name and reference object
        self.cast = context.object.name
        cast      = context.scene.objects[ self.cast ]
        
        # Set dimensions
        cast.dimensions = props.cast_dimensions        
        
        # Apply transformations (scale)
        bpy.ops.object.transform_apply( scale = True )
        
    def prepare_insoles( self, context ): 
        """ Pre boolean positioning and preparation """
        props = context.scene.insole_properties

        # Find the width of both insoles, and compare it with cast width
        total_insole_width = sum( 
            [ context.scene.objects[ ins ].dimensions.x \
            for ins in [ self.insole_R, self.insole_L ] ]
        )
        
        cast_width = props.cast_dimensions.x 
        total_gap  = cast_width - total_insole_width

        # Divide gap by 3 - will be used to space insoles and spread on cast
        gap = math.trunc( total_gap / 3 )
        
        for name in [ self.insole_R, self.insole_L ]:
            bpy.ops.object.mode_set( mode = 'OBJECT' )

            o = context.scene.objects[ name ]

            # Select and activate only current insole object
            bpy.ops.object.select_all( action = 'DESELECT' )
            o.select = True
            context.scene.objects.active = o            
            
            # Flip object
            bpy.ops.transform.rotate(value = math.radians(180), axis = (0,1,0) )
            
            # Apply rotation
            bpy.ops.object.transform_apply( rotation = True )
            
            # Select top verts
            bpy.ops.object.mode_set(  mode = 'EDIT' )
            bpy.ops.mesh.select_mode( type = 'VERT' )

            bm = bmesh.from_edit_mesh( o.data ) # Create bmesh object
            
            maxZ = -10000
            for v in bm.verts:
                if v.co.z > maxZ: maxZ = v.co.z

            bpy.ops.mesh.select_all( action = 'DESELECT' ) # Deselect all verts
            maxZ = round( maxZ, 2 ) # Round Z value to 2 points
                
            for v in bm.verts:
                if round( v.co.z, 2 ) == maxZ: v.select = True
                
            bm.select_flush( True )
            
            # Snap cursor to selection
            bpy.ops.view3d.snap_cursor_to_selected()
            
            # Delete faces
            bpy.ops.mesh.delete( type = 'FACE' )
            
            # Place origin at cursor location
            bpy.ops.object.mode_set(   mode = 'OBJECT'        )
            bpy.ops.object.origin_set( type = 'ORIGIN_CURSOR' )
            
            # Snap insole to top of cast face
            cast = context.scene.objects[ self.cast ]
            bpy.ops.object.select_all( action = 'DESELECT' )
            cast.select = True
            context.scene.objects.active = cast
            
            bpy.ops.object.mode_set(  mode = 'EDIT' )
            bpy.ops.mesh.select_mode( type = 'FACE' )
            
            bm = bmesh.from_edit_mesh( cast.data ) # Create bmesh object
            
            # Find top face
            max = -10000
            idx = -1
            for i,f in enumerate( bm.faces ):
                center_co = f.calc_center_median()
                if center_co > max:
                    max = center_co
                    idx = i
            
            # Select top face
            bpy.ops.mesh.select_all( action = 'DESELECT' )
            bm.faces[i].select = True
            bm.select_flush( True )

            bpy.ops.view3d.snap_cursor_to_selected() # Cursor to selected

            # Select insole object
            bpy.ops.object.mode_set(   mode   = 'OBJECT'   )
            bpy.ops.object.select_all( action = 'DESELECT' )
            o.select = True
            context.scene.objects.active = o
            
            bpy.ops.view3d.snap_selected_to_cursor() # Selected to cursor
            
            # Place at insole at correct side and distance from edge
            transform_distance = cast_width / 2 - o.dimensions.x / 2 - gap
            bpy.ops.transform.translate( value = ( transform_distance, 0, 0 ) )
            
            # Select non manifold
            bpy.ops.object.mode_set(  mode = 'EDIT' )
            bpy.ops.mesh.select_mode( type = 'VERT' )
            
            bpy.ops.mesh.select_non_manifold()
            
            # Extrude in place
            bpy.ops.mesh.extrude_region()
            
            # Scale extruded geometry           x    y    z
            bpy.ops.transform.resize( value = ( 1.3, 1.1, 1 ) )
            
            # Calculate Z height = current Z dimension + 1
            extrude_length = -1 * ( o.dimensions.z + 1 )
            
            # Extrude down by 6 mm
            bpy.ops.mesh.extrude_region_move( 
                TRANSFORM_OT_translate = { "value" :(0, 0, extrude_length) }
            )
            
            # Close face and triangulate
            bpy.ops.mesh.fill()
            bpy.ops.mesh.quads_convert_to_tris()
            
    def create_positive_cast( self, context ):
        """ Expand insole to create a positive for cast creation """
        pass

    def create_cast( self, context ):
        """ Crete finished cast """
        pass

    def execute( self, context ):
        self.create_cast_block( context )
        self.prepare_insoles( context )
        
        return {'FINISHED'}
    
right_foot_insole_curve_coordinates = [
  {
    "rh": {
      "type": "ALIGNED", 
      "co": [
        -52.266014099121094, 
        27.295093536376953, 
        0.0
      ]
    }, 
    "lh": {
      "type": "ALIGNED", 
      "co": [
        -30.258426666259766, 
        -40.74249267578125, 
        0.0
      ]
    }, 
    "point": [
      -37.095340728759766, 
      -19.605823516845703, 
      0.0
    ]
  }, 
  {
    "rh": {
      "type": "ALIGNED", 
      "co": [
        -57.40950012207031, 
        115.08479309082031, 
        0.0
      ]
    }, 
    "lh": {
      "type": "ALIGNED", 
      "co": [
        -60.92235565185547, 
        64.29387664794922, 
        0.0
      ]
    }, 
    "point": [
      -59.16592788696289, 
      89.6893310546875, 
      0.0
    ]
  }, 
  {
    "rh": {
      "type": "ALIGNED", 
      "co": [
        9.416471481323242, 
        129.8833770751953, 
        0.0
      ]
    }, 
    "lh": {
      "type": "ALIGNED", 
      "co": [
        -45.24030303955078, 
        128.87692260742188, 
        0.0
      ]
    }, 
    "point": [
      -18.759876251220703, 
      129.36453247070312, 
      0.0
    ]
  }, 
  {
    "rh": {
      "type": "FREE", 
      "co": [
        51.541465759277344, 
        49.96627426147461, 
        0.0
      ]
    }, 
    "lh": {
      "type": "FREE", 
      "co": [
        29.194015502929688, 
        109.89535522460938, 
        0.0
      ]
    }, 
    "point": [
      40.367740631103516, 
      79.93081665039062, 
      0.0
    ]
  }, 
  {
    "rh": {
      "type": "FREE", 
      "co": [
        44.40078353881836, 
        -62.87953567504883, 
        0.0
      ]
    }, 
    "lh": {
      "type": "FREE", 
      "co": [
        54.11138153076172, 
        10.025206565856934, 
        0.0
      ]
    }, 
    "point": [
      47.87248611450195, 
      -29.36204719543457, 
      0.0
    ]
  }, 
  {
    "rh": {
      "type": "ALIGNED", 
      "co": [
        32.898555755615234, 
        -141.05630493164062, 
        0.0
      ]
    }, 
    "lh": {
      "type": "ALIGNED", 
      "co": [
        44.93161392211914, 
        -95.7703857421875, 
        0.0
      ]
    }, 
    "point": [
      38.91508483886719, 
      -118.41334533691406, 
      0.0
    ]
  }, 
  {
    "rh": {
      "type": "ALIGNED", 
      "co": [
        -25.744993209838867, 
        -141.8401641845703, 
        0.0
      ]
    }, 
    "lh": {
      "type": "ALIGNED", 
      "co": [
        20.334665298461914, 
        -153.45138549804688, 
        0.0
      ]
    }, 
    "point": [
      -9.32647705078125, 
      -145.97732543945312, 
      0.0
    ]
  }, 
  {
    "rh": {
      "type": "ALIGNED", 
      "co": [
        -31.525466918945312, 
        -70.26678466796875, 
        0.0
      ]
    }, 
    "lh": {
      "type": "ALIGNED", 
      "co": [
        -29.268753051757812, 
        -120.81562805175781, 
        0.0
      ]
    }, 
    "point": [
      -30.397109985351562, 
      -95.54120635986328, 
      0.0
    ]
  }
]
    
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.insole_properties = bpy.props.PointerProperty( 
        type = insole_props
    )

def unregister():
    bpy.utils.unregister_module(__name__)
