# camp.py
# Camera Aligned Material Plane
# (c) 2024 Andrew S. Gordon

import bpy

bl_info = {
    "name": "Camera Aligned Material Plane",
    "author": "Andrew S. Gordon",
    "version": (1,0),
    "blender": (4,1,0),
    "location": "View3D > Tool Shelf > Object",
    "description": "Utility for aligning material-based image planes to the camera",
    "tooltip": "CAMP tooltip",
    "category": "Development",
}

class AlignPlaneToCamera(bpy.types.Operator):
    """Align selected plane to camera"""
    bl_idname = "object.align_plane_to_camera"
    bl_label = "Align Plane to Camera"
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        main(context)
        return {'FINISHED'}
    
def main(context):
    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # Assume the camera is named "Camera"
    camera = bpy.data.objects['Camera']
    # Assume the active object is the plane
    plane = bpy.context.active_object
    # Go for it
    align(camera, plane)

def align(camera, plane):
    # Aligns the panel to the camera

    # Ensure plane has scale (1,1,1)
    with bpy.context.temp_override(active_object=plane):
        bpy.ops.object.transform_apply(location=False, rotation=False)
    
    # Add constraint so that plane always faces camera
    copyr = plane.constraints.new("COPY_ROTATION")
    copyr.target = camera

    # Parent the plane to the camera and center-align
    distance = (camera.location - plane.location).length
    plane.parent = camera
    plane.location[0] = 0
    plane.location[1] = 0
    plane.lock_location[0] = True
    plane.lock_location[1] = True
    plane.location[2] = -distance

    # Resize the plane
    resize = 2 / plane.dimensions[0]
    plane.scale[0] = resize
    plane.scale[1] = resize
    with bpy.context.temp_override(active_object=plane):
        bpy.ops.object.transform_apply(location=False, rotation=False)

    # Setup driver for dimensions to fit/fill camera
    driver_x = plane.driver_add("scale", 0).driver
    driver_y = plane.driver_add("scale", 1).driver
    var_x = driver_x.variables.new()
    var_y = driver_y.variables.new()
    var_x.name = "varx"
    var_y.name = "vary"
    var_x.type = 'SINGLE_PROP'
    var_y.type = 'SINGLE_PROP'
    var_x.targets[0].id_type = 'OBJECT'
    var_y.targets[0].id_type = 'OBJECT'
    var_x.targets[0].id = plane
    var_y.targets[0].id = plane
    var_x.targets[0].data_path = "location[2]"
    var_y.targets[0].data_path = "location[2]"
    angle = camera.data.angle_x
    driver_x.expression = f"-varx*tan({angle}/2)"
    driver_y.expression = f"-vary*tan({angle}/2)"

    bpy.context.view_layer.update()
  
def menu_func(self, context):
    self.layout.operator(AlignPlaneToCamera.bl_idname)

def register():
    bpy.utils.register_class(AlignPlaneToCamera)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(AlignPlaneToCamera)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()

