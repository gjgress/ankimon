from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

def open_browser_window():
    """Opens the PokePaste website in the default web browser.

    This function is used to share Pokémon team compositions and battle logs.
    """
    url = "https://pokepast.es/"
    QDesktopServices.openUrl(QUrl(url))

def open_team_builder():
    """Opens the Pokémon Showdown Team Builder in the default web browser.

    This provides a convenient way for users to create and manage their teams.
    """
    team_builder_url = "https://play.pokemonshowdown.com/teambuilder"
    QDesktopServices.openUrl(QUrl(team_builder_url))

def rate_addon_url():
    """Opens the AnkiWeb page for rating the Ankimon addon."""
    rating_url = "https://ankiweb.net/shared/review/1908235722"
    QDesktopServices.openUrl(QUrl(rating_url))

def report_bug():
    """Opens the GitHub issues page for reporting bugs."""
    bug_url = "https://github.com/Unlucky-Life/ankimon/issues"
    QDesktopServices.openUrl(QUrl(bug_url))

def join_discord_url():
    """Opens the invite link for the official Ankimon Discord server."""
    discord_url = "https://discord.gg/hcq53X5mcu"
    QDesktopServices.openUrl(QUrl(discord_url))

def open_leaderboard_url():
    """Opens the official Ankimon leaderboard website."""
    leaderboard_url = "https://leaderboard.ankimon.com/"
    QDesktopServices.openUrl(QUrl(leaderboard_url))