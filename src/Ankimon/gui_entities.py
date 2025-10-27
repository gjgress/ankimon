import markdown
import json
from PyQt6.QtGui import QMovie, QIcon
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QTextEdit, QCheckBox, QPushButton, QMessageBox, QWidget, QScrollArea, QGridLayout, QTextBrowser
from aqt import mw
from aqt.qt import QDialog, qconnect
from aqt.utils import showWarning, showInfo, tooltip
from PyQt6.QtCore import Qt

from .resources import icon_path, addon_dir, eff_chart_html_path, table_gen_id_html_path, mypokemon_path
from .texts import terms_text, pokedex_html_template
from .utils import read_local_file, read_github_file, compare_files, write_local_file, read_html_file
from .pyobj.error_handler import show_warning_with_traceback


class MovieSplashLabel(QLabel):
    """A QLabel that displays an animated GIF as a splash screen.

    This class is used to create a visually engaging loading screen or intro
    sequence for the addon, providing a more polished user experience.
    """
    def __init__(self, gif_path, parent=None):
        """Initializes the splash screen label.

        Args:
            gif_path (str): The file path to the animated GIF.
            parent (QWidget, optional): The parent widget.
        """
        super().__init__(parent)
        self.movie = QMovie(gif_path)
        self.movie.jumpToFrame(0)
        self.setMovie(self.movie)
        self.movie.frameChanged.connect(self.repaint)

    def showEvent(self, event):
        """Starts the animation when the label is shown."""
        self.movie.start()

    def hideEvent(self, event):
        """Stops the animation when the label is hidden."""
        self.movie.stop()

class UpdateNotificationWindow(QDialog):
    """A dialog for displaying update notifications and other important messages.

    This class provides a flexible way to present formatted text to the user,
    supporting both plain HTML and Markdown. It is used to inform users about
    new features, bug fixes, and other important announcements.
    """
    def __init__(self, content, is_markdown=False):
        """Initializes the notification window.

        Args:
            content (str): The content to be displayed, either as HTML or
                           Markdown.
            is_markdown (bool, optional): Whether the content is in Markdown
                                          format.
        """
        super().__init__()
        self.setWindowTitle("Ankimon Notifications")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)  # Enable clickable links
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # If content is markdown, convert to HTML
        if is_markdown:
            import markdown
            html_content = markdown.markdown(content)
        else:
            html_content = content

        self.text_browser.setHtml(html_content)
        layout.addWidget(self.text_browser)
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setLayout(layout)

    def open(self):
        """Displays the notification window."""
        self.exec()

class AgreementDialog(QDialog):
    """A dialog for presenting terms and conditions to the user.

    This dialog is used to ensure that users agree to the addon's terms of
    service before downloading or accessing certain features. It is a crucial
    part of the addon's legal compliance.
    """
    def __init__(self):
        """Initializes the agreement dialog."""
        super().__init__()

        # Setup the dialog layout
        layout = QVBoxLayout()
        # Add a label with the warning message
        title = QLabel("""Please agree to the terms before downloading the information:""")
        subtitle = QLabel("""Terms and Conditions Clause""")
        terms = QLabel(terms_text)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(terms)
         # Ensure the terms QLabel is readable and scrolls if necessary
        terms.setWordWrap(True)
        terms.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Add a checkbox for the user to agree to the terms
        self.checkbox = QCheckBox("I agree to the above named terms.")
        layout.addWidget(self.checkbox)

        # Add a button to proceed
        proceed_button = QPushButton("Proceed")
        proceed_button.clicked.connect(self.on_proceed_clicked)
        layout.addWidget(proceed_button)

        self.setLayout(layout)

    def on_proceed_clicked(self):
        """Handles the proceed button click event.

        If the user has checked the agreement box, the dialog is closed and
        the action is allowed to proceed. Otherwise, a warning is displayed.
        """
        if self.checkbox.isChecked():
            self.accept()  # Close the dialog and return success
        else:
            QMessageBox.warning(self, "Agreement Required", "You must agree to the terms to proceed.")

