import sys

import vtk
from vtk.qt import QVTKRenderWindowInteractor
from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets


class VTKViewer(QtWidgets.QFrame):
    def __init__(self, parent):
        super(VTKViewer, self).__init__(parent)

        # Make the actual QtWidget a child so that it can be re parented
        self.interactor = QVTKRenderWindowInteractor.QVTKRenderWindowInteractor(self)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.interactor)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        # Setup VTK environment
        self.renderer = vtk.vtkRenderer()
        self.render_window = self.interactor.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.render_window.SetInteractor(self.interactor)
        self.renderer.SetBackground(0.8,0.8,0.8)

    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()


class MyMdiArea(QtWidgets.QMdiArea):
    def __init__(self, parent):
        super(MyMdiArea, self).__init__(parent)

    def tileHorizontally(self):
        windows = self.subWindowList()
        number_of_windows = len(windows)
        if number_of_windows < 2:
            self.tileSubWindows()
        else:
            window_height = self.height()
            window_width = self.width() / number_of_windows
            x = 0
            for window in windows:
                window.resize(window_width, window_height)
                window.move(x, 0)
                x += window_width

    def tileVertically(self):
        windows = self.subWindowList()
        number_of_windows = len(windows)
        if number_of_windows < 2:
            self.tileSubWindows()
        else:
            window_height = self.height() / number_of_windows
            window_width = self.width()
            y = 0
            for window in windows:
                window.resize(window_width, window_height)
                window.move(0, y)
                y += window_height


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("VTK Viewer")
        self.create_menu()
        self.statusBar()
        self.mdi = MyMdiArea(self)
        self.setCentralWidget(self.mdi)

    def create_menu(self):
        """ Create the menu bar. """
        # Create the menu Bar.
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu("&File")
        self.help_menu = self.menubar.addMenu("&Help")

        # setup File Menu
        quit_action = self.create_action("&Quit", "Ctrl+Q", "Quit the app", QtCore.QCoreApplication.instance().quit)
        self.add_actions(self.file_menu, quit_action)

        #setup Help Menu
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

    def open_file(self, filename):
        doc = VTKViewer(self.mdi, filename)
        self.mdi.addSubWindow(doc)
        doc.show()
        doc.start()
        self.mdi.tileHorizontally()

    def on_about(self):
        msg = """Text appearing in the about dialog of our application."""
        QtWidgets.QMessageBox.about(self, "About the demo", msg.strip())


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.open_file("tower.vtk")
    window.open_file("tower.vtk")
    sys.exit(app.exec_())
