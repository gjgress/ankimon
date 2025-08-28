
var button_place = document.getElementById('outer');
if (button_place) { // Only modify if 'outer' element exists
    button_place.innerHTML += `<button id="playButton" onclick="toggleSound()"></button>`;
    button_place.innerHTML += `<button id="skipButton" onclick="skipSound()"></button>`;
    button_place.innerHTML += `<input type="range" id="volumeSlider" min="0" max="1" step="0.01" value="0.5">`;
} else {
    console.warn("Element with ID 'outer' not found. Music player buttons may not be initialized.");
}

document.addEventListener('DOMContentLoaded', function() {
    // Check if ambientSound element exists before proceeding
    var ambientSound = document.getElementById('ambientSound');
    if (!ambientSound) {
        console.warn("Audio element with ID 'ambientSound' not found. Ambient sounds will not play.");
        return; // Exit if the audio element is not present
    }

    var songs = [
        'ambient-sound1.mp3',
        'ambient-sound2.mp3',
        'ambient-sound3.mp3'
    ];

    var currentSongIndex = 0;
    var ambientSound = document.getElementById('ambientSound');
    var playButton = document.getElementById('playButton');
    var skipButton = document.getElementById('skipButton');
    var volumeSlider = document.getElementById('volumeSlider');

    // Function to play the current song
    function playCurrentSong() {
        var currentSong = songs[currentSongIndex];
        ambientSound.src = 'path/to/your/' + currentSong; // Adjust path as needed
        ambientSound.play();
        playButton.classList.add('playing');
        console.log('Now playing: ' + currentSong);
    }

    // Event listener for play/pause button click
    playButton.addEventListener('click', function() {
        if (ambientSound.paused) {
            playCurrentSong();
        } else {
            ambientSound.pause();
            playButton.classList.remove('playing');
        }
    });

    // Function to go to the next song
    function nextSong() {
        var previousIndex = currentSongIndex;
        currentSongIndex = (currentSongIndex + 1) % songs.length;
        playCurrentSong();
        if (currentSongIndex === 0 && previousIndex !== 0) {
            console.log('Looped back to the start of the playlist.');
        }
    }

    // Event listener for skip button click
    skipButton.addEventListener('click', function() {
        nextSong();
    });

    // Event listener for audio ended (song finished)
    ambientSound.addEventListener('ended', function() {
        nextSong();
    });

    // Event listener for volume slider change
    volumeSlider.addEventListener('input', function() {
        ambientSound.volume = volumeSlider.value;
    });

    // Initially play the first song
    playCurrentSong();
});
