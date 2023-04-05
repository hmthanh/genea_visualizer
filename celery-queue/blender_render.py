import sys
import os
import bpy
import math
import random
from mathutils import Vector
import time
import argparse
import tempfile
from pathlib import Path

# cleans up the scene and memory
def clear_scene():
    for block in bpy.data.meshes:       bpy.data.meshes.remove(block)
    for block in bpy.data.materials:    bpy.data.materials.remove(block)
    for block in bpy.data.textures:     bpy.data.textures.remove(block)
    for block in bpy.data.images:       bpy.data.images.remove(block)  
    for block in bpy.data.curves:       bpy.data.curves.remove(block)
    for block in bpy.data.cameras:      bpy.data.cameras.remove(block)
    for block in bpy.data.lights:       bpy.data.lights.remove(block)
    for block in bpy.data.sounds:       bpy.data.sounds.remove(block)
    for block in bpy.data.armatures:    bpy.data.armatures.remove(block)
    for block in bpy.data.objects:      bpy.data.objects.remove(block)
    for block in bpy.data.actions:      bpy.data.actions.remove(block)
            
    if bpy.context.object == None:          bpy.ops.object.delete()
    elif bpy.context.object.mode == 'EDIT': bpy.ops.object.mode_set(mode='OBJECT')
    elif bpy.context.object.mode == 'POSE': bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.delete()
    
def setup_scene(cam_pos, cam_rot, actor1, actor2, arm1, arm2):
    
    # Camera Main
    name = 'Main'
    add_camera(cam_pos, cam_rot, name)
    
    # 2 new camers needed (1 behind each actor)
    # readjust camera that views both actors
    
    # Camera actor 1
    actor1c = actor1.children[0]
    actor1c.name = 'actor1_loc'
    arm1 = bpy.data.objects[arm1]
    actor1_bvh_offset_x = arm1.matrix_world @ arm1.data.bones['body_world'].head_local
    actor1_bvh_offset_y = arm1.matrix_world @ arm1.data.bones['b_root'].head_local
    actor1_bvh_offset_z = Vector((0, 0, 1.5)) + (arm1.matrix_world @ arm1.data.bones['body_world'].head_local)
    cam_pos = [actor1_bvh_offset_x[0], actor1_bvh_offset_y[1], actor1_bvh_offset_z[2]]
    cam_rot = [math.radians(75), 0, math.radians(90)]
    add_camera(cam_pos, cam_rot, actor1.name)
    
    # Camera actor 2
    actor2c = actor2.children[0]
    actor2c.name = 'actor2_loc'
    arm2 = bpy.data.objects[arm2]
    actor2_bvh_offset_x = arm2.matrix_world @ arm2.data.bones['body_world'].head_local
    actor2_bvh_offset_y = arm2.matrix_world @ arm2.data.bones['b_root'].head_local
    actor2_bvh_offset_z = Vector((0, 0, 1.5)) + (arm2.matrix_world @ arm2.data.bones['body_world'].head_local)
    cam_pos = [actor2_bvh_offset_x[0], actor2_bvh_offset_y[1], actor2_bvh_offset_z[2]]
    cam_rot = [math.radians(75), 0, math.radians(-90)]
    add_camera(cam_pos, cam_rot, actor2.name)
    
    # Floor Plane
    bpy.ops.mesh.primitive_plane_add(size=20, location=[0, 0, 0], rotation=[0, 0, 0])
    plane_obj = bpy.data.objects['Plane']
    plane_obj.name = 'Floor'
    plane_obj.scale = [100, 100, 100]
    mat = bpy.data.materials['FloorColor'] #set new material to variable
    plane_obj.data.materials.append(mat) #add the material to the object

def add_camera(cam_pos, cam_rot, name):
    bpy.ops.object.camera_add(enter_editmode=False, location=cam_pos, rotation=cam_rot)
    cam = bpy.data.objects['Camera']
    cam.scale = [5, 25, 5]
    cam.data.lens = 25
    cam.name = name + '_cam'
    bpy.context.scene.camera = cam # add cam so it's rendered
    
