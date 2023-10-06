'''
@file face_matcher_app_class.py
GUI related functions to handle the UI, inputs, outputs, table, console, etc
'''
print("Loading Application...") # inform user applcation is loading
import os
from platform import win32_ver
import cv2
import types
from gui_init import initUI
from PySide2.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QWidget, QHBoxLayout, QCheckBox
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtWidgets import QAction
from PySide2.QtCore import Qt
from gui_elements import NumericTableWidgetItem, MatchTableWidgetItem
from FaceProcessingThread import FaceProcessingThread
from themes import apply_dark_theme, apply_light_theme
import logging
import csv
import shutil


try:
    logging.basicConfig(filename=r'.\debug.log',
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.debug('Logging setup successful')
    print("Logging setup2 successful.")
except Exception as e:
    print(f"Logging setup failed: {str(e)}")

logger = logging.getLogger()

print("Application loaded.")

class FaceMatcherApp(QMainWindow):
    """
    Initializes the FaceMatcherApp main window.
    
    Parameters:
    - face_data (dict, optional): Data related to the faces. Defaults to None.
    """
    def __init__(self, face_data=None):
        super().__init__()
        self.face_data = face_data
        self.dark_theme_enabled = False
        self.worker = None
        self.initUI = types.MethodType(initUI, self)  # This binds the initUI function as an instance method
        self.initUI()
        self.result_table.cellDoubleClicked.connect(self.open_image_in_default_viewer)
        self.matching_faces = []

        # # Apply the qdarkstyle theme
        # dark_stylesheet = qdarkstyle.load_stylesheet_pyside2()
        # self.setStyleSheet(dark_stylesheet)

    def create_menu_bar(self):
        """
        Creates the menu bar for the application's main window.
        """        
        try:
            menubar = self.menuBar()

            # Create File menu
            file_menu = menubar.addMenu('File')

            # Create Exit action
            exit_action = QAction('Exit', self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            # Create View menu
            view_menu = menubar.addMenu('View')

            # Create Toggle Dark Theme action
            toggle_dark_theme_action = QAction('Toggle Dark Theme', self)
            toggle_dark_theme_action.triggered.connect(self.toggle_dark_theme)
            view_menu.addAction(toggle_dark_theme_action)

            # Create Export to CSV action
            export_csv_action = QAction('Export to CSV', self)
            export_csv_action.triggered.connect(self.export_table_to_csv)
            file_menu.addAction(export_csv_action)

            # Create Export to HTML action
            export_html_action = QAction('Export to HTML', self)
            export_html_action.triggered.connect(self.export_table_to_html)
            file_menu.addAction(export_html_action)

            # Create help menu item
            help_menu = menubar.addMenu('Help')
            help_action = QAction('Help', self)
            help_action.triggered.connect(self.help_dialogue)
            help_menu.addAction(help_action)
            
        except Exception as e:
            logging.exception("An error occurred while creating the menu bar")
            raise e

    def help_dialogue(self):
        """ 
        Displays help message from menu bar selection.
        """
        help_message = ("Welcome to Face Finder.\n\n"
        "1. Select an image of a face you wish to search for.\n"
        "2. Select a directory containing images you wish to analyse.\n"
        "3. Select an output directory to place any images of faces found.\n"
        "4. Press find match and face finder will commence its analysis.\n\n"
        "All images in the selected directory and any sub-directories will be analysed.\n\n"
        "Faces in which the algorithms compute to be similar enough will be placed in the output directory and entered in the results table along with any available location and timestamp data.\n\n"
        "Once the analysis is complete you can choose to:\n\n"
        "1. Double click on the original image file in the results table to view the original image.\n"
        "2. In the right hand column you can opt to export original images to a selected directory based upon similarity score.\n"
        "3. Alternatively you can opt to export original images to a selected directory by tagging them in the results table.")
        help_text = QMessageBox(self)
        help_text.setWindowTitle('Help')
        help_text.setText(help_message)
        help_text.exec()

    def get_matched_face_by_row(self, row):
        """
        Retrieves the matched face image based on the provided table row index.
        
        Parameters:
        - row (int): Index of the row in the results table.
        
        Returns:
        Image or None: The matched face image or None if not found.
        """        
        if row >= 0 and row < self.result_table.rowCount():
            resized_image_name = self.result_table.item(row, 9).text()
            print("resized_image: ", resized_image_name)
            matched_face_path = os.path.join(self.output_folder_edit.text(), resized_image_name)
            print("matched_image: ", matched_face_path)
            matched_face = cv2.imread(matched_face_path)

            return matched_face
        return None

    def previous_matched_face(self):
        """
        Displays the matched face from the previous row in the results table.
        """
        try:
            current_row = self.result_table.currentRow()
            if current_row > 0:
                self.result_table.selectRow(current_row - 1)
                matched_face = self.get_matched_face_by_row(current_row - 1)
                
                if matched_face is not None:
                    similarity_item = self.result_table.item(current_row - 1, 1)
                    original_image_name_item = self.result_table.item(current_row - 1, 2)

                    if similarity_item and original_image_name_item:
                        similarity = float(similarity_item.text().rstrip('%')) / 100
                        original_image_name = original_image_name_item.text()
                        self.display_matched_face(matched_face, similarity, original_image_name)
                    else:
                        logging.warning("Could not find similarity or original image name for row: {}".format(current_row - 1))
        except Exception as e:
            logging.exception("An error occurred while navigating to the previous matched face")
            raise e

    def next_matched_face(self):
        """
        Displays the matched face from the next row in the results table.
        """
        try:
            current_row = self.result_table.currentRow()
            if current_row < self.result_table.rowCount() - 1:
                self.result_table.selectRow(current_row + 1)
                matched_face = self.get_matched_face_by_row(current_row + 1)
                
                if matched_face is not None:
                    similarity_item = self.result_table.item(current_row + 1, 1)
                    original_image_name_item = self.result_table.item(current_row + 1, 2)

                    if similarity_item and original_image_name_item:
                        similarity = float(similarity_item.text().rstrip('%')) / 100
                        original_image_name = original_image_name_item.text()
                        self.display_matched_face(matched_face, similarity, original_image_name)
                    else:
                        logging.warning("Could not find similarity or original image name for row: {}".format(current_row + 1))
        except Exception as e:
            logging.exception("An error occurred while navigating to the next matched face")
            raise e

    def on_result_table_selection_changed(self):
        """
        Handles the event when the selection in the results table changes. It displays relevant data 
        for the selected face.
        """
        try:
            current_row = self.result_table.currentRow()
            if current_row != -1:
                print("Selection changed")  # debug print
                img_hash = self.result_table.item(current_row, 3).text()
                print(f"Selected image hash: {img_hash}")

                # access face_data using the selected image hash
                face_info = self.face_data.get(img_hash, {})

                # print the face_info to the console
                print(face_info)

 
                self.console_output.append("\nSelected face:")
                self.console_output.append(f"\nImage file: {face_info.get('file_name', 'N/A')}")

                # EXIF data
                self.console_output.append("\nEXIF data:")
                exif_data = face_info.get('exif_data', {})
                for k, v in exif_data.items():
                    self.console_output.append(f"{k}: {v}")

                self.display_selected_matched_face()
        except Exception as e:
            logging.exception("An error occurred while handling the selection change in the result table")
            raise e

    def on_table_selection_changed_and_display_face(self): 
        try:
            self.display_selected_matched_face()
        except Exception as e:
            logging.exception("An error occurred while handling the selection change in the result table and displaying the face")
            raise e

    def toggle_dark_theme(self):
        """
        Toggles the UI theme between dark and light.
        """
        try:
            if self.dark_theme_enabled:
                self.dark_theme_enabled = False
                apply_light_theme(self)
            else:
                self.dark_theme_enabled = True
                apply_dark_theme(self)
        except Exception as e:
            logging.exception("An error occurred while toggling the dark theme")
            raise e

    def browse_input_folder(self):
        """
        Opens a dialog to select an output folder and updates the output folder text field.
        """
        try:
            print("Browsing input folder")
            input_folder = QFileDialog.getExistingDirectory(self, 'Select Input Folder')
            if input_folder:
                self.input_folder_edit.setText(input_folder)
            print("Finished browsing input folder")
        except Exception as e:
            logging.exception("An error occurred while browsing the input folder")
            raise e

    def browse_output_folder(self):
        """
        Opens a dialog to select an output folder and updates the output folder text field.
        """
        try:
            print("Browsing output folder")
            output_folder = QFileDialog.getExistingDirectory(self, 'Select Output Folder')
            if output_folder:
                self.output_folder_edit.setText(output_folder)
            print("Finished browsing output  folder")
        except Exception as e:
            logging.exception("An error occurred while browsing the output folder")
            raise e

    def browse_image_to_search(self):
        """
        Opens a dialog to select an image to search for and updates the related text field and preview.
        """
        try:
            print("Browsing image to search")
            file_path, _ = QFileDialog.getOpenFileName(self, 'Select Image to Search', '', 'Image files (*.png *.jpeg *.jpg *.bmp *.tiff)')
            if file_path:
                self.image_to_search_edit.setText(file_path)
                self.load_image_thumbnail(file_path)
            print("Finished browsing image to search")
        except Exception as e:
            logging.exception("An error occurred while browsing the image to search")
            raise e

    def load_image_thumbnail(self, file_path):
        """
        Loads and displays a thumbnail of the image at the given file path.
        
        Parameters:
        - file_path (str): Path to the image file.
        """
        try:
            print("Loading image thumbnail")
            image = QImage(file_path)
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_preview_label.setPixmap(scaled_pixmap)
            print("Finished loading image thumbnail")
        except Exception as e:
            logging.exception("An error occurred while loading the image thumbnail")
            raise e

    def display_matched_face(self, matched_face, similarity, original_image_name):
        """
        Displays a matched face image, its similarity score, and the name of the original image.
        """
        try:
            if matched_face is None:
                print("Error: Matched face is None. Cannot display.")
                return
            
            matched_face = cv2.cvtColor(matched_face, cv2.COLOR_BGR2RGB)
            height, width = matched_face.shape[:2]
            bytes_per_line = 3 * width
            q_image = QImage(matched_face.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(q_image)
            if pixmap.isNull():
                print("Error: QPixmap is null. Cannot display.")
                return

            self.matched_face_label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            self.similarity_original_image_label.setText(f"Similarity: {similarity * 100:.2f}% | Original Image: {original_image_name}")

        except Exception as e:
            logging.exception("An error occurred while displaying the matched face")
            raise e


    def find_match(self):
        """
        Initiates the process of finding matching faces based on the user's input.
        """
        try:
            logging.debug("Starting find_match")

            # Save the image path
            image_to_search_path = self.image_to_search_edit.text()

            self.clear_outputs_and_data()

            # enable cancel button and set progress bar to zero
            self.cancel_button.setEnabled(True)
            self.update_progress_bar(0)

            # Restore the image path and reload the thumbnail
            self.image_to_search_edit.setText(image_to_search_path)
            self.load_image_thumbnail(image_to_search_path)

            input_folder = self.input_folder_edit.text()
            output_folder = self.output_folder_edit.text()
            image_to_search = self.image_to_search_edit.text()

            if not input_folder or not output_folder or not image_to_search:
                QMessageBox.critical(self, "Error", "Please select all required folders and files.")
                return

            if hasattr(self, 'face_processing_thread'):
                # Stop the thread if it's running
                if self.face_processing_thread.isRunning():
                    self.face_processing_thread.terminate()
                    self.face_processing_thread.wait()
                del self.face_processing_thread

            # Reinitialize the thread
            self.face_processing_thread = FaceProcessingThread(input_folder, output_folder, image_to_search)
            self.face_processing_thread.cancel = False  # Reset the cancel flag

            # Connect the signals
            self.face_processing_thread.processing_done.connect(self.on_face_processing_done)
            self.face_processing_thread.progress_signal.connect(self.update_progress_bar)
            self.face_processing_thread.error_signal.connect(self.show_error_message)
            self.face_processing_thread.start()

            logging.debug("FaceProcessingThread started successfully")
            logging.debug("Finished find_match")

        except Exception as e:
            logging.exception("An error occurred while finding the match")
            raise e

    def select_output_directory(self):
        """
        Opens a dialog to select an output directory where matching photos will be copied.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.sim_output_directory_edit.setText(directory)

    def copy_matching_photos(self):
        """
        Copies the photos with faces that match the criteria to the selected output directory.
        """
        output_directory = self.sim_output_directory_edit.text()
        
        if not output_directory:
            QMessageBox.warning(self, "Warning", "Please select an output directory first.")
            return

        threshold = self.similarity_threshold_spinbox.value() / 100.0  # Convert back to a fraction

        for img_hash, file_name, _, similarity, _ in self.matching_faces:
            if similarity >= threshold:
                try:
                        src_path = os.path.join(self.input_folder_edit.text(), file_name)
                        dest_path = os.path.join(output_directory, file_name)
                        shutil.copy2(src_path, dest_path)
                except:
                    print(f'Error, unable to locate file:  {file_name}')

        QMessageBox.information(self, "Done", "Photos copied successfully!")

    def browse_output_directory_for_similarity(self):
        """
        Lets the user browse for an output directory for similar images and updates the QLineEdit.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        
        if directory:
            # Set the directory path to the QLineEdit
            self.sim_output_directory_edit.setText(directory)

    def show_error_message(self, message):
        """
        Displays an error message in a popup dialog.
        
        Parameters:
        - message (str): The error message to display.
        """
        QMessageBox.critical(self, "Error", message)
        self.cancel_button.setEnabled(False)  # Disable the Cancel button here too


    def cancel_face_processing(self):
        """
        Cancels the ongoing face processing operation.
        """
        if hasattr(self, 'face_processing_thread') and self.face_processing_thread.isRunning():
            self.face_processing_thread.cancel_processing()
            QMessageBox.information(self, "Info", "Face processing has been cancelled.")

        self.cancel_button.setEnabled(False)  # To disable
        self.cancel_button.setEnabled(True)   # To enable
    
    def on_face_processing_done(self, result):
        """
        Handles the event when face processing is done. Updates the UI with the results.
        
        Parameters:
        - result (tuple): Contains matching faces and face data.
        """
        try:
            self.matching_faces, self.face_data = result
            logging.debug("Processing finished")
            self.cancel_button.setEnabled(False)  # Disable the Cancel button here

            if len(self.matching_faces) > 0:
                # Setup the table columns
                columns = ['Match', 'Similarity', 'Tags', 'Original Image File', 'Latitude', 'Longitude', 'Device', 'Date', 'Time', 'Resized Image Name']
                self.result_table.setRowCount(len(self.matching_faces))  # Set the row count based on matching faces
                self.result_table.setColumnCount(len(columns))
                self.result_table.setHorizontalHeaderLabels(columns)

                for i, (img_hash, original_image_name, face_vector, similarity, resized_image_name) in enumerate(self.matching_faces):
                    face_info = self.face_data.get(img_hash, {})  # This line retrieves the relevant data for the current img_hash
                    self.result_table.setItem(i, 0, MatchTableWidgetItem(f"Match {i + 1}"))
                    self.result_table.setItem(i, 1, NumericTableWidgetItem(f"{similarity * 100:.2f}%"))
                    original_image_full_path = face_info.get('full_path', '')
                    self.result_table.setItem(i, 3, QTableWidgetItem(original_image_full_path))

                    
                    exif_data = face_info.get('exif_data', {})
                    latitude = exif_data.get('GPSInfo', {}).get('Latitude', '')
                    longitude = exif_data.get('GPSInfo', {}).get('Longitude', '')
                    device = f"{exif_data.get('Make', '')} {exif_data.get('Model', '')}".strip()
                    date = exif_data.get('DateDigitized', '')
                    time = exif_data.get('TimeDigitized', '')

                    self.result_table.setItem(i, 4, QTableWidgetItem(str(latitude)))
                    self.result_table.setItem(i, 5, QTableWidgetItem(str(longitude)))
                    self.result_table.setItem(i, 6, QTableWidgetItem(device))
                    self.result_table.setItem(i, 7, QTableWidgetItem(date))
                    self.result_table.setItem(i, 8, QTableWidgetItem(time))
                    self.result_table.setItem(i, 9, QTableWidgetItem(resized_image_name))
                    
                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox = QCheckBox()
                    checkbox_layout.addWidget(checkbox)
                    checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    checkbox_widget.setLayout(checkbox_layout)
                    self.result_table.setCellWidget(i, 2, checkbox_widget)  # Set the checkbox in the "Tags" column for this row

                    print(f"Storing resized_image_name for row {i}: {resized_image_name}")

                self.result_table.resizeColumnsToContents()
            else:
                self.result_table.setRowCount(0)
                self.result_table.setColumnCount(0)
        except Exception as e:
            logging.exception("An error occurred while handling the face processing done event")
            raise e

    def browse_output_directory(self):
        """
        Opens a dialog to select an output directory and updates the related text field.
        """
        output_directory = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        if output_directory:
            self.output_directory_edit.setText(output_directory)

    def export_tagged_photos(self):
        """
        Exports photos tagged by the user to the selected output directory.
        """
        output_directory = self.output_directory_edit.text()
        if not output_directory:
            QMessageBox.warning(self, "Warning", "Please select an output directory first!")
            return

        for row in range(self.result_table.rowCount()):
            try:
                checkbox_widget = self.result_table.cellWidget(row, 2)  
                checkbox = checkbox_widget.children()[1]  # QCheckBox is the second child of the widget
                if checkbox.isChecked():
                    original_image_path = self.result_table.item(row, 3).text()  # This is the full path now
                    dest_path = os.path.join(output_directory, os.path.basename(original_image_path))
                    shutil.copy2(original_image_path, dest_path)
            except Exception as e:
                logger.exception(f"Error in export_tagged_photos at row {row}: {str(e)}")

        QMessageBox.information(self, "Done", "Tagged photos exported successfully!")

    def display_selected_matched_face(self):
        """
        Displays the matched face image for the currently selected row in the results table.
        """
        try:
            current_row = self.result_table.currentRow()
            if current_row != -1:
                print("Displaying selected matched face")
                
                # Fetch the 'Resized Image Name' from the table
                resized_image_name = self.result_table.item(current_row, 9).text()
                folder_path = self.output_folder_edit.text().rstrip('/\\')
                matched_face_path = os.path.join(folder_path, resized_image_name)

                
                # Print the matched face path for debugging
                print(f"Debug Attempting to read image from: {matched_face_path}")
                
                # Check if the file exists before trying to read
                if not os.path.exists(matched_face_path):
                    print(f"Image file does not exist at: {matched_face_path}")
                    return

                matched_face = cv2.imread(matched_face_path)

                similarity = float(self.result_table.item(current_row, 1).text().replace('%', '')) / 100.0

                # Fetch the 'Original Image Name' from the table CB
                original_image_name = self.result_table.item(current_row, 3).text()

                self.display_matched_face(matched_face, similarity, original_image_name)
                print(f"Retrieved resized_image_name for row {current_row}: {resized_image_name}")

                print("Finished displaying selected matched face")
        except Exception as e:
            logging.exception("An error occurred while displaying the selected matched face")
            raise e

    def update_progress_bar(self, progress):
        """
        Updates the progress bar with the given progress value.
        
        Parameters:
        - progress (int): Progress value between 0 and 100.
        """
        try:
            self.progress_bar.setValue(int(progress))
        except Exception as e:
            logging.exception("An error occurred while updating the progress bar")
            raise e

    def on_result_table_selection_changed(self):
        try:
            self.display_selected_matched_face()
        except Exception as e:
            logging.exception("An error occurred while handling the selection change in the result table")
            raise e

    def open_image_in_default_viewer(self, row, column):
        """
        Opens the image in the default viewer when the corresponding cell in the results table is double-clicked.
        
        Parameters:
        - row (int): The row index of the double-clicked cell.
        - column (int): The column index of the double-clicked cell.
        """
        if column == 3: 
            original_image_full_path = self.result_table.item(row, 3).text()
            print(original_image_full_path)
                
            # Open the image using the default viewer
            if os.path.exists(original_image_full_path):
                os.startfile(original_image_full_path)
            else:
                QMessageBox.critical(self, "Error", f"File not found: {original_image_full_path}")
        
    def clear_outputs_and_data(self):
        """
        Clears all outputs in the UI and internal data structures.
        """
        # Clear the table
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        
        # Clear any displayed images or labels
        self.matched_face_label.clear()
        self.image_preview_label.clear()
        self.similarity_original_image_label.clear()
        
        # Clear any other relevant outputs (e.g., console outputs)
        self.console_widget.console_output.clear()

        
        # Clear internal data structures
        self.face_data = None
        if hasattr(self, 'face_processing_thread'):
            # Stop the thread if it's running
            if self.face_processing_thread.isRunning():
                self.face_processing_thread.terminate()
                self.face_processing_thread.wait()
            # Delete the thread
            del self.face_processing_thread
    

    def export_table_to_csv(self):
        """
        Exports the results table to a CSV file.
        """
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                # Write headers
                headers = [self.result_table.horizontalHeaderItem(i).text() if self.result_table.horizontalHeaderItem(i) else "" for i in range(self.result_table.columnCount())]
                writer.writerow(headers)
                # Write data
                for row in range(self.result_table.rowCount()):
                    row_data = [self.result_table.item(row, col).text() if self.result_table.item(row, col) else "" for col in range(self.result_table.columnCount())]
                    writer.writerow(row_data)
            QMessageBox.information(self, "Success", "Exported to CSV successfully!")   

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export to CSV: {e}")


    def export_table_to_html(self):
        """
        Exports the results table to an HTML file.
        """
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "HTML Files (*.html)")
        if not path:
            return

        try:
            html_content = "<table border='1'>\n"
            
            # Headers
            html_content += "<thead>\n<tr>\n"
            for i in range(self.result_table.columnCount()):
                header_item = self.result_table.horizontalHeaderItem(i)
                header_text = header_item.text() if header_item else ""
                html_content += f"<th>{header_text}</th>\n"
            html_content += "</tr>\n</thead>\n<tbody>\n"
            
            # Rows
            for row in range(self.result_table.rowCount()):
                html_content += "<tr>\n"
                for col in range(self.result_table.columnCount()):
                    item = self.result_table.item(row, col)
                    cell_text = item.text() if item else ""
                    html_content += f"<td>{cell_text}</td>\n"
                html_content += "</tr>\n"
            html_content += "</tbody>\n</table>"

            with open(path, 'w') as html_file:
                html_file.write(html_content)
            QMessageBox.information(self, "Success", "Exported to HTML successfully!")

        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export to HTML: {e}")