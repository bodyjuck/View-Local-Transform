import bpy
import math
import mathutils
import copy

bl_info = {
    "name" : "View Local Transform",             
    "author" : "dskjal",                  
    "version" : (1,0),                  
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
        return mathutils.Matrix.Identity(4)

    return ob.parent.matrix_world
    
def create_scale_matrix_4x4(v):
    m = mathutils.Matrix.Identity(4)
    m[0][0] = v[0]
    m[1][1] = v[1]
    m[2][2] = v[2]

    return m

def get_updated_world():
    ob = bpy.context.active_object
    loc = ob.lt_location
    scale = ob.lt_scale

    mRot = None
    if ob.rotation_mode=='QUATERNION':
        mRot = ob.lt_quaternion.to_euler('XYZ').to_matrix().to_4x4()
    elif ob.rotation_mode=='AXIS_ANGLE':
        mRot = mathutils.Matrix.Rotation(ob.lt_axisangle[0], 4, ob.lt_axisangle[1:4])
    else:
        mRot = mathutils.Euler(ob.lt_euler,ob.rotation_mode).to_matrix().to_4x4()

    mLoc = mathutils.Matrix.Translation(loc)
    mScale = create_scale_matrix_4x4(scale)
    updated_local = mLoc * mRot * mScale

    parent_world = get_parent_world_matrix(ob)
    return parent_world * updated_local

def value_changed_callback(self, context):
    bpy.context.scene.lt_value_updated_from_Panel = True

#------------------------------------------UI------------------------
class UI(bpy.types.Panel):
    bl_label = "Local Transform"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bpy.types.Object.lt_location = bpy.props.FloatVectorProperty(name="",subtype='XYZ', update = value_changed_callback)
    bpy.types.Object.lt_scale = bpy.props.FloatVectorProperty(name="",subtype='XYZ',update = value_changed_callback)
    bpy.types.Object.lt_euler = bpy.props.FloatVectorProperty(name="",subtype='EULER',update = value_changed_callback)
    bpy.types.Object.lt_quaternion = bpy.props.FloatVectorProperty(name="",subtype='QUATERNION',size=4,update = value_changed_callback)
    bpy.types.Object.lt_axisangle = bpy.props.FloatVectorProperty(name="",subtype='AXISANGLE',size=4,update=value_changed_callback)

    bpy.types.Object.lt_old_location = bpy.props.FloatVectorProperty(name="",subtype='XYZ')
    bpy.types.Object.lt_old_scale = bpy.props.FloatVectorProperty(name="",subtype='XYZ')
    bpy.types.Object.lt_old_euler = bpy.props.FloatVectorProperty(name="",subtype='EULER')
    bpy.types.Object.lt_old_quaternion = bpy.props.FloatVectorProperty(name="",subtype='QUATERNION',size=4)
    bpy.types.Object.lt_old_axisangle = bpy.props.FloatVectorProperty(name="",subtype='AXISANGLE',size=4)
    bpy.types.Object.lt_old_rotation_mode = bpy.props.StringProperty(name="")

    bpy.types.Scene.lt_value_updated_from_Panel = bpy.props.BoolProperty(name="",default=False)
    bpy.types.Scene.lt_last_selected_object = bpy.props.StringProperty(name="")

    @classmethod
    def poll(self, context):
        return context.active_object.mode == 'OBJECT'

    def draw(self, context):
        ob = context.active_object
        layout = self.layout
        scn = context.scene

        layout.label(text="Local Location:")
        col = layout.column(align=True)
        col.prop(ob, "lt_location")
        layout.separator()

        layout.label(text="Local Rotation:")
        col = layout.column(align=True)
        if ob.rotation_mode=='QUATERNION':
            col.prop(ob, "lt_quaternion")
        elif ob.rotation_mode=='AXIS_ANGLE':
            col.prop(ob, "lt_axisangle")
        else:
            col.prop(ob, "lt_euler")

        layout.prop(ob, "rotation_mode",text="")
        layout.separator()

        layout.label(text="Local Scale:")
        col = layout.column(align=True)
        col.prop(ob, "lt_scale")

# update value with local matrix
def update_property(force_update=False):
    ob = bpy.context.active_object
    scn = bpy.context.scene

    component = ob.matrix_local.decompose()
    loc = component[0]
    qt = component[1]
    scale = component[2]

    ob.lt_location = loc
    ob.lt_scale = scale

    # Rotation is not update when updated by Local Transform Panel
    if not force_update and scn.lt_value_updated_from_Panel:
        return

    if ob.rotation_mode=='QUATERNION':
        if ob.lt_quaternion != qt:
            ob.lt_quaternion = qt
    elif ob.rotation_mode=='AXIS_ANGLE':
        aa = qt.to_axis_angle()
        angle = ob.rotation_axis_angle[0]
        aa_out = (angle, aa[0][0], aa[0][1], aa[0][2])
        if ob.lt_axisangle != aa_out:
            ob.lt_axisangle = aa_out
    else:
        euler = qt.to_euler(ob.rotation_mode)
        if ob.lt_euler != euler:
            ob.lt_euler = euler

def global_callback_handler(context):
    ob = bpy.context.active_object
    scn = bpy.context.scene
    if ob.mode != 'OBJECT':
        return

    # Selected object changed
    if scn.lt_last_selected_object != ob.name:
        scn.lt_last_selected_object = ob.name
        scn.lt_value_updated_from_Panel = False
        update_property(force_update=True)

    # Rotation mode changed
    if ob.lt_old_rotation_mode != ob.rotation_mode:
        ob.lt_old_rotation_mode = ob.rotation_mode
        update_property(force_update=True)

    if scn.lt_value_updated_from_Panel:
        # Updated by Local Transform Panel
        mWorld = get_updated_world()
        if ob.rotation_mode=='AXIS_ANGLE':
            ob.rotation_mode = 'XYZ'
            ob.matrix_world = mWorld
            ob.rotation_mode = 'AXIS_ANGLE'
        else:
            ob.matrix_world = mWorld
        update_property()
    else:
        # Updated by manipulation
        if ob.lt_old_location != ob.location:
            ob.lt_old_location = ob.location
            update_property()

        if ob.lt_old_scale != ob.scale:
            ob.lt_old_scale = ob.scale
            update_property()

        if ob.rotation_mode=='QUATERNION':
            if ob.lt_old_quaternion != ob.rotation_quaternion:
                ob.lt_old_quaternion = ob.rotation_quaternion
                update_property()
        elif ob.rotation_mode=='AXIS_ANGLE':
            if ob.lt_old_axisangle != ob.rotation_axis_angle:
                ob.lt_old_axisangle = ob.rotation_axis_angle
                update_property()
        else:
            if ob.lt_old_euler != ob.rotation_euler:
                ob.lt_old_euler = ob.rotation_euler
                update_property()

    scn.lt_value_updated_from_Panel = False



def register():
    bpy.utils.register_module(__name__)
    bpy.app.handlers.scene_update_post.append(global_callback_handler)

def unregister():
    bpy.utils.unregister_module(__name__)
    
if __name__ == "__main__":
    register()
