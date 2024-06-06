# Camera Aligned Material Plane
A Blender add-on for aligning material-based image planes to a camera's viewport.

***Work-in-progress! Use at your own risk!***

## About

In 3D modeling software such as Blender, an "image plane" is a 2D rectangle positioned in 3D space, where the surface of the rectangle displays a photograph or other image. Such planes may include an alpha channel that removes the background from the image, allowing a 2D foreground object to be placed anywhere in the 3D scene. 

A "material plane" sets the material properties of the image plane (e.g., diffuse, specular, normal layers) to enable Physically Based Rendering, allowing the foreground object to interact with the synthetic lighting environment as if it were another 3D object in the scene. 

A "camera aligned material plane" (CAMP) positions and rotates the plane to be flush and in the center of the virtual camera's viewport, with a virtual distance to the camera the same as the distance between the real-world world camera and the real-world foreground object, and the scale of the plane set to fill the virtual camera's entire field of view.

When positioned and scaled correctly, a CAMP appearing in a virtual camera retains the pixel resolution of the original real-world imagery, but where each pixel of the foreground object has been relit using Physically Based Rendering.

## Basic use

This workflow was tested in Blender 4.1

1. Enable add-on "Import-Export: Import Images as Planes"
1. Install add-on "camera_aligned_material_plane.py" from this repository.
1. Import images planes into your scene.
1. With the plane selected as the active object, select Object > Align Plane to Camera.
1. Position the camera and plane's distance to camera as needed.

This add-on operator does several things to a selected image plane: locks its rotation to the camera's rotation, parents it to the camera and locks its x and y local coordinates to 0, and uses drivers to scale the plane to fill the camera viewport regardless of its distance to the camera.