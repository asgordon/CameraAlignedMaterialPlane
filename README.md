# Camera Aligned Material Plane
A Blender add-on for importing an image plane with material properties, and aligning the plane to a virtual camera's viewport.

***Work-in-progress! Use at your own risk!***

## About

In 3D modeling software such as Blender, an "image plane" is a 2D rectangle positioned in 3D space, where the surface of the rectangle displays a photograph or other image. Such planes may include an alpha channel that removes the background from the image, allowing a 2D foreground object to be placed anywhere in the 3D scene. 

A "material plane" sets the material properties of the image plane (e.g., diffuse, specular, normal layers) to enable Physically Based Rendering, allowing the foreground object to interact with the synthetic lighting environment as if it were another 3D object in the scene. 

A "Camera-Aligned Material Plane" (CAMP) positions and rotates the plane to be flush and in the center of the virtual camera's viewport, with a virtual distance to the camera the same as the distance between the real-world world camera and the real-world foreground object, and the scale of the plane set to fill the virtual camera's entire field of view.

When positioned and scaled correctly, a CAMP appearing in a virtual camera retains the pixel resolution of the original real-world imagery, but where each pixel of the foreground object has been relit using Physically Based Rendering.

## Basic use

This workflow was tested in Blender 4.2

1. Install add-on "camera_aligned_material_plane.py" from this repository
1. Select the menu item File > Import > Camera-Aligned Material Plane
1. Select a directory with image/movie textures and a valid properties.json file
1. Position the camera, and adjust plane's distance to camera as needed

When importing a valid CAMP directory, this add-on does several things.
1. Creates an image mesh (plane) with a Principled BSDF shader node that uses the diffuse file as the texture
1. Links the alpha of the BSDF node to an image texture node that uses the mask file
1. Links the normal of the BSDF node to an image texture node that uses the normal file
1. Sets the IOR of the BSDF shader to 1.0
1. Sets the number of frames for the mask and normal textures to equal the diffuse texture (for movie textures), and auto-refresh to True
1. Creates a child-of constraint between the plane and the camera for location and rotation, and clears the inverse transform
1. Adds an empty object to the scene to animate the distance of the plane to the camera, and parents this empty object to the camera
1. Adds a z location driver for the plane to match the empty object
1. Adds a x,y scale driver for the plane to fill the camera's view based on its angle and the distance of the empty object to the camera.

## properties.json

A valid CAMP directory includes a properties.json file, such as this:
```
{
    "version": "1.3", 
    "type": "image", 
    "name": "example1", 
    "diffuse": "example1_diffuse.jpg", 
    "mask": "example1_mask.jpg", 
    "normal": "example1_normal.jpg",
}
```
The "type" can be either "image" or "movie", and the referenced media files should be present in the directory. The "mask" and "normal" entries are optional, but "diffuse" is required. If shot in a flat/diffuse lighting environment, the original image/movie file can be used as the diffuse material.


