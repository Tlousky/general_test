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
            'object.delete_loose',
            text = 'Delete loose verts',
            icon = 'CANCEL'
        )

        col.operator( 
            'object.decimate_object',
            text = 'Reduce to %s faces' % MAX_FACES,
            icon = 'MOD_DECIM'
        )
        
        col.operator( 
            'object.smooth_verts',
            text = 'Smooth object',
            icon = 'MOD_SMOOTH'
        )
        
        col.operator( 
            'object.flatten_front',
            text = 'Flatten Front',
            icon = 'BRUSH_FLATTEN'
        )
        
class delete_loose( bpy.types.Operator ):
    """ Delete vertices not-connected to selected one """
    bl_idname      = "object.delete_loose"
    bl_label       = "Delete unconnected vertices"
    bl_description = "Delete vertices not-connected to selected one"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works in edit mode of mesh objects '''
        omode = context.object.mode == 'EDIT' # In edit mode
        otype = context.object.type == 'MESH' # Is of mesh type 
        return omode and otype

    def execute( self, context ):
        """ Deletes all the verts that aren't connected to the selected one """

        bpy.ops.object.mode_set(mode = 'EDIT') # Go to edit mode to create bmesh
        o = bpy.context.object

        # Select all verts linked to this one (on the same island or "loose part")
        bpy.ops.mesh.select_linked( limit = False )
        
        # Selecte inverse (all non-connected verts)
        bpy.ops.mesh.select_all( action = 'INVERT' )
        
        # Delete selected vertices
        bpy.ops.mesh.delete( type = 'VERT' )
        
        # Return to object mode
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
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
        bpy.ops.object.modifier_add(type='DECIMATE')
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
        o = context.object        

        # To perform flattenning:

        # 1. Go to edit mode and create bmesh object
        if o.mode != 'EDIT': bpy.ops.object.mode_set(mode = 'EDIT')
        bm = bmesh.from_edit_mesh( o.data )
        
        # 2. Find the vertex with the highest Y value
        max_y = -1000
        idx  = -1
        for v in bm.verts:
            if v.co.y > max_y:
                max_y = v.co.y
                idx   = v.index

        if idx == -1: return {'FAILED'}
                
        # 3. Store y dimensions of insole. Find 25% of this value. flat_dist.
        flat_dist = o.dimensions.y * LENGTH_PERCENTAGE

        # 4. Select all vertices that are up to flat_dist from top-y vert.
        min_y = bm.verts[idx].co.y - flat_dist

        # Go to vertex selection mode and deselect all verts
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Select all vertices located above minimum Y value
        for v in bm.verts:
            if v.co.y > min_y: v.select = True
        
        # 5. Activate proportional editing tool.
        context.scene.tool_settings.proportional_edit = 'ENABLED'
        
        # 6. Set it's radius to be 20% of y length of insole (diamter = 40%)
        context.scene.tool_settings.proportional_size = \
            o.dimensions.y * LENGTH_PERCENTAGE

        # 7. Scale all selected verts to 0 on Z axis.
        bpy.ops.transform.resize(
            value                     = (1, 1, 0), 
            constraint_axis           = (False, False, True), 
            proportional              = 'ENABLED', 
            proportional_edit_falloff = 'SMOOTH',
            proportional_size         = o.dimensions.y * LENGTH_PERCENTAGE
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
            proportional_size         = o.dimensions.y * LENGTH_PERCENTAGE
        )        
        
        # 9. Deactivate proportional editing tool.
        context.scene.tool_settings.proportional_edit = 'DISABLED'

        # 10. Go back to object mode.
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
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
        
def register():
    bpy.utils.register_module(__name__)
    
def unregister():
    bpy.utils.unregister_module(__name__)