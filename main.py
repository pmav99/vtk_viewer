import sys
import pathlib

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

    def representation_wireframe(self):
        self.actor.GetProperty().SetRepresentationToWireframe()
        self.interactor.Render()

    def representation_surface(self):
        self.actor.GetProperty().SetRepresentationToSurface()
        self.interactor.Render()

    def representation_points(self):
        self.actor.GetProperty().SetRepresentationToPoints()
        self.interactor.Render()

    def edge_visibility_on(self):
        self.actor.GetProperty().EdgeVisibilityOn()
        self.interactor.Render()

    def edge_visibility_off(self):
        self.actor.GetProperty().EdgeVisibilityOff()
        self.interactor.update()


class VTKUnStructuredGridViewer(VTKViewer):
    def __init__(self, parent, filename):
        super(VTKUnStructuredGridViewer, self).__init__(parent)

        self.filename = filename

        # read File
        self.reader = reader = vtk.vtkUnstructuredGridReader()
        reader.SetFileName(self.filename.as_posix())
        reader.Update()
        self.output = reader.GetOutput()
        self.scalar_range = self.output.GetScalarRange()
        scalars_number = reader.GetNumberOfScalarsInFile()
        self.scalars_names = [reader.GetScalarsNameInFile(i) for i in range(scalars_number)]

        self.current_combo = self.scalars_names[0]

        # Create the custom lut and add it to the mapper
        self.lut = vtk.vtkLookupTable()
        self.lut.SetHueRange(0.667, 0) # From Blue to Red
        self.lut.SetNumberOfTableValues(4)
        self.lut.Build()          # must be invoked before lut.SetTableValue()
        self.lut.SetTableValue(0, 0, 1, 0, 1)
        self.lut.SetTableValue(1, 0, 0, 1, 1)
        self.lut.SetTableValue(2, 1, 1, 0, 1)
        self.lut.SetTableValue(3, 1, 0, 0, 1)

        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.SetInputData(self.output)
        # self.mapper.SetInputConnection(self.output.GetOutputPort())
        self.mapper.SetScalarRange(self.scalar_range)
        self.mapper.SetLookupTable(self.lut)

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.renderer.AddActor(self.actor)
        # self.renderer.AddActor(self.legend)
        # self.renderer.AddActor2D(self.scalar_bar)


class DockRepresentation(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super(DockRepresentation, self).__init__("Representation", parent)

        # convenient names for the vtk_interactor instances
        self.parent = parent

        self.main_widget = QtWidgets.QWidget(self)

        self.create_widgets()
        self.place_widgets()
        self.bind_events()

        self.setWidget(self.main_widget)

        self.wireframe.toggle()

    def create_widgets(self):
        self.wireframe = QtWidgets.QRadioButton("Wireframe", self)
        self.surface= QtWidgets.QRadioButton("Surface", self)
        self.surface_with_edges = QtWidgets.QRadioButton("Surface with Edges", self)

    def place_widgets(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.surface_with_edges)
        self.layout.addWidget(self.surface)
        self.layout.addWidget(self.wireframe)
        self.layout.addStretch(1)
        self.main_widget.setLayout(self.layout)

    def bind_events(self):
        self.wireframe.toggled.connect(self.on_wireframe)
        self.surface.toggled.connect(self.on_surface)
        self.surface_with_edges.toggled.connect(self.on_surface_with_edges)

    def get_windows(self):
        return self.parent.mdi.subWindowList()

    def on_wireframe(self):
        for window in self.get_windows():
            window.children()[-1].representation_wireframe()

    def on_surface(self):
        for window in self.get_windows():
            window.children()[-1].representation_surface()
            window.children()[-1].edge_visibility_off()

    def on_surface_with_edges(self):
        for window in self.get_windows():
            window.children()[-1].representation_surface()
            window.children()[-1].edge_visibility_on()


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
    filetype_viewers = {
        ".vtk": VTKUnStructuredGridViewer,
    }


    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("VTK Viewer")
        self.create_menu()
        self.statusBar()
        self.mdi = MyMdiArea(self)
        self.setCentralWidget(self.mdi)

        self.dw_representation = DockRepresentation(self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dw_representation)
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
        filepath = pathlib.Path(filename)
        ViewerClass = self.filetype_viewers[filepath.suffix]
        doc = ViewerClass(self.mdi, filepath)
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