class Version_Dialog(QDialog):
    """A dialog for displaying the addon's version and update information.

    This dialog is used to inform users about the latest changes and updates
    to the addon. It reads the update information from a local Markdown file
    and displays it in a readable format.
    """
    def __init__(self):
        """Initializes the version dialog."""
        super().__init__()
        self.setWindowTitle("Ankimon Notifications")
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)  # Enable clickable links
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.local_file_path = addon_dir / "updateinfos.md"
        self.local_content = read_local_file(self.local_file_path)
        self.html_content = markdown.markdown(self.local_content)
        self.text_browser.setHtml(self.html_content)
        layout.addWidget(self.text_browser)
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setLayout(layout)

    def open(self):
        """Displays the version dialog."""
        self.exec()

class License(QWidget):
    """A window for displaying the addon's license information."""
    def __init__(self):
        """Initializes the license window."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface of the license window."""
        self.setWindowTitle("AnkiMon License")

        # Create a label and set HTML content
        label = QLabel()
        html_content = self.read_html_file(f"{addon_dir}/license.html")  # Replace with the path to your HTML file
        # Create a QScrollArea to enable scrolling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a layout for the scroll area using QGridLayout
        scroll_layout = QGridLayout()

        # Create a widget to hold the layout
        container = QWidget()

        label.setText(html_content)  # 'html_table' contains the HTML table string
        label.setWordWrap(True)

        #layout = QVBoxLayout()
        scroll_layout.addWidget(label)
        # Set the widget for the scroll area
        scroll_area.setWidget(container)

        # Set the layout for the container
        container.setLayout(scroll_layout)

        # Set the widget for the scroll area
        scroll_area.setWidget(container)

        # Add the scroll area to the dialog
        window_layout = QVBoxLayout()
        window_layout.addWidget(scroll_area)
        self.setLayout(window_layout)
    def read_html_file(self, file_path):
        """Reads an HTML file and returns its content as a string."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    def show_window(self):
        """Displays the license window."""
        self.show()

class Credits(QWidget):
    """A window for displaying the addon's credits."""
    def __init__(self):
        """Initializes the credits window."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface of the credits window."""
        self.setWindowTitle("AnkiMon License")

        # Create a label and set HTML content
        label = QLabel()
        html_content = self.read_html_file(f"{addon_dir}/credits.html")  # Replace with the path to your HTML file
        # Create a QScrollArea to enable scrolling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a layout for the scroll area using QGridLayout
        scroll_layout = QGridLayout()

        # Create a widget to hold the layout
        container = QWidget()

        label.setText(html_content)  # 'html_table' contains the HTML table string
        label.setWordWrap(True)

        #layout = QVBoxLayout()
        scroll_layout.addWidget(label)
        # Set the widget for the scroll area
        scroll_area.setWidget(container)

        # Set the layout for the container
        container.setLayout(scroll_layout)

        # Set the widget for the scroll area
        scroll_area.setWidget(container)

        # Add the scroll area to the dialog
        window_layout = QVBoxLayout()
        window_layout.addWidget(scroll_area)
        self.setLayout(window_layout)
    def read_html_file(self, file_path):
        """Reads an HTML file and returns its content as a string."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    def show_window(self):
        """Displays the credits window."""
        self.show()

class HelpWindow(QDialog):
    """A window for displaying the addon's help guide."""
    def __init__(self, online_connectivity):
        """Initializes the help window."""
        super().__init__()
        html_content = " "
        help_local_file_path = addon_dir / "HelpInfos.html"
        try:
            if online_connectivity != False:
                # URL of the file on GitHub
                help_local_file_path = addon_dir / "HelpInfos.html"
                help_github_url = "https://raw.githubusercontent.com/Unlucky-Life/ankimon/main/src/Ankimon/HelpInfos.html"
                # Path to the local file
                local_content = read_local_file(help_local_file_path)
                # Read content from GitHub
                github_content, github_html_content = read_github_file(help_github_url)
                if local_content is not None and compare_files(local_content, github_content):
                    html_content = github_html_content
                else:
                    # Download new content from GitHub
                    if github_content is not None:
                        # Write new content to the local file
                        write_local_file(help_local_file_path, github_content)
                        html_content = github_html_content
            else:
                help_local_file_path = addon_dir / "HelpInfos.html"
                local_content = read_local_file(help_local_file_path)
                html_content = local_content
        except Exception as e:
            show_warning_with_traceback(parent=mw, exception=e, message="Failed to retrieve Ankimon HelpGuide from GitHub.")
            local_content = read_local_file(help_local_file_path)
            html_content = local_content
        self.setWindowTitle("Ankimon HelpGuide")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setHtml(html_content)
        layout.addWidget(self.text_edit)
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setLayout(layout)

