import sys
from PyQt5 import QtWidgets, QtCore, QtGui

class DragLabel(QtWidgets.QLabel):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

    def mouseMoveEvent(self, e):
        if e.buttons() == QtCore.Qt.MouseButton.LeftButton:
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            drag.setMimeData(mime)
            pixmap = QtGui.QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec(QtCore.Qt.DropAction.MoveAction)
        return super().mouseMoveEvent(e)
    
class ClassificationContainer(QtWidgets.QScrollArea):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setWidgetResizable(True)
        self.setFixedWidth(300)
        self.setAcceptDrops(True)
        self.mainWidget = QtWidgets.QWidget()
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.setWidget(self.mainWidget)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        widget = e.source()
        widgetToInsertBefore = 0
        for i in range(self.mainLayout.count()):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if e.pos().y() < currentWidget.y() + widget.width() // 2:
                widgetToInsertBefore = i
                break
        self.mainLayout.insertWidget(widgetToInsertBefore, widget)
        e.accept()

    def addTeam(self, teamNumber, teamName):
        teamLabel = DragLabel(text=f"{teamNumber} - {teamName}")
        self.mainLayout.addWidget(teamLabel)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainLayout = QtWidgets.QHBoxLayout()
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(self.mainLayout)
        self.setCentralWidget(centralWidget)
        '''self.teamListScrollArea = QtWidgets.QScrollArea()
        self.teamListScrollArea.setWidgetResizable(True)
        self.teamListScrollArea.setFixedWidth(300)
        self.teamListScrollArea.setAcceptDrops(True)
        teamListWidget = QtWidgets.QWidget()
        self.teamList = QtWidgets.QVBoxLayout()
        teamListWidget.setLayout(self.teamList)
        self.teamListScrollArea.setWidget(teamListWidget)
        self.mainLayout.addWidget(self.teamListScrollArea)'''
        self.teamListScrollArea = ClassificationContainer()
        self.mainLayout.addWidget(self.teamListScrollArea)
        self.teamClassificationListScrollArea = QtWidgets.QScrollArea()
        self.teamClassificationListScrollArea.setWidgetResizable(True)
        teamClassificationListWidget = QtWidgets.QWidget()
        self.classificationList = QtWidgets.QHBoxLayout()
        teamClassificationListWidget.setLayout(self.classificationList)
        self.teamClassificationListScrollArea.setWidget(teamClassificationListWidget)
        self.mainLayout.addWidget(self.teamClassificationListScrollArea)
        self.addTeam("4450", "Olympia Robotics Federation")
        self.addTeam("1690", "Orbit")
        self.addTeam("4450", "Olympia Robotics Federation")
        self.addTeam("1690", "Orbit")
        self.addTeam("4450", "Olympia Robotics Federation")
        self.addTeam("1690", "Orbit")
        self.addTeam("4450", "Olympia Robotics Federation")
        self.addTeam("1690", "Orbit")
        self.addTeam("4450", "Olympia Robotics Federation")
        self.addTeam("1690", "Orbit")
        self.addTeam("4450", "Olympia Robotics Federation")
        self.addTeam("1690", "Orbit")
        self.addTeam("4450", "Olympia Robotics Federation")
        self.addTeam("1690", "Orbit")
        self.addClassification()
        self.addClassification()
        self.addClassification()
        self.classificationList.addStretch()
        self.show()

    def addTeam(self, teamNumber, teamName):
        self.teamListScrollArea.addTeam(teamNumber, teamName)

    def addClassification(self):
        classificationContainer = ClassificationContainer()
        self.classificationList.addWidget(classificationContainer)

app = QtWidgets.QApplication(sys.argv)
mainWindow = MainWindow()
sys.exit(app.exec())