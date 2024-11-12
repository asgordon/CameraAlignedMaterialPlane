# camp.py
# Camera Aligned Material Plane
# (c) 2024 Andrew S. Gordon

import bpy, bpy_extras
from bpy.props import StringProperty, BoolProperty
import os, json, math

bl_info = {
    "name": "Camera Aligned Material Plane",
    "author": "Andrew S. Gordon",
    "version": (1,3),
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
    
    # The following properties force ImportHelper to only select directories.
    
    directory: StringProperty()

    filter_glob: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    # This option creates a second CAMP for the background
    
    background_boolean: BoolProperty( 
        name='Include background plane', 
        description='Creates two planes rather than one, where the second is a backgroud CAMP lacking a mask. Use when relighting a video', 
        default=False, 
        )
        
    # EXECUTE
    
    def execute(self, context):
        """Read in the selected directory as a Camera-Aligned Material Plane"""
        # load the properties
        props = self.camp_properties()
        # identify the camera
        camera = bpy.context.scene.camera # Assume the active camera is the target camera
        # create foreground_plane
        foreground_plane = self.import_material_plane(props)
        # resize plane
        self.resize_plane(foreground_plane)
        # parent plane to camera
        self.parent_plane_to_camera(foreground_plane, camera)
        # create camp_depth (empty)
        foreground_depth = self.create_depth(camera, props['name'] + "_depth")
        # add depth driver to camp
        self.add_depth_driver(foreground_plane, foreground_depth)
        # add scale driver to camp
        self.add_scale_driver(foreground_plane, foreground_depth, camera)
        
        if 'depth' in props:
            self.add_depth_keyframes(props['depth'], foreground_depth)
        else:
            self.set_depth(foreground_depth, -3.0) # default
            
        if self.background_boolean:
            # create background_plane
            background_plane = self.import_material_plane(props, mask=False)
            # resize plane
            self.resize_plane(background_plane)
            # parent plane to camera
            self.parent_plane_to_camera(background_plane, camera)
            # create camp_background_depth (empty)
            background_depth = self.create_depth(camera, props['name'] + "_background_depth")
            # add depth driver to background camp
            self.add_depth_driver(background_plane, background_depth)
            # add scale driver to background
            self.add_scale_driver(background_plane, background_depth, camera)
            
            if 'depth' in props:
                self.add_depth_keyframes(props['depth'], background_depth, 'bg')
            else:
                self.set_depth(background_depth, -6.0) # default
               
        return {'FINISHED'}
    
    def camp_properties(self):
        """Read the properties.json file"""
        properties_path = os.path.join(self.directory, "properties.json")
        if not os.path.exists(properties_path):
            raise FileNotFoundError(f"{properties_path} does not exist")
        else:
            with open(properties_path) as f:
                result = json.load(f)
            return result
    
    def import_material_plane(self, props, mask=True):
        """Import the files in the given camp directory as a material plane"""
        if 'type' not in props or props['type'] not in ['movie', 'image']:
            raise Exception('properties.json must specify a "type" with value "image" or "movie"')
        
        # diffuse is base image mesh
        if not 'diffuse' in props:
            raise Exception("properties.json does not specify a diffuse image basename (required).")
        diffuse_path = os.path.join(self.directory, props['diffuse'])
        bpy.ops.image.import_as_mesh_planes(filepath=diffuse_path, files=[{'name':props['diffuse']}], directory=self.directory, overwrite_material=False, align_axis='+Z')
        
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
        if mask and 'mask' in props:
            mask_path = os.path.join(self.directory, props['mask'])
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
            normal_path = os.path.join(self.directory, props['normal'])
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
        
        # Set the name of the plane to match that in the properties.json 
        plane.name = "CAMP " + props['name'] 

        # return plane
        return plane
    
    def offset(self, location, offset): # (100,100) (50,50) => (150,150)
        """Utility function for offsetting position of shader nodes"""
        return (location[0] + offset[0], location[1] + offset[1])    

    def resize_plane(self, plane):
        """Set the initial scale to simplify math"""
        # Ensure plane has scale of (1,1,1)
        with bpy.context.temp_override(active_object=plane):
            bpy.ops.object.transform_apply(location=False, rotation=False)
        # Resize the plane to simplify math
        resize = 2 / plane.dimensions[0]
        plane.scale[0] = resize
        plane.scale[1] = resize
        with bpy.context.temp_override(active_object=plane):
            bpy.ops.object.transform_apply(location=False, rotation=False)

    def parent_plane_to_camera(self, plane, camera):
        """Create a child-of constraint for plane to camera, ignoring scale"""
        bpy.context.view_layer.objects.active = plane # set plane as active object
        bpy.ops.object.constraint_add(type='CHILD_OF')
        plane.constraints['Child Of'].use_scale_x = False
        plane.constraints['Child Of'].use_scale_y = False
        plane.constraints['Child Of'].use_scale_z = False
        plane.constraints['Child Of'].target = camera
        bpy.ops.constraint.childof_clear_inverse(constraint="Child Of", owner='OBJECT')

    def create_depth(self, camera, name):
        """Add an empty object to the scene to animate distance of plane to camera"""
        bpy.ops.object.empty_add() # creates new empty, sets as active object
        empty = bpy.context.active_object 
        empty.name = name
        empty.parent = camera
        return empty

    def add_depth_driver(self, plane, empty):
        """Add driver to the plane that sets the z-location to that of the empty"""
        driver = plane.driver_add("location", 2).driver
        empty_z = driver.variables.new()
        empty_z.name = "depth"
        empty_z.targets[0].id = empty
        empty_z.targets[0].data_path = "location[2]"
        driver.expression = "depth"

    def add_scale_driver(self, plane, empty, camera):
        """Add scale driver (x and y) to fill frame based on the camera angle and distance to camera"""
        angle = camera.data.angle_x # fill width
        # scale x
        driver_x = plane.driver_add("scale", 0).driver
        var_x = driver_x.variables.new()
        var_x.name = "varx"
        var_x.type = 'SINGLE_PROP'
        var_x.targets[0].id = empty
        var_x.targets[0].data_path = "location[2]"
        driver_x.expression = f"-varx*tan({angle}/2)"
        # scale y
        driver_y = plane.driver_add("scale", 1).driver
        var_y = driver_y.variables.new()
        var_y.name = "vary"
        var_y.type = 'SINGLE_PROP'
        var_y.targets[0].id = empty
        var_y.targets[0].data_path = "location[2]"
        driver_y.expression = f"-vary*tan({angle}/2)"
        
    def add_depth_keyframes(self, filename, empty, column='fg'): # use column='bg' for background CAMP
        """Read csv file containing depth information and animate the depth empties using keyframes"""
        depth_path = os.path.join(self.directory, filename)
        if not os.path.exists(depth_path):
            raise Exception("Couldn't find {csv_path} when trying to add distance keyframes. Check properties.json file.")
        with open(depth_path) as csv_file:
            lines = csv_file.readlines()
        columns = [part.strip() for part in lines[0].split(',')]
        column_index = columns.index(column)
        for line in lines[1:]: # skip first line
            parts = line.split(',') # typically [frame, fg, bg]
            empty.location = (0, 0, -float(parts[column_index]))
            empty.keyframe_insert(data_path="location", frame = int(parts[0]) + 1) # blender frames start at 1, not 0
            
    def set_depth(self, empty, value):
        empty.location = (0, 0, value)
    
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