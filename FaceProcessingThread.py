'''
@file FaceProcessingThread.py
Enables multi threading with worker and GUI threads for progress bar callback
'''

from PySide2.QtCore import QThread, Signal as pyqtSignal
from face_detection import save_faces_from_folder, find_matching_face, face_detector  # Import face_detector
import logging
import traceback

class FaceProcessingThread(QThread):
    # Define signals to communicate with the main thread
    progress_signal = pyqtSignal(int)          # Signal to update progress
    processing_done = pyqtSignal(tuple)        # Signal to indicate completion
    error_signal = pyqtSignal(str)             # Signal to report errors
    partial_result_signal = pyqtSignal(object) # Signal for partial results

    def __init__(self, input_folder, output_folder, image_to_search):
        """
        Initialize the FaceProcessingThread.

        Parameters:
        - input_folder (str): Path to the folder containing images to be processed.
        - output_folder (str): Path to the folder where processed images should be saved.
        - image_to_search (str): Path to the image containing the face to search for.
        """
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.image_to_search = image_to_search
        self.cancel = False  # Initialize the cancel flag

    def cancel_processing(self):
        """Set the cancel flag to stop processing."""
        self.cancel = True

    def run(self):
        """
        Main execution method for the thread. It processes faces and searches for matches.
        """
        try:
            # Extract and save faces from the input folder if not canceled
            if not self.cancel:
                self.face_data = save_faces_from_folder(
                    folder_path=self.input_folder,
                    output_folder=self.output_folder,
                    face_detector=face_detector,
                    progress_callback=self.update_progress,
                    cancel_flag=lambda: self.cancel
                )

            # Find matching faces in the extracted faces if not canceled
            if not self.cancel:
                matching_faces = find_matching_face(self.image_to_search, self.face_data, face_detector)
                self.processing_done.emit((matching_faces, self.face_data))
                
        except Exception as e:
            error_message = f"An error occurred during face processing: {str(e)}"
            logging.error(error_message)
            logging.error(traceback.format_exc())
            self.error_signal.emit(error_message)  # Emit the error message to be handled by the main thread

    def update_progress(self, progress):
        """
        Emit the progress signal with the current progress value.

        Parameters:
        - progress (int): Progress value to emit.
        """
        self.progress_signal.emit(int(progress))