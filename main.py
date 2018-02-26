import abc
import sys
import pathlib

from math import pi, sin, cos

import vtk

# from vtk.qt import QVTKRenderWindowInteractor
# from qtpy import QtGui
# from qtpy import QtCore
# from qtpy import QtWidgets

from PyQt4 import QtGui
from PyQt4 import QtGui as QtWidgets
from PyQt4 import QtCore
from vtk.qt4 import QVTKRenderWindowInteractor


def rad2deg(rad):
    """Converts radians to degrees."""
    return rad*180./pi


def deg2rad(deg):
    """Converts degrees to radians."""
    return deg*pi/180.


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

    def view(self, azimuth, elevation):
        cam = self.renderer.GetActiveCamera()

        phi = deg2rad(azimuth)
        theta = deg2rad(elevation)

        # We compute the position of the camera on the surface of a sphere
        # centered at the center of the bounds, with radius chosen from the
        # bounds.
        bounds = self.mapper.GetBounds()
        r = max(bounds[1] - bounds[0],
                bounds[3] - bounds[2],
                bounds[5] - bounds[4]) * 2
        fp = ((bounds[1] + bounds[0]) * 0.5,
              (bounds[3] + bounds[2]) * 0.5,
              (bounds[5] + bounds[4]) * 0.5)
#        r = max(bounds[1::2] - bounds[::2]) * 2
#        fp = (bounds[1::2] + bounds[::2]) * 0.5

        # Find camera position.
        x = r*cos(phi)*sin(theta)
        y = r*sin(phi)*sin(theta)
        z = r*cos(theta)

        # Now setup the view.
        cam.SetFocalPoint(fp)
        cam.SetPosition(fp[0] + x, fp[1] + y, fp[2] + z)
        cam.ComputeViewPlaneNormal()
        self.renderer.ResetCameraClippingRange()

        # Reset Roll
        view_up = [0, 0, 1]
        if abs(elevation) < 1 or abs(elevation) > 179.:
            view_up = [sin(phi), cos(phi), 0]
        cam.SetViewUp(view_up)

        self.renderer.SetActiveCamera(cam)
        self.interactor.Render()

        return rad2deg(phi), rad2deg(theta), r, fp

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

    def parallel_projection_on(self):
        cam = self.renderer.GetActiveCamera()
        cam.ParallelProjectionOn()
        self.renderer.SetActiveCamera(cam)
        self.interactor.Render()

    def parallel_projection_off(self):
        cam = self.renderer.GetActiveCamera()
        cam.ParallelProjectionOff()
        self.renderer.SetActiveCamera(cam)
        self.interactor.Render()

    def backface_culling_on(self):
        self.actor.GetProperty().BackfaceCullingOn()
        self.interactor.Render()

    def backface_culling_off(self):
        self.actor.GetProperty().BackfaceCullingOff()
        self.interactor.Render()

    def frontface_culling_on(self):
        self.actor.GetProperty().FrontfaceCullingOn()
        self.interactor.Render()

    def frontface_culling_off(self):
        self.actor.GetProperty().FrontfaceCullingOff()
        self.interactor.Render()


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


class MyDock(QtWidgets.QDockWidget):
    def __init__(self, title, parent):
        super(MyDock, self).__init__(title, parent)
        self.parent = parent
        self.main_widget = QtWidgets.QWidget(self)
        self.setup_UI()
        self.setWidget(self.main_widget)

    @abc.abstractmethod
    def setup_UI(self):
        pass

    def get_vtk_viewers(self):
        # not the most elegant solution, but it seems to work...
        return [window.children()[-1] for window in self.parent.mdi.subWindowList()]


class DockRepresentation(MyDock):
    def __init__(self, parent):
        super(DockRepresentation, self).__init__("Representation", parent)

    def setup_UI(self):
        # create widgets
        self.wireframe = QtWidgets.QRadioButton("Wireframe", self)
        self.surface= QtWidgets.QRadioButton("Surface", self)
        self.surface_with_edges = QtWidgets.QRadioButton("Surface with Edges", self)
        # place widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.surface_with_edges)
        self.layout.addWidget(self.surface)
        self.layout.addWidget(self.wireframe)
        self.layout.addStretch(1)
        self.main_widget.setLayout(self.layout)
        # bind events
        self.wireframe.toggled.connect(self.on_wireframe)
        self.surface.toggled.connect(self.on_surface)
        self.surface_with_edges.toggled.connect(self.on_surface_with_edges)

    def on_wireframe(self):
        for viewer in self.get_vtk_viewers():
            viewer.representation_wireframe()

    def on_surface(self):
        for viewer in self.get_vtk_viewers():
            viewer.representation_surface()
            viewer.edge_visibility_off()

    def on_surface_with_edges(self):
        for viewer in self.get_vtk_viewers():
            viewer.representation_surface()
            viewer.edge_visibility_on()


class DockModel(MyDock):
    def __init__(self, parent):
        super(DockModel, self).__init__("Model", parent)
        self.no_culling.toggle()

    # def create_widgets(self):
    def setup_UI(self):
        # create widgets
        self.parallel_projection = QtWidgets.QCheckBox("Parallel Projection", self)
        self.back_culling = QtWidgets.QRadioButton("Backface Culling", self)
        self.front_culling = QtWidgets.QRadioButton("Frontface Culling", self)
        self.no_culling = QtWidgets.QRadioButton("No Culling", self)
        # place widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.parallel_projection)
        self.layout.addWidget(self.back_culling)
        self.layout.addWidget(self.front_culling)
        self.layout.addWidget(self.no_culling)
        self.layout.addStretch(1)
        self.main_widget.setLayout(self.layout)
        # bind events
        self.parallel_projection.stateChanged.connect(self.on_parallel_projection)
        self.back_culling.toggled.connect(self.on_back_culling)
        self.front_culling.toggled.connect(self.on_front_culling)
        self.no_culling.toggled.connect(self.on_no_culling)

    def on_back_culling(self):
        for viewer in self.get_vtk_viewers():
            viewer.frontface_culling_off()
            viewer.backface_culling_on()

    def on_front_culling(self):
        for viewer in self.get_vtk_viewers():
            viewer.backface_culling_off()
            viewer.frontface_culling_on()
            viewer.interactor.Render()

    def on_no_culling(self):
        for viewer in self.get_vtk_viewers():
            viewer.backface_culling_off()
            viewer.frontface_culling_off()

    def on_parallel_projection(self):
        state = self.parallel_projection.isChecked()
        for viewer in self.get_vtk_viewers():
            method = viewer.parallel_projection_on if state else viewer.parallel_projection_off
            method()


