from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea

class DataHandlerWindow(QMainWindow):
    """A developer tool for inspecting the addon's data.

    This window provides a read-only view of the user's collection, team,
    items, and other data managed by the `DataHandler`. It is an essential
    utility for debugging and ensuring data integrity, allowing for easy
    inspection of the addon's state.
    """
    def __init__(self, data_handler):
        """Initializes the data viewer window.

        Args:
            data_handler: An instance of the `DataHandler` class, which
                          provides access to the addon's data.
        """
        super().__init__()
        self.data_handler = data_handler
        self.init_ui()

    def init_ui(self):
        """Initializes the user interface of the data viewer window."""
        self.setWindowTitle('Data Viewer')

        # Create the central widget and the main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Create a scroll area and set it as the main widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # List of attributes to process
        attributes_to_handle = ['mypokemon', 'mainpokemon', 'items', 'team', 'data', 'badges']

        # Process each attribute using the modular function
        for attr_name in attributes_to_handle:
            self.handle_file(attr_name, scroll_layout)

        # Display the entries in data_handler.data
        if isinstance(self.data_handler.data, list):
            for entry in self.data_handler.data:
                if isinstance(entry, dict):  # Ensure it's a dictionary
                    for key, value in entry.items():
                        entry_label = QLabel(f"{key}:")
                        entry_text_edit = QTextEdit()
                        entry_text_edit.setPlainText(str(value))
                        entry_text_edit.setReadOnly(True)
                        scroll_layout.addWidget(entry_label)
                        scroll_layout.addWidget(entry_text_edit)
                else:
                    # Handle non-dictionary entries
                    error_label = QLabel("Invalid data entry (not a dictionary)")
                    error_text_edit = QTextEdit()
                    error_text_edit.setPlainText(str(entry))
                    error_text_edit.setReadOnly(True)
                    scroll_layout.addWidget(error_label)
                    scroll_layout.addWidget(error_text_edit)
        else:
            error_label = QLabel("Data is not a list")
            error_text_edit = QTextEdit()
            error_text_edit.setPlainText(str(self.data_handler.data))
            error_text_edit.setReadOnly(True)
            scroll_layout.addWidget(error_label)
            scroll_layout.addWidget(error_text_edit)

        # Set the scrollable content
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        # Add the scroll area to the main layout and set the central widget
        main_layout.addWidget(scroll_area)
        self.setCentralWidget(central_widget)

    def handle_file(self, attr_name, scroll_layout):
        """Handles the UI setup and processing for a specific data attribute.

        This method dynamically creates UI elements to display the content of a
        given attribute from the `DataHandler`. It's designed to be extendable,
        allowing for easy addition of new data views in the future.

        Args:
            attr_name (str): The name of the attribute to be displayed.
            scroll_layout (QVBoxLayout): The layout to which the UI elements
                                         will be added.
        """
        if hasattr(self.data_handler, attr_name):
            # Add a label and text display for the attribute
            label = QLabel(attr_name)
            text_edit = QTextEdit()
            content = getattr(self.data_handler, attr_name)
            text_edit.setPlainText(str(content))
            text_edit.setReadOnly(True)
            scroll_layout.addWidget(label)
            scroll_layout.addWidget(text_edit)

            # Assign unique IDs and save JSON data if necessary
            if attr_name in ['mypokemon', 'mainpokemon']:
                self.data_handler.assign_unique_ids(content)
                self.data_handler.assign_new_variables(content)
                self.data_handler.save_file(attr_name)

    def show_window(self):
        """Displays the data viewer window."""
        self.show()
