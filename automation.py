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
        
        for a in bpy.data.window_managers[0].windows[0].screen.areas:
            if a.type == 'VIEW_3D': 
                area = a
                break

        space = area.spaces[0]
                
        # Make sure 3D manipulator is displayed
        if not space.show_manipulator:
            space.show_manipulator = True

        # Display rotation manipulator
        space.transform_manipulators = {'ROTATE'}
            
        # Switch to orthographic mode if not already in it
        if space.region_3d.view_perspective != 'ORTHO':
            bpy.ops.view3d.view_persportho()

        
        bpy.ops.view3d.viewnumpad( type = self.view )
        
        # Center view on object
        bpy.ops.view3d.view_selected()
        
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

class import_and_fit_curve( bpy.types.Operator ):
    """ *** TODO: FIX bl constants *** """
    bl_idname      = "object.import_and_fit_curve" 
    bl_label       = ""
    bl_description = ""
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with MESH type objects '''
        return context.object.type == 'MESH' and context.object.select

    def execute( self, context ):
        """ Smooths vertices on object """
        o = context.object        
        
        # 1. import curve
        # 2. Find y length ratio between scan and curve
        ratio = scan.dimensions.y / curve.dimensions.y

        # Select curve, and scale to fit y length
        bpy.ops.transform.resize(value=(ratio,ratio,1))
        
        # Push curve (translate) so that the rearmost point matches
        # the scan's rear vertex.

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
        
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.insole_properties = bpy.props.PointerProperty( 
        type = insole_props
    )

def unregister():
    bpy.utils.unregister_module(__name__)