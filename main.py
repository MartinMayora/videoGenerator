import src.conseguirVideos as conseguirVideos
import src.DeteccionCara as DeteccionCara
import src.comando as comando
import os
import src.cleanUp as cleanUp

def main():
    choice = input("Choose an option (1 = Top clips from a category, 2 = Top clips from a creator): ")
    language = input("Choose the language (english, spanish, none): ").lower()
    commands = []
    
    
    creatorNames = conseguirVideos.conseguirVids(choice, language)
    
    for creator in creatorNames:
        aux = f"./build/videos/{creator['thumbnail']}"
        coords = DeteccionCara.get_interactive_coordinates(aux)
        print(coords['x'])
        creator['x'] = coords['x']
        creator['y'] = coords['y']
        
    for creator in creatorNames:
        aAgregar = comando.crearComandoShort(creator['video'], creator['name'], creator['x'], creator['y'])
        print(aAgregar)
        commands.append(aAgregar)
        
    
    for command in commands:
        os.system(command)
    
    cleanUp.clear_videos_folder()
if __name__ == "__main__":
    main()
