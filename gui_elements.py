'''
@file gui_elements.py
Handles table elements in the GUI
'''


from PySide2.QtWidgets import QTableWidgetItem


class NumericTableWidgetItem(QTableWidgetItem):
    """
    A custom QTableWidgetItem designed to handle numeric values, 
    especially ones represented as percentages.
    """
    
    def __init__(self, value):
        """
        Initialize the NumericTableWidgetItem with the given value.

        Parameters:
        - value (str/int/float): A value to be stored in the table cell.
        """
        super().__init__(str(value))

    def __lt__(self, other):
        """
        Overload the less than operator to compare two NumericTableWidgetItem 
        objects based on their numeric value.

        Parameters:
        - other (NumericTableWidgetItem): Another item to compare with.

        Returns:
        - bool: True if current item's value is less than the other item's value, otherwise False.
        """
        # Extract the numeric value from the text, removing any trailing '%' if present
        my_number = float(self.text().rstrip('%'))
        other_number = float(other.text().rstrip('%'))
        
        return my_number < other_number

  
class MatchTableWidgetItem(QTableWidgetItem):
    """
    A custom QTableWidgetItem designed to handle match descriptions like 'Match 1', 'Match 2', etc.
    """

    def __lt__(self, other):
        """
        Overload the less than operator to compare two MatchTableWidgetItem 
        objects based on their numeric match number.

        Parameters:
        - other (MatchTableWidgetItem): Another item to compare with.

        Returns:
        - bool: True if current item's match number is less than the other item's match number, otherwise False.
        """
        # Extract the numeric match number from the text
        my_number = int(self.text().split()[-1])
        other_number = int(other.text().split()[-1])
        
        return my_number < other_number