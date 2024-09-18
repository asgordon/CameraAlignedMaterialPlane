# camp.py
# Camera Aligned Material Plane
# (c) 2024 Andrew S. Gordon

import bpy, bpy_extras
import os, json, math

bl_info = {
    "name": "Camera Aligned Material Plane",
    "author": "Andrew S. Gordon",
    "version": (1,2),
    "blender": (4,2,0),
    "location": "File > Import > Import Camera-Aligned Material Plane",
    "description": "Utility for importing image planes with material properties and aligning them to the camera",
    "tooltip": "Camera-Aligned Material Plane",
    "category": "Development",
}

class ImportCamp(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import directory of files as a Camera-Aligned Material Plane"""
    bl_idname = "object.import_camp" # Should this be object?
    bl_label = "Camera-Aligned Material Plane"
    
    def execute(self, context):
        """Read in the selected directory as a Camera-Aligned Material Plane"""
        plane = self.import_material_plane()
        camera = bpy.context.scene.camera # Assume the active camera is the target camera
        if plane and camera:
            self.align_plane_to_camera(plane, camera)
        return {'FINISHED'}
    
    def camp_properties(self):
        """Read the properties.json file"""
        properties_path = os.path.join(self.filepath, "properties.json")
        if not os.path.exists(properties_path):
            raise FileNotFoundError(f"{properties_path} does not exist")
        else:
            with open(properties_path) as f:
                result = json.load(f)
            return result
    
    def offset(self, location, offset): # (100,100) (50,50) => (150,150)
        return (location[0] + offset[0], location[1] + offset[1])

    def import_material_plane(self):
        """Import the files in the given directory as a material plane"""
        props = self.camp_properties()
        if 'type' not in props or props['type'] not in ['movie', 'image']:
            raise Exception('properties.json must specify a "type" with value "image" or "movie"')
        
        # diffuse is base image mesh
        if not 'diffuse' in props:
            raise Exception("properties.json does not specify a diffuse image basename (required).")
        diffuse_path = os.path.join(self.filepath, props['diffuse'])
        bpy.ops.image.import_as_mesh_planes(filepath=diffuse_path, files=[{'name':props['diffuse']}], directory=self.filepath)
        plane = bpy.context.object
        material = plane.material_slots[0].material
        material.use_nodes = True
        nodes = material.node_tree.nodes
        diffuse_node = nodes.get('Image Texture')
        
        # bsdf_node and output_node
        bsdf_node = nodes.get('Principled BSDF')
        bsdf_node.inputs['IOR'].default_value = 1.0
        output_node = nodes.get('Material Output')
        diffuse_node.location = self.offset(bsdf_node.location, (-600, 0)) # left two columns
        
        # mask_node
        if 'mask' in props:
            mask_path = os.path.join(self.filepath, props['mask'])
            mask_node = nodes.new('ShaderNodeTexImage')
            mask_node_image = bpy.data.images.load(mask_path)
            mask_node.image = mask_node_image
            if props['type'] == 'movie':
                mask_node.image_user.use_auto_refresh = True
                mask_node.image_user.frame_duration = diffuse_node.image_user.frame_duration
            mask_node.image.colorspace_settings.name = 'Non-Color'
            mask_node.location = self.offset(diffuse_node.location, (0,-400)) # down one row
            material.node_tree.links.new(mask_node.outputs['Color'], bsdf_node.inputs['Alpha'])
     
        # normalmap_node and normal_node    
        if 'normal' in props:
            normalmap_node = nodes.new('ShaderNodeNormalMap')
            # normal
            normal_path = os.path.join(self.filepath, props['normal'])
            normal_node = nodes.new('ShaderNodeTexImage')
            normal_node_image = bpy.data.images.load(normal_path)
            normal_node.image = normal_node_image
            if props['type'] == 'movie':
                normal_node.image_user.use_auto_refresh = True
                normal_node.image_user.frame_duration = diffuse_node.image_user.frame_duration
            normal_node.image.colorspace_settings.name = 'Non-Color'
            material.node_tree.links.new(normalmap_node.outputs['Normal'], bsdf_node.inputs['Normal'])
            material.node_tree.links.new(normal_node.outputs['Color'], normalmap_node.inputs['Color'])
            normal_node.location = self.offset(diffuse_node.location, (0,-800)) # down two row from diffuse
            normalmap_node.location = self.offset(normal_node.location, (300,0)) # right one column            
        
        # Add solidify modifier to prevent strong backlight from seeping through
        plane.modifiers.new(name="Solidify", type='SOLIDIFY')
        
        # Set the name of the plane to match that in the properties.json 
        plane.name = props['name']

        # return plane
        return plane
    
    def align_plane_to_camera(self, plane, camera):
        """Align the material plane to the camera"""
        # Ensure plane has scale of (1,1,1)
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
        # Resize the plane to simplify math
        resize = 2 / plane.dimensions[0]
        plane.scale[0] = resize
        plane.scale[1] = resize
        with bpy.context.temp_override(active_object=plane):
            bpy.ops.object.transform_apply(location=False, rotation=False)
        # Set the new scale based on current distance to fill camera
        angle = camera.data.angle_x
        scale = distance * math.tan(angle/2)
        plane.scale[0] = scale
        plane.scale[1] = scale
        # Setup driver for scale to fit/fill camera when distance changes
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
    
### Registration of functionality

def menu_func_import(self, context):
    self.layout.operator(ImportCamp.bl_idname)
    
def register():
    bpy.utils.register_class(ImportCamp)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportCamp)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()