#This Source Code is not from me, its from audiovisualfeedback
#https://github.com/AnKing-VIP/anki-audiovisual-feedback/blob/master/addon/audios.py
#right now there is no clear license in this, therefore I see this as
#open as MIT License or atleast opensource due to posting on GitHub
#audiovisualfeedback is an addon developed with the help of the Anking or Atleast under his Account
#The Code here was commited from BlueGreenMagick  https://github.com/BlueGreenMagick
#If the author has any issues with this being posted here, please let me know!

from pathlib import Path
from typing import Literal, Union

from aqt import mw, gui_hooks
from aqt.webview import AnkiWebView, WebContent
import aqt.sound
from aqt.sound import SoundOrVideoTag, AVPlayer

try:  # 2.1.50+
    from anki.utils import is_win
except:
    from anki.utils import isWin as is_win  # type: ignore


class CustomAVPlayer(AVPlayer):
    """A custom audio player that prevents audio from being interrupted.

    This class extends Anki's default AVPlayer to introduce a 'no_interrupt'
    mode, ensuring that certain sounds play to completion without being cut
    off by other audio events in Anki.
    """
    no_interrupt = False

    def _on_play_without_interrupt_finished(self) -> None:
        """Resets the interrupt flag when non-interruptible audio finishes."""
        self.no_interrupt = False
        self._on_play_finished()

    def _stop_if_playing(self) -> None:
        """Stops the currently playing audio, unless it's non-interruptible."""
        if self.current_player and not self.no_interrupt:
            self.current_player.stop()

    def play_without_interrupt(self, file: Path) -> None:
        """Plays an audio file without being interrupted by other sounds.

        This method ensures that the audio playback is not stopped by other
        sounds, which is crucial for Ankimon's sound effects during reviews.

        Args:
            file: The path to the audio file to be played.
        """
        if self.current_player:
            self.current_player.stop()

        self.no_interrupt = True
        tag = SoundOrVideoTag(filename=str(file.resolve()))
        best_player = self._best_player_for_tag(tag)
        if best_player:
            self.current_player = best_player
            gui_hooks.av_player_will_play(tag)
            self.current_player.play(tag, self._on_play_without_interrupt_finished)
        else:
            print(f"ERROR: no players found for {tag}")


def will_use_audio_player() -> None:
    """Monkey-patches Anki's default audio player to use custom behavior.

    This function is a critical setup step that replaces methods in Anki's
    global AVPlayer instance with the custom, non-interruptible versions
    defined in this module. This allows the addon to control audio playback
    behavior globally.
    """
    aqt.sound.av_player.no_interrupt = False
    AVPlayer._on_play_without_interrupt_finished = (
        CustomAVPlayer._on_play_without_interrupt_finished
    )
    AVPlayer._stop_if_playing = CustomAVPlayer._stop_if_playing  # type: ignore
    AVPlayer.play_without_interrupt = CustomAVPlayer.play_without_interrupt


def audio(file: Path) -> None:
    """Plays a non-interruptible audio file.

    A convenience wrapper around `play_without_interrupt` for cleaner code.

    Args:
        file: The path to the audio file.
    """
    aqt.sound.av_player.play_without_interrupt(file)


def force_stop_audio() -> None:
    """Forces the currently playing audio to stop, bypassing any protections."""
    av_player = aqt.sound.av_player
    if av_player.current_player:
        av_player.current_player.stop()
