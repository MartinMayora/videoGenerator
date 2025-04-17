import conseguirVideos
import DeteccionCara
import comando
import os

choice = input("Choose an option (1 = Top clips from a category, 2 = Top clips from a creator): ")
language = input("Choose the language (english, spanish, none): ").lower()
commands = []
creatorNames = conseguirVideos.conseguirVids(choice, language)

for creator in creatorNames:
    aux = f"./build/videos/{creator['thumbnail']}"
    coords = DeteccionCara.deteccionCara(aux)
    creator['x'] = coords['x']
    creator['y'] = coords['y']
    
for creator in creatorNames:
    commands.append(comando.crearComandoShort(creator['video'], creator['name'], creator['x'], creator['y']))

for command in commands:
    os.system(command)