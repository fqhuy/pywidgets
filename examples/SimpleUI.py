from PyQt5 import QtGui
from PyQt5.QtGui import QBrush
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QGridLayout, QWidget, QAction, QGraphicsView, \
    QMainWindow, QDockWidget

from GraphicsItems import InteractiveScene, SplineItem
from DataModels import Spline
import sys


class MainGUI(QMainWindow):
    def __init__(self):
        super(MainGUI, self).__init__()
        self.initUI()

    def initUI(self):
        # right panel
        rightLayout = QVBoxLayout()
        gridLayout = QGridLayout()
        rightPanel = QWidget()
        rightPanel.setLayout(rightLayout)

        # Add the panel to a dock for flexibility
        rightDock = QDockWidget("Control Panel", self)
        rightDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        rightDock.setWidget(rightPanel)
        self.addDockWidget(Qt.RightDockWidgetArea, rightDock)

        # The main widget
        self.view = QGraphicsView()
        self.view.scale(1,-1)
        self.view.centerOn(0, 0)
        self.scene = InteractiveScene(self)  # QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(Qt.white, Qt.SolidPattern))

        # Add the axes
        self.scene.addLine(0, 0, 1000, 0)
        self.scene.addLine(0, 0, 0, 1000)

        test_geo = Spline([[0, 0], [100, 100], [0, 150], [50, 200]])
        test_item = SplineItem(test_geo)
        # test_item = PolylineItem([[0, 0], [100, 0], [100, 100], [0, 100]])
        # test_item = RectItem(5, 5, 55, 55)
        # test_item = CircleItem(200, 200, 50)
        # test_item = RingItem(200, 200, 50, 100)
        self.scene.addItem(test_item)

        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

        # Menus, status bar, tool bar and stuff
        exitAction = QAction(QtGui.QIcon.fromTheme('application-exit'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        self.statusBar().showMessage('Hi there!')

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAction)

        self.setGeometry(0, 0, 1200, 800)
        self.setWindowTitle('SimpleUI 1.0')
        self.showMaximized()


def main():
    app = QApplication(sys.argv)
    ex = MainGUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    # PYTHONPATH=/Users/huphan-osx/perforce/patternista python Main.py
