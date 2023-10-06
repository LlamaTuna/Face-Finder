from PySide2.QtWidgets import QTextEdit, QVBoxLayout, QWidget
from PySide2.QtCore import QThread, Signal
import sys

class ConsoleOutputThread(QThread):
    '''A thread that captures standard output and emits it as a signal.'''
    
    signal = Signal(str)  # signal to emit text

    def write(self, s):
        '''Capture write calls and emit as signal.'''
        self.signal.emit(s)  # emit the signal with the text

    def flush(self):
        '''Implement a flush method to maintain a file-like interface.'''
        pass  # needed for file-like interface

class ConsoleWidget(QWidget):
    '''A widget that displays standard output in a QTextEdit.'''
    
    def __init__(self, parent=None):
        '''Initialize the ConsoleWidget with layout and console output.'''
        super().__init__(parent)

        # Set up layout and widgets
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        layout.addWidget(self.console_output)

        # ConsoleOutputThread instance
        self.console_output_thread = ConsoleOutputThread()
        self.console_output_thread.signal.connect(self.console_output.append)  # connect signal to append method of QTextEdit

        # Replace the standard output with ConsoleOutputThread instance
        sys.stdout = self.console_output_thread

    def start_console_output_thread(self):
        '''Start the thread that listens for standard output.'''
        self.console_output_thread.start()
