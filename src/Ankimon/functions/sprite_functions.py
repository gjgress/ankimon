from ..resources import pkmnimgfolder
import os

def get_sprite_path(side, sprite_type, id=132, shiny=False, gender="M"):
    """Constructs the file path for a Pokémon sprite with fallback logic.

    This function dynamically generates the path to a Pokémon's sprite based
    on several parameters, including its view (front or back), type (static
    or animated), Pokédex ID, shiny status, and gender. It includes a robust
    fallback system that searches for alternative sprites if the specific
    requested version is not available, ultimately defaulting to a substitute
    image if no suitable sprite is found.

    Args:
        side (str): The sprite's perspective, typically 'front' or 'back'.
        sprite_type (str): The file format of the sprite, e.g., 'png' or 'gif'.
        id (int, optional): The National Pokédex ID of the Pokémon. Defaults to 132 (Ditto).
        shiny (bool, optional): Whether to retrieve the shiny version of the sprite. Defaults to False.
        gender (str, optional): The gender of the Pokémon ('M' or 'F'). Defaults to 'M'.

    Returns:
        str: The absolute path to the requested sprite image, or a default
             substitute image if no match is found.
    """
    base_path = f"{side}_default_gif" if sprite_type == "gif" else f"{side}_default"

    shiny_path = "shiny/" if shiny else ""
    gender_path = "female/" if gender == "F" else ""

    path = f"{pkmnimgfolder}/{base_path}/{shiny_path}{gender_path}{id}.{sprite_type}"
    default_path = f"{pkmnimgfolder}/front_default/substitute.png"

    # Check if the file exists at the given path
    if os.path.exists(path):
        return path
    else:
        # Suppress log message for expected missing female sprites, as they fall back to male/default.
        if gender != "F":
            print(f"Unable to find path: {path}, trying fallback values.")

        if gender == "F":
            gender_path = ""
            path = f"{pkmnimgfolder}/{base_path}/{shiny_path}{gender_path}{id}.{sprite_type}"
            return path
        elif shiny == True:
            shiny_path = ""
            path = f"{pkmnimgfolder}/{base_path}/{shiny_path}{gender_path}{id}.{sprite_type}"
            return path
        else:
            return default_path