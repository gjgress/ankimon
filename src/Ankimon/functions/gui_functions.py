from ..resources import addon_dir, type_icon_path_resources


def type_icon_path(type):
    png_file = f"{type}.png"
    return type_icon_path_resources / png_file


def move_category_path(category):
    png_file = f"{category}_move.png"
    return addon_dir / "addon_sprites" / png_file