def setup_characters(actor1, actor2):
    arm1 = bpy.context.scene.objects[actor1]
    arm2 = bpy.context.scene.objects[actor2]
    arm1.location = [1, 0, 0]
    arm1.rotation_euler[2] = math.radians(-90)
    arm2.location = [-1, 0, 0]
    arm2.rotation_euler[2] = math.radians(90)
    
def get_camera(name):
    cam = bpy.data.objects[name]
    bpy.context.scene.camera = cam

def remove_bone(armature, bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.edit_bones: # deselect the other bones
        if bone.name == bone_name:
            armature.data.edit_bones.remove(bone)
    bpy.ops.object.mode_set(mode='OBJECT')
    
def load_fbx(filepath, name):
    bpy.ops.import_scene.fbx(filepath=filepath, ignore_leaf_bones=True, 
    force_connect_children=True, automatic_bone_orientation=False)
    remove_bone(bpy.data.objects['Armature'], 'b_r_foot_End')
    bpy.data.objects['Armature'].name = name
        
def load_bvh(filepath):
    bpy.ops.import_anim.bvh(filepath=filepath, use_fps_scale=False,
    update_scene_fps=True, update_scene_duration=True, global_scale=0.01)

def add_materials(work_dir, name):
    mat = bpy.data.materials.new('gray')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(os.path.join(work_dir, 'model', "LowP_03_Texture_ColAO_grey5.jpg"))
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    obj = bpy.data.objects['LowP_01']
    obj.modifiers['Armature'].use_deform_preserve_volume=True
    # Assign it to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # set new material to variable
    mat = bpy.data.materials.new(name="FloorColor")
    mat.diffuse_color = (0.15, 0.4, 0.25, 1)
    
def constraintBoneTargets(armature = 'Armature', rig = 'None', mode = 'full_body'):
    armobj = bpy.data.objects[armature]
    for ob in bpy.context.scene.objects: ob.select_set(False)
    bpy.context.view_layer.objects.active = armobj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    for bone in bpy.context.selected_pose_bones:
        # Delete all other constraints
        for c in bone.constraints:
            bone.constraints.remove( c )
        # Create body_world location to fix floating legs
        if bone.name == 'body_world' and mode == 'full_body':
            constraint = bone.constraints.new('COPY_LOCATION')
            constraint.target = bpy.context.scene.objects[rig]
            temp = bone.name.replace('BVH:','')
            constraint.subtarget = temp
        # Create all rotations
        if bpy.context.scene.objects[armature].data.bones.get(bone.name) is not None:
            constraint = bone.constraints.new('COPY_ROTATION')
            constraint.target = bpy.context.scene.objects[rig]
            temp = bone.name.replace('BVH:','')
            constraint.subtarget = temp
    if mode == 'upper_body':
        bpy.context.object.pose.bones["b_root"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_r_upleg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_r_leg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_l_upleg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_l_leg"].constraints["Copy Rotation"].mute = True
    bpy.ops.object.mode_set(mode='OBJECT')
    
def load_audio(filepath):
    bpy.context.scene.sequence_editor_create()
    bpy.context.scene.sequence_editor.sequences.new_sound(
        name='AudioClip',
        filepath=filepath,
        channel=1,
        frame_start=0
    )
    
def render_video(output_dir, picture, video, bvh1_fname, bvh2_fname, actor1, actor2, render_frame_start, render_frame_length, res_x, res_y):
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.display.shading.light = 'MATCAP'
    bpy.context.scene.display.render_aa = 'FXAA'
    bpy.context.scene.render.resolution_x=int(res_x)
    bpy.context.scene.render.resolution_y=int(res_y)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = render_frame_start
    bpy.context.scene.frame_set(render_frame_start)
    if render_frame_length > 0:
        bpy.context.scene.frame_end = render_frame_start + render_frame_length
    
    if picture:
        bpy.context.scene.render.image_settings.file_format='PNG'
        get_camera('Main_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath=os.path.join(output_dir, 'Main.png')
        bpy.ops.render.render(write_still=True)
        get_camera(actor1 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = True
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}.png'.format(bvh1_fname))
        bpy.ops.render.render(write_still=True)
        get_camera(actor2 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = True
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}.png'.format(bvh2_fname))
        bpy.ops.render.render(write_still=True)
        
    if video:
        print(f"total_frames {render_frame_length}", flush=True)
        bpy.context.scene.render.image_settings.file_format='FFMPEG'
        bpy.context.scene.render.ffmpeg.format='MPEG4'
        bpy.context.scene.render.ffmpeg.codec = "H264"
        bpy.context.scene.render.ffmpeg.ffmpeg_preset='REALTIME'
        bpy.context.scene.render.ffmpeg.constant_rate_factor='HIGH'
        bpy.context.scene.render.ffmpeg.audio_codec='MP3'
        bpy.context.scene.render.ffmpeg.gopsize = 30
        get_camera('Main_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath=os.path.join(output_dir, 'Main_')
        bpy.ops.render.render(animation=True, write_still=True)
        get_camera(actor1 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = True
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_'.format(bvh1_fname))
        bpy.ops.render.render(animation=True, write_still=True)
        get_camera(actor2 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = True
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_'.format(bvh2_fname))
        bpy.ops.render.render(animation=True, write_still=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i1', '--input1', help='Input file name of the first BVH to render.', type=Path, required=True)
    parser.add_argument('-i2', '--input2', help='Input file name of the second BVH to render.', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=Path)
    parser.add_argument('-s', '--start', help='Which frame to start rendering from.', type=int, default=0)
    parser.add_argument('-r', '--rotate', help='Rotates the character for better positioning in the video frame. Use "cw" for 90-degree clockwise, "ccw" for 90-degree counter-clockwise, "flip" for 180 degree rotation, or leave at "default" for no rotation.', choices=['default', 'cw', 'ccw', 'flip'], type=str, default="default")
    parser.add_argument('-d', '--duration', help='How many consecutive frames to render.', type=int, default=3600)
    parser.add_argument('-a', '--input_audio', help='Input file name of an audio clip to include in the final render.', type=Path)
    parser.add_argument('-p', '--png', action='store_true', help='Renders the result in a PNG-formatted image.')
    parser.add_argument('-v', '--video', action='store_true', help='Renders the result in an MP4-formatted video.')
    parser.add_argument('-m', "--visualization_mode", help='The visualization mode to use for rendering.',type=str, choices=['full_body', 'upper_body'], default='full_body')
    parser.add_argument('-rx', '--res_x', help='The horizontal resolution for the rendered videos.', type=int, default=1024)
    parser.add_argument('-ry', '--res_y', help='The vertical resolution for the rendered videos.', type=int, default=768)  
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    return vars(parser.parse_args(args=argv))

def main():
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')
        
    if bpy.ops.text.run_script.poll():
        print('[INFO] Script is running in Blender UI.')
        SCRIPT_DIR = Path(bpy.context.space_data.text.filepath).parents[0]
        ##################################
        ##### SET ARGUMENTS MANUALLY #####
        ##### IF RUNNING BLENDER GUI #####
        ##################################
        ARG_BVH1_PATHNAME = SCRIPT_DIR / 'test/' / 'session15_take17_noFingers_deep5_SL_30fps-normalized.bvh'
        ARG_BVH2_PATHNAME = SCRIPT_DIR / 'test/' / 'session15_take17_noFingers_shallow13_SL_30fps-normalized-faced.bvh'
#        ARG_AUDIO_FILE_NAME = SCRIPT_DIR / 'test/session14_take5' / 'session14_take5.wav' # set to None for no audio
        ARG_IMAGE = True
        ARG_VIDEO = False
        ARG_START_FRAME = 0
        ARG_DURATION_IN_FRAMES = 360
        ARG_ROTATE = 'default'
        ARG_RESOLUTION_X = 1024
        ARG_RESOLUTION_Y = 768
        ARG_MODE = 'full_body'
        # might need to adjust output directory
        ARG_OUTPUT_DIR = ARG_BVH1_PATHNAME.parents[0]
    else:
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = Path(os.path.realpath(__file__)).parents[0]
        # process arguments
        args = parse_args()
        ARG_BVH1_PATHNAME = args['input1']
        ARG_BVH2_PATHNAME = args['input2']
        ARG_AUDIO_FILE_NAME = args['input_audio'].resolve() if args['input_audio'] else None
        ARG_IMAGE = args['png']
        ARG_VIDEO = args['video'] # set to 'False' to get a quick image preview
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_ROTATE = args['rotate']
        ARG_RESOLUTION_X = args['res_x']
        ARG_RESOLUTION_Y = args['res_y']
        ARG_MODE = args['visualization_mode']
        # might need to adjust output directory
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else ARG_BVH1_PATHNAME.parents[0]
        
        
    if ARG_MODE not in ["full_body", "upper_body"]:
        raise NotImplementedError("This visualization mode is not supported ({})!".format(ARG_MODE))
    
    # FBX file
    FBX_MODEL = os.path.join(SCRIPT_DIR, 'model', "GenevaModel_v2_Tpose_Final.fbx")
    BVH1_NAME = os.path.basename(ARG_BVH1_PATHNAME).replace('.bvh','')
    BVH2_NAME = os.path.basename(ARG_BVH2_PATHNAME).replace('.bvh','')

    start = time.time()
    
    clear_scene()
    OBJ1_friendly_name = 'OBJ1'
    load_fbx(FBX_MODEL, OBJ1_friendly_name)
    add_materials(SCRIPT_DIR, OBJ1_friendly_name)
    load_bvh(str(ARG_BVH1_PATHNAME))
    constraintBoneTargets(armature = OBJ1_friendly_name, rig = BVH1_NAME, mode = ARG_MODE)
    
    OBJ2_friendly_name = 'OBJ2'
    load_fbx(FBX_MODEL, OBJ2_friendly_name)
    add_materials(SCRIPT_DIR, OBJ2_friendly_name)
    load_bvh(str(ARG_BVH2_PATHNAME))
    constraintBoneTargets(armature = OBJ2_friendly_name, rig = BVH2_NAME, mode = ARG_MODE)
#    setup_characters(BVH1_NAME, BVH2_NAME)
    
    print(ARG_OUTPUT_DIR)
    
    # 05/04/2023 fix main camera orientation, fix character rotation and personal cameras
    if ARG_MODE == "full_body":     CAM_POS = [0, -3, 1.1]
    elif ARG_MODE == "upper_body":  CAM_POS = [0, -2.45, 1.3]
    MAIN_CAM_ROT = [math.radians(90), 0, 0]
    setup_scene(CAM_POS, MAIN_CAM_ROT, bpy.data.objects[OBJ1_friendly_name], bpy.data.objects[OBJ2_friendly_name], BVH1_NAME, BVH2_NAME)
    
    # for sanity, audio is handled using FFMPEG on the server and the input_audio argument should be ignored
    try:
        ARG_AUDIO_FILE_NAME
    except:
        ARG_AUDIO_FILE_NAME = ''
        
    if ARG_AUDIO_FILE_NAME and not IS_SERVER:
        load_audio(str(ARG_AUDIO_FILE_NAME))
    
    if not os.path.exists(str(ARG_OUTPUT_DIR)):
        os.mkdir(str(ARG_OUTPUT_DIR))
        
    total_frames1 = bpy.data.objects[BVH1_NAME].animation_data.action.frame_range.y
    total_frames2 = bpy.data.objects[BVH2_NAME].animation_data.action.frame_range.y
    if total_frames1 != total_frames2:
        frames = total_frames1 - total_frames2
        print('Frame Difference' + str(frames))
        total_frames = total_frames1
    else:
        total_frames = total_frames1
        print('Frames are equal!')
    render_video(str(ARG_OUTPUT_DIR), ARG_IMAGE, ARG_VIDEO, BVH1_NAME, BVH2_NAME, OBJ1_friendly_name, OBJ2_friendly_name, ARG_START_FRAME, min(ARG_DURATION_IN_FRAMES, total_frames), ARG_RESOLUTION_X, ARG_RESOLUTION_Y)
    
    end = time.time()
    all_time = end - start
    print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    
#Code line
main()
