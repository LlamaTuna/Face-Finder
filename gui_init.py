'''
@file gui_init.py
Initialize the GUI elements
'''

from PySide2.QtWidgets import QSplitter, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QProgressBar, QTableWidget, QStyle, QHBoxLayout, QDoubleSpinBox
from PySide2.QtCore import Qt
from console_output import ConsoleWidget
import logging
import os
import sys
from themes import load_stylesheet




def initUI(self):
    """
    Initialize the main user interface components for the 'Face Finder' application.
    """
    try:
        self.setWindowTitle('Face Finder')
        self.create_menu_bar()

        # Check if we are running in a bundled app or regular Python environment 
        # to correctly set the theme path
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = os.path.dirname(os.path.abspath(__file__))

        # Load the light theme stylesheet
        light_theme_path = os.path.join(bundle_dir, "styles", "light_theme.qss")
        self.setStyleSheet(load_stylesheet(light_theme_path))

        # Define the central widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Create a horizontal splitter for left and right panels
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel_widget = QWidget()
        right_panel_widget = QWidget()
        top_splitter.addWidget(left_panel_widget)
        top_splitter.addWidget(right_panel_widget)

        left_panel_layout = QVBoxLayout(left_panel_widget)
        right_panel_layout = QVBoxLayout(right_panel_widget)

        # Image search section in left panel
        image_to_search_layout = QHBoxLayout()
        self.image_to_search_edit = QLineEdit()
        image_to_search_button = QPushButton('Browse')
        image_to_search_button.clicked.connect(self.browse_image_to_search)
        image_to_search_layout.addWidget(QLabel('Image to search for:'))
        image_to_search_layout.addWidget(self.image_to_search_edit)
        image_to_search_layout.addWidget(image_to_search_button)
        left_panel_layout.addLayout(image_to_search_layout)

        # Input folder section in left panel
        input_folder_layout = QHBoxLayout()
        self.input_folder_edit = QLineEdit()
        input_folder_button = QPushButton('Browse')
        input_folder_button.clicked.connect(self.browse_input_folder)
        input_folder_layout.addWidget(QLabel('Input folder:'))
        input_folder_layout.addWidget(self.input_folder_edit)
        input_folder_layout.addWidget(input_folder_button)
        left_panel_layout.addLayout(input_folder_layout)

        # Output folder section in left panel
        output_folder_layout = QHBoxLayout()  
        self.output_folder_edit = QLineEdit()
        output_folder_button = QPushButton('Browse')
        output_folder_button.clicked.connect(self.browse_output_folder)
        output_folder_layout.addWidget(QLabel('Output folder:'))
        output_folder_layout.addWidget(self.output_folder_edit)
        output_folder_layout.addWidget(output_folder_button)
        left_panel_layout.addLayout(output_folder_layout)

        # Find and cancel match buttons in left panel
        match_buttons_layout = QHBoxLayout()
        find_match_button = QPushButton('Find match')
        find_match_button.clicked.connect(self.find_match)
        match_buttons_layout.addWidget(find_match_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_face_processing)
        match_buttons_layout.addWidget(self.cancel_button) 
        left_panel_layout.addLayout(match_buttons_layout)

        # Image preview in left panel
        self.image_preview_label = QLabel()
        self.image_preview_label.setObjectName('image_preview_label')
        left_panel_layout.addWidget(self.image_preview_label)

        # Progress bar in left panel
        left_panel_layout.addWidget(QLabel('Progress:'))
        self.progress_bar = QProgressBar()
        left_panel_layout.addWidget(self.progress_bar)

        # Thumbnail navigation (left and right arrows) in left panel
        self.left_arrow_button = QPushButton()
        self.left_arrow_button.setObjectName('left_arrow_button')
        self.left_arrow_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.left_arrow_button.clicked.connect(self.previous_matched_face)
        self.right_arrow_button = QPushButton()
        self.right_arrow_button.setObjectName('right_arrow_button')
        self.right_arrow_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
        self.right_arrow_button.clicked.connect(self.next_matched_face)
        arrows_layout = QHBoxLayout()
        arrows_layout.addWidget(self.left_arrow_button)
        self.matched_face_label = QLabel()
        self.matched_face_label.setObjectName('matched_face_label')
        arrows_layout.addWidget(self.matched_face_label)
        arrows_layout.addWidget(self.right_arrow_button)
        left_panel_layout.addLayout(arrows_layout)

        # Similarity and original image label in left panel
        self.similarity_original_image_label = QLabel()
        self.similarity_original_image_label.setObjectName('similarity_original_image_label')
        self.similarity_original_image_label.setWordWrap(True)
        left_panel_layout.addWidget(self.similarity_original_image_label)

        # Image similarity threshold in right panel
        self.similarity_threshold_spinbox = QDoubleSpinBox(self)
        self.similarity_threshold_spinbox.setRange(0, 100)
        self.similarity_threshold_spinbox.setSingleStep(1)
        self.similarity_threshold_spinbox.setValue(90)
        self.similarity_threshold_spinbox.setFixedWidth(100)
        self.similarity_threshold_spinbox.setSuffix('%')
        similarity_label = QLabel('Enter the minimum similarity percentage for images to copy.')
        right_panel_layout.addWidget(similarity_label) 
        right_panel_layout.addWidget(self.similarity_threshold_spinbox)

        # Output directory for similar images in right panel
        sim_output_directory_layout = QHBoxLayout()
        sim_dir_label = QLabel('Select a folder to copy similar images to.')
        right_panel_layout.addWidget(sim_dir_label)
        self.sim_output_directory_edit = QLineEdit()
        sim_output_directory_button = QPushButton('Browse')
        sim_output_directory_button.clicked.connect(self.browse_output_directory_for_similarity)
        sim_output_directory_layout.addWidget(QLabel('Output Folder:'))
        sim_output_directory_layout.addWidget(self.sim_output_directory_edit)
        sim_output_directory_layout.addWidget(sim_output_directory_button)
        right_panel_layout.addLayout(sim_output_directory_layout)

        self.copy_photos_button = QPushButton("Copy Similar Images", self)
        self.copy_photos_button.clicked.connect(self.copy_matching_photos)
        right_panel_layout.addWidget(self.copy_photos_button)

        # Tagged image output directory and export button in right panel
        output_directory_layout = QHBoxLayout()
        tags_label = QLabel('Select an output folder for any tagged images from table.')
        right_panel_layout.addWidget(tags_label)
        self.output_directory_edit = QLineEdit()
        output_directory_button = QPushButton('Browse')
        output_directory_button.clicked.connect(self.browse_output_directory)
        output_directory_layout.addWidget(QLabel('Output Folder:'))
        output_directory_layout.addWidget(self.output_directory_edit)
        output_directory_layout.addWidget(output_directory_button)
        right_panel_layout.addLayout(output_directory_layout)
        export_tags_button = QPushButton('Copy Tagged Images')
        export_tags_button.clicked.connect(self.export_tagged_photos)
        right_panel_layout.addWidget(export_tags_button)

        # Add the top splitter to the main layout
        main_layout.addWidget(top_splitter)

        # Results table below the top splitter
        self.result_table = QTableWidget(self)
        self.result_table.itemSelectionChanged.connect(self.on_result_table_selection_changed)
        self.result_table.setSortingEnabled(True)
        self.result_table.verticalHeader().setDefaultSectionSize(12)
        main_layout.addWidget(self.result_table)

        # Console output in right panel
        self.console_widget = ConsoleWidget()
        right_panel_layout.addWidget(self.console_widget)
        self.console_widget.start_console_output_thread()

    except Exception as e:
        logging.exception("An error occurred while initializing the UI")
        raise e

