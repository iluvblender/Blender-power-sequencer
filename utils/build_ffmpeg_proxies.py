"""
Script to generate 25% proxies for Blender with ffmpeg. It walks through your project folder or any folder tree and finds videos and image files.
It only looks for the file types in VIDEO_EXT and IMG_EXT below. Feel free to upload a PR to improve this script and add more.
At the moment it only support 25% proxy generation. For HD and 4k video, I find it's the only size that always gives good performance. 50% of a 4k video is 1920*1080 after all, which is huge to preview on one CPU core like Blender does.

How to use:

- Open the script from the shell like `python build_ffmpeg_proxies.py project_folder`
- The project_folder should be the path to a folder that contains all the files you want to proxy.

You must have ffmpeg installed and available from the command line. Write ffmpeg -v in the shell to check if it's globally available.

The script uses the mpeg-2 video codec. It produces small and clean video files with decent performance in Blender. The result is of a much higher quality than the mjpeg proxies blender generates by default, and takes far less space on your drive.
For images, it respects the original format and transparency, unlike the built-in proxy system.

To improve:

- Use last file changed/timestamp and only rebuild proxies on files that changed
- Add support for more file formats
- Add option or script to clear/remove proxies
- Add a hook in the add-on to run the script from within Blender, with progress logging

Extra ideas:

- Add an optional cli option to generate to a different proxy size (25%, 50%, 100%)
- Add an optional cli option for more efficient codec for performance, size? E.g. h264 and ProRes?
- Currently local proxies only. add an optional master proxy folder to dump all the files? NB: Not a big fan of this. Although it's easier to delete them later or this lets you share them with your team on a server the folder soon becomes cluttered. One master folder with sub-folder per project would be ideal, but it requires more work.
"""

import os
import subprocess
import sys
import logging


def parse_cmd_args():
    if len( sys.argv ) > 1:
        path = os.path.abspath(sys.argv[1])
        if not os.path.exists(path):
            return
        if os.path.isfile(path) and path.endswith('.blend'):
            path = os.path.split(path)[0]
        if not os.path.isdir(path):
            return
        return path

project_folder = parse_cmd_args()
if not project_folder:
    project_folder = '.'
    logging.warning('The folder passed as an argument isn\'t valid. Using the current folder instead')


VIDEO_EXT = ['.mp4', '.mkv']
IMG_EXT = ['.png', '.jpg', '.jpeg']

FFMPEG_VIDEO_COMMAND = ["ffmpeg", "-i", "", "-hide_banner", "-f", "matroska", "-sn", "-an", "-c:v", "mpeg2video", "-b:v", "1800k", "-filter:v", "scale=iw*0.25:ih*0.25", "-y", ""]
FFMPEG_IMAGE_COMMAND = ["ffmpeg", "-i", "", "-hide_banner", "-vf", "scale=iw*0.25:ih*0.25", ""]

ffmpeg_commands = []
img_proxy_folders = []
for dirpath, dirnames, filenames in os.walk(project_folder):
    found_image, found_video = False, False

    if 'BL_proxy' in dirpath:
        continue

    for f in filenames:
        file_path = os.path.join(dirpath, f)
        _, extension = os.path.splitext(f)

        if extension in VIDEO_EXT:
            video_proxy_subdir = os.path.join(dirpath, 'BL_proxy/{!s}/'.format(f))
            if not os.path.isdir(video_proxy_subdir):
                os.makedirs(video_proxy_subdir)

            new_command = [arg for arg in FFMPEG_VIDEO_COMMAND]
            new_command[2] = file_path
            new_command[-1] = os.path.join(video_proxy_subdir, 'proxy_25.avi')
            print(new_command)
            ffmpeg_commands.append(new_command)

        elif extension in IMG_EXT:
            img_proxy_folder = os.path.join(dirpath, 'BL_proxy/images/25/')
            if not found_image:
                if not os.path.isdir(img_proxy_folder):
                    os.makedirs(img_proxy_folder)
                img_proxy_folders.append(img_proxy_folder)
                found_image = True
            new_command = [arg for arg in FFMPEG_IMAGE_COMMAND]
            new_command[2] = file_path
            new_command[-1] = os.path.join(img_proxy_folder, f)
            print(new_command)
            ffmpeg_commands.append(new_command)

for command in ffmpeg_commands:
    process = subprocess.Popen(command)
    process.wait()

for folder in img_proxy_folders:
    # print(folder)
    for img in os.listdir(folder):
        file_path = os.path.join(folder, img)
        # print(file_path)
        os.rename(file_path, file_path + '_proxy.jpg')
