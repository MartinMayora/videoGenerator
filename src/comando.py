def crearComandoShort(video_file, nombre, crop_x, crop_y):
    command = (
        f'ffmpeg -y -i ./build/Videos/{video_file} '
        f'-vf "scale=1920:1080, crop=360:240:{crop_x}:{crop_y},scale=720:480" top_crop_scaled.mp4 && '
        f'ffmpeg -y -i ./build/Videos/{video_file} '  
        f'-vf "scale=1920:1080, crop=720:800:(in_w-720)/2:(in_h-800)" bottom_crop.mp4 && '
        f'ffmpeg -y -i bottom_crop.mp4 -i top_crop_scaled.mp4 -i ./src/utils/twitchLogo.png '
        f'-filter_complex "[1:v][0:v]vstack=inputs=2[video]; '
        f'[2:v]scale=86:100[overlay]; '
        f'[video][overlay]overlay=100:430,drawtext=text=\'{nombre}\''
        f':fontfile=./src/utils/TwitchyTV.ttf:x=200:y=440:fontsize=60:fontcolor=white" '
        f'-s 720x1280 ./build/output/{video_file}'
    )
    return command