class TableWidget(QWidget):
    """A widget for displaying the Pokémon type effectiveness chart."""
    def __init__(self):
        """Initializes the type effectiveness chart widget."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface of the type effectiveness chart."""
        self.setWindowTitle("Pokémon Type Effectiveness Table")

        # Create a label and set HTML content
        label = QLabel()
        html_content = read_html_file(f"{eff_chart_html_path}")  # Replace with the path to your HTML file
        label.setText(html_content)  # 'html_table' contains the HTML table string
        label.setWordWrap(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

    def show_eff_chart(self):
        """Displays the type effectiveness chart."""
        self.show()

class IDTableWidget(QWidget):
    """A widget for displaying the Pokémon generation and ID chart."""
    def __init__(self):
        """Initializes the generation and ID chart widget."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface of the generation and ID chart."""
        self.setWindowTitle("Pokémon - Generations and ID")
        # Create a label and set HTML content
        label = QLabel()
        html_content = read_html_file(f"{table_gen_id_html_path}")  # Replace with the path to your HTML file
        label.setText(html_content)  # 'html_table' contains the HTML table string
        label.setWordWrap(True)
        label.setStyleSheet("background-color: rgb(44,44,44);")
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

    def show_gen_chart(self):
        """Displays the generation and ID chart."""
        self.show()

class Pokedex_Widget(QWidget):
    """A widget for displaying the user's Pokédex."""
    def __init__(self):
        """Initializes the Pokédex widget."""
        super().__init__()
        self.read_poke_coll()
        self.initUI()

    def read_poke_coll(self):
        """Reads the user's Pokémon collection from the JSON file."""
        with (open(mypokemon_path, "r", encoding="utf-8") as json_file):
            self.captured_pokemon_data = json.load(json_file)

    def initUI(self):
        """Initializes the user interface of the Pokédex."""
        self.setWindowTitle("Pokédex")

        # Create a label and set HTML content
        label = QLabel()
        # Extract the IDs of the Pokémon listed in the JSON file
        self.available_pokedex_ids = {pokemon['id'] for pokemon in self.captured_pokemon_data}

        # Now we generate the HTML rows for each Pokémon in the range 1-898, graying out those not in the JSON file
        table_rows = [self.generate_table_row(i, i not in self.available_pokedex_ids) for i in range(1, 899)]

        # Combine the HTML template with the generated rows
        html_content = pokedex_html_template.replace('<!-- Table Rows Will Go Here -->', ''.join(table_rows))

        #html_content = self.read_html_file(f"{pokedex_html_path}")  # Replace with the path to your HTML file
        label.setText(html_content)  # 'html_table' contains the HTML table string
        label.setWordWrap(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

    # Helper function to generate table rows
    def generate_table_row(self, pokedex_number, is_gray):
        """Generates an HTML table row for a Pokémon."""
        name = f"Pokemon #{pokedex_number}" # Placeholder, actual name should be fetched from a database or API
        image_class = "pokemon-gray" if is_gray else ""
        return f'''
        <tr>
            <td>{pokedex_number}</td>
            <td>{name}</td>
            <td><img src="{pokedex_number}.png" alt="{name}" class="pokemon-image {image_class}" /></td>
        </tr>
        '''

    def show_pokedex(self):
        """Displays the Pokédex."""
        self.read_poke_coll()
        self.show()

class CheckFiles(QDialog):
    """A dialog for checking the integrity of the addon's files."""
    def __init__(self):
        """Initializes the file checker dialog."""
        super().__init__()
        self.setWindowTitle("Ankimon Files Checker")
        check_files_message = "Ankimon Files:"
        check_files_message += " \n Sprite Resource Files incomplete. \n  Please go to Ankimon => 'Help' => 'Download Resources' to download the needed files"
        check_files_message += "\n Once all files have been downloaded: Restart Anki"

        # Create a QLabel instance
        self.label = QLabel(f"{check_files_message}", self)

        # Create a QVBoxLayout instance
        self.layout = QVBoxLayout()

        # Add the QLabel to the layout
        self.layout.addWidget(self.label)

        # Set the dialog's layout
        self.setLayout(self.layout)