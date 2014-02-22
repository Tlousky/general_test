class create_twist_armature( bpy.types.Operator ):
    """ Preview the heel area to be straightened """
    bl_idname      = "object.create_twist_armature"
    bl_label       = "Create twist controls"
    bl_description = "Create twist controls"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll( self, context ):
        ''' Only works with selected MESH type objects '''
        if context.object:
            return context.object.type == 'MESH' and context.object.select
        else:
            return False

    def create_vertex_groups( self, context, scan, arm ):
        ''' Create a vertex_group in the scan object for each
            bone in the armature
        '''
        # Go to object mode
        bpy.ops.object.mode_set(mode = 'OBJECT') 
        
        # Deselect all objects
        bpy.ops.object.select_all( action = 'DESELECT' )
        
        # Select and activate scan obj
        scan.select = True
        context.scene.objects.active = scan
        
        # Create a vgroup for each bone
        for b in arm.data.bones:
            bpy.ops.object.mode_set(mode = 'OBJECT')

            # Check if the vertex group already exists
            if b.name not in scan.vertex_groups.keys():
                # Add vertex group
                bpy.ops.object.vertex_group_add()
                
                # vgroup.name = bone.name
                scan.vertex_groups[-1].name = b.name

    def create_weight_maps( self, context, scan, arm ):
        ''' Create the weight maps 
        vertex.groups[0].group
        vertex.groups[0].weight
        '''

        vertex_map = {}
        
        # for v in scan.data.vertices:
            

        pass

    def execute( self, context ):
        ''' Preview the aread of the heel to be and the straightening line '''

        o = context.scene.objects[ context.object.name ]

        # Find front and rear vertices on scan        
        rear  = -1
        front = -1
        least = 10000
        top   = -10000

        for v in o.data.vertices:
            if v.co.y > top:
                top = v.co.y
                front = v.index
            if v.co.y < least:
                least = v.co.y
                rear = v.index

        v_rear  = o.data.vertices[ rear  ].co
        v_front = o.data.vertices[ front ].co

        head = ( o.location.x, v_rear.y,  o.location.z )
        tail = ( o.location.x, v_front.y, v_front.z    )

        # Create armature
        bpy.ops.object.armature_add( enter_editmode = True )
        
        a = context.scene.objects[ context.object.name ] # Armature
        b = a.data.edit_bones[0]                         # Bone
        
        b.head = head
        b.tail = tail
        
        b.select = True
        
        bpy.ops.armature.subdivide( number_cuts = 2 ) # Subdivide bone
        
        self.create_vertex_groups( context, o, a ) # Create vertex groups
        
        return {'FINISHED'}