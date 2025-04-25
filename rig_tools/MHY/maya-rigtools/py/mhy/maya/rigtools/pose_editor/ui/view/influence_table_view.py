"""
View module representing influence and attributes information
"""
from PySide2 import QtWidgets


class InfluenceListView(QtWidgets.QTableView):
    """
    The GUI to manage all the influence influences.
    """

    def __init__(self, *args, **kwargs):
        super(InfluenceListView, self).__init__(*args, **kwargs)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    @property
    def controller(self):
        """
        Dummy property that linked to controller variable in model
        Returns:
            PoseController:

        """
        return self.model().controller

    @property
    def data_model(self):
        """
        Get the model from the view
        Returns:
            QAbstractTableModel: The model object associated with the view

        """
        return self.model()

