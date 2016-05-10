import bpy
import mathutils
import copy

bl_info = {
    "name" : "View Local Transform",             
    "author" : "dskjal",                  
    "version" : (0,1),                  
    "blender" : (2, 77, 0),              
    "location" : "View3D > PropertiesShelf > Local Transform",   
    "description" : "View Local Transform",   
    "warning" : "",
    "wiki_url" : "https://github.com/dskjal/View-Local-Transform",                    
    "tracker_url" : "",                 
    "category" : "Object"                   
}

#-----------------------------------------value updates-------------------------------------------------
def get_parent_world_matrix(ob):
    if ob.parent == None:
        m = mathutils.Matrix()
        m.identity()
        return m

    return ob.parent.matrix_world
    

def local_loc_update(self, context):
    ob = bpy.context.active_object
    scn = bpy.context.scene
    loc = scn.lt_location

    if not scn.disable_recursion:
        scn.disable_recursion = True

        updated_local = copy.deepcopy(ob.matrix_local)
        updated_local[0][3] = loc[0]
        updated_local[1][3] = loc[1]
        updated_local[2][3] = loc[2]

        parent_world = get_parent_world_matrix(ob)
        ob.matrix_world = parent_world * updated_local

        bpy.context.scene.update()

def local_rot_update(self, context):
    ob = bpy.context.active_object
    scn = bpy.context.scene

    if not scn.disable_recursion:
        scn.disable_recursion = True

        mRot = None
        if ob.rotation_mode=='QUATERNION':
            mRot = scn.lt_quaternion.to_matrix().to_4x4()
        elif ob.rotation_mode=='AXIS_ANGLE':
            mRot = mathutils.Quaternion(scn.lt_quaternion[1:3], scn.lt_quaternion[0]).to_matrix().to_4x4()
        else:
            mRot = mathutils.Euler(scn.lt_euler,ob.rotation_mode).to_matrix().to_4x4()

        component = ob.matrix_local.decompose()
        mLoc = mathutils.Matrix.Translation(component[0])
        mScale = create_scale_matrix_4x4(component[2])
        updated_local = mLoc * mRot * mScale

        parent_world = get_parent_world_matrix(ob)
        ob.matrix_world = parent_world * updated_local

        bpy.context.scene.update()

def create_scale_matrix_4x4(v):
    m = mathutils.Matrix()
    m.identity()
    m[0][0] = v[0]
    m[1][1] = v[1]
    m[2][2] = v[2]

    return m

def local_scale_update(self, context):
    ob = bpy.context.active_object
    scn = bpy.context.scene
    scale = scn.lt_scale

    if not scn.disable_recursion:
        scn.disable_recursion = True
        component = ob.matrix_local.decompose()
        mLoc = mathutils.Matrix.Translation(component[0])
        mRot = component[1].to_matrix().to_4x4()
        mScale = create_scale_matrix_4x4(scale)
        updated_local = mLoc * mRot * mScale

        parent_world = get_parent_world_matrix(ob)
        ob.matrix_world = parent_world * updated_local

        bpy.context.scene.update()

#------------------------------------------UI------------------------
class UI(bpy.types.Panel):
    bl_label = "Local Transform"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bpy.types.Scene.lt_location = bpy.props.FloatVectorProperty(name="",subtype='XYZ',update=local_loc_update)
    bpy.types.Scene.lt_scale = bpy.props.FloatVectorProperty(name="",subtype='XYZ',update=local_scale_update)
    bpy.types.Scene.lt_euler = bpy.props.FloatVectorProperty(name="",subtype='EULER',update=local_rot_update)
    bpy.types.Scene.lt_quaternion = bpy.props.FloatVectorProperty(name="",subtype='QUATERNION',size=4,update=local_rot_update)

    bpy.types.Scene.disable_recursion = bpy.props.BoolProperty(name="")

    @classmethod
    def poll(self, context):
        return context.active_object.mode == 'OBJECT'

    def draw(self, context):
        ob = context.active_object
        layout = self.layout
        scn = context.scene

        layout.label(text="Local Location:")
        col = layout.column(align=True)
        col.prop(scn, "lt_location")

        layout.label(text="Local Rotation:")
        col = layout.column(align=True)
        if ob.rotation_mode=='QUATERNION' or ob.rotation_mode=='AXIS_ANGLE':
            col.prop(scn, "lt_quaternion")
        else:
            col.prop(scn, "lt_euler")

        layout.label(text="Local Scale:")
        col = layout.column(align=True)
        col.prop(scn, "lt_scale")

def global_callback_handler(context):
    ob = bpy.context.active_object
    scn = bpy.context.scene
    if ob.mode != 'OBJECT':
        return

    component = ob.matrix_local.decompose()
    loc = component[0]
    qt = component[1]
    scale = component[2]

    scn.disable_recursion = False

    if scn.lt_location != loc:
        scn.lt_location = loc
    if scn.lt_scale != scale:
        scn.lt_scale = scale
    
    if ob.rotation_mode=='QUATERNION':
        if scn.lt_quaternion != qt:
            scn.lt_quaternion = qt
    elif ob.rotation_mode=='AXIS_ANGLE':
        aa = qt.to_axis_angle()
        aa_out = (aa[1],aa[0][0], aa[0][1], aa[0][2])
        if scn.lt_quaternion != aa_out:
            scn.lt_quaternion = aa_out
    else:
        euler = qt.to_euler(ob.rotation_mode)
        if scn.lt_euler != euler:
            scn.lt_euler = euler

def register():
    bpy.utils.register_module(__name__)
    bpy.app.handlers.scene_update_post.append(global_callback_handler)

def unregister():
    bpy.utils.unregister_module(__name__)
    
if __name__ == "__main__":
    register()