class DockCamera(MyDock):
    def __init__(self, parent):
        super(DockCamera, self).__init__("Camera", parent)

    def setup_UI(self):
        # create widgets
        self.elev_text = QtWidgets.QLineEdit(str(0), self)
        self.elev_text.setMaximumWidth(60)
        self.elev_slider = QtWidgets.QSlider(self)
        self.elev_slider.setRange(-180, 180)
        self.elev_slider.setValue(0)
        self.elev_slider.setOrientation(QtCore.Qt.Horizontal)
        #
        self.azim_text = QtWidgets.QLineEdit(str(0), self)
        self.azim_text.setMaximumWidth(60)
        self.azim_slider = QtWidgets.QSlider(self)
        self.azim_slider.setRange(0, 180)
        self.azim_slider.setValue(0)
        self.azim_slider.setOrientation(QtCore.Qt.Horizontal)
        #
        self.Xplus  = QtWidgets.QPushButton("X+", self)
        self.Xminus = QtWidgets.QPushButton("X-", self)
        self.Yplus  = QtWidgets.QPushButton("Y+", self)
        self.Yminus = QtWidgets.QPushButton("Y-", self)
        self.Zplus  = QtWidgets.QPushButton("Z+", self)
        self.Zminus = QtWidgets.QPushButton("Z-", self)
        # place widgets
        layout = QtWidgets.QFormLayout()
        layout.addRow("Elevation", self.elev_text)
        layout.addRow(self.elev_slider)
        layout.addRow("Azimuth", self.azim_text)
        layout.addRow(self.azim_slider)
        layout.addRow(self.Xplus, self.Xminus)
        layout.addRow(self.Yplus, self.Yminus)
        layout.addRow(self.Zplus, self.Zminus)
        self.main_widget.setLayout(layout)
        # bind events
        self.azim_slider.valueChanged.connect(self.on_camera_slider)
        self.elev_slider.valueChanged.connect(self.on_camera_slider)
        self.Xplus.pressed.connect(self.on_Xplus)
        self.Xminus.pressed.connect(self.on_Xminus)
        self.Yplus.pressed.connect(self.on_Yplus)
        self.Yminus.pressed.connect(self.on_Yminus)
        self.Zplus.pressed.connect(self.on_Zplus)
        self.Zminus.pressed.connect(self.on_Zminus)

    def on_camera_slider(self):
        azimuth = self.azim_slider.value()
        elevation = self.elev_slider.value()
        self.azim_text.setText(str(azimuth))
        self.elev_text.setText(str(elevation))
        for viewer in self.get_vtk_viewers():
            viewer.view(elevation, azimuth)

    def on_Xplus(self):
        """It calls implicitly on_camera_slider method"""
        self.elev_slider.setValue(180)
        self.azim_slider.setValue(90)
        # In case the user has rotated the view with the mouse,
        # the slider will not have changed. So we explicitly call the view method
        for viewer in self.get_vtk_viewers():
            viewer.view(180, 90)

    def on_Xminus(self):
        """It calls implicitly on_camera_slider method"""
        self.elev_slider.setValue(0)
        self.azim_slider.setValue(90)
        # In case the user has rotated the view with the mouse,
        # the slider will not have changed. So we explicitly call the view method
        for viewer in self.get_vtk_viewers():
            viewer.view(0, 90)

    def on_Yplus(self):
        """It calls implicitly on_camera_slider method"""
        self.elev_slider.setValue(-90)
        self.azim_slider.setValue(90)
        # In case the user has rotated the view with the mouse,
        # the slider will not have changed. So we explicitly call the view method
        for viewer in self.get_vtk_viewers():
            viewer.view(-90, 90)

    def on_Yminus(self):
        """It calls implicitly on_camera_slider method"""
        self.elev_slider.setValue(90)
        self.azim_slider.setValue(90)
        # In case the user has rotated the view with the mouse,
        # the slider will not have changed. So we explicitly call the view method
        for viewer in self.get_vtk_viewers():
            viewer.view(90, 90)

    def on_Zplus(self):
        """It calls implicitly on_camera_slider method"""
        self.elev_slider.setValue(0)
        self.azim_slider.setValue(180)
        # In case the user has rotated the view with the mouse,
        # the slider will not have changed. So we explicitly call the view method
        for viewer in self.get_vtk_viewers():
            viewer.view(0, 180)

    def on_Zminus(self):
        """It calls implicitly on_camera_slider method"""
        self.elev_slider.setValue(0)
        self.azim_slider.setValue(0)
        # In case the user has rotated the view with the mouse,
        # the slider will not have changed. So we explicitly call the view method
        for viewer in self.get_vtk_viewers():
            viewer.view(0, 0)


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

        self.dw_camera = DockCamera(self)
        self.dw_representation = DockRepresentation(self)
        self.dw_model = DockModel(self)

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dw_camera)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dw_representation)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dw_model)

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
