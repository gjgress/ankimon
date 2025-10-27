from ..resources import type_icon_path_resources, addon_dir

def type_icon_path(type):
    """Constructs the file path for a Pokémon type icon.

    This function is a simple but essential utility for the addon's UI,
    dynamically generating the path to a Pokémon type's icon based on its
    name. This allows for easy and consistent display of type icons throughout
    the addon.

    Args:
        type (str): The name of the Pokémon type (e.g., 'Fire', 'Water').

    Returns:
        pathlib.Path: The absolute path to the type icon image.
    """
    png_file = f"{type}.png"
    icon_png_file_path = type_icon_path_resources / png_file
    return icon_png_file_path

def move_category_path(category):
    """Constructs the file path for a move category icon.

    Similar to `type_icon_path`, this function generates the path to a move
    category's icon (Physical, Special, or Status). This is crucial for
    providing clear visual cues in the battle interface and other parts of
    the UI.

    Args:
        category (str): The name of the move category (e.g., 'Physical').

    Returns:
        pathlib.Path: The absolute path to the move category icon.
    """
    png_file = f"{category}_move.png"
    category_path = addon_dir / "addon_sprites" / png_file
    return category_path