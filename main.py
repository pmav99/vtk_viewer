import sys

import vtk
from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTK Viewer")
        self.create_menu()

    def create_menu(self):
        """ Create the menu bar. """
        # Create the menu Bar.
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu("&File")
        self.help_menu = self.menubar.addMenu("&Help")

        # create File Menu actions
        quit_action = self.create_action("&Quit", "Ctrl+Q", "Quit the app", QtCore.QCoreApplication.instance().quit)
        self.add_actions(self.file_menu, quit_action)

        #Create Help Menu's actions.
        about_action = self.create_action("&About", QtGui.QKeySequence.HelpContents, "About the demo", self.on_about)
        self.add_actions(self.help_menu, about_action)

    def add_actions(self, target, *actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, shortcut, tip, callback):
        """ Return a QAction object. """
        action = QtWidgets.QAction(text, self)
        action.setShortcut(shortcut)
        action.setStatusTip(tip)
        action.triggered.connect(callback)
        return action

    def on_about(self):
        msg = """Text appearing in the about dialog of our application."""
        QtWidgets.QMessageBox.about(self, "About the demo", msg.strip())


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
