import sys
import requests
import json
from PyQt5 import QtWidgets, QtCore, QtGui

TBAKey = "V86v838SJb4GJhpaNbElRqLSLHFhyBc0LPBscDetwnXZosPS2pmtehPSNNsY6Hy1"

class TeamLabel(QtWidgets.QWidget):
    def __init__(self, teamNumber, teamName, eliminated=False, isFromAllTeamContainer=False, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.teamNumber = teamNumber
        self.teamName = teamName
        self.eliminated = eliminated
        self.setMinimumHeight(50)
        self.isFromAllTeamContainer = isFromAllTeamContainer
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.teamLabel = QtWidgets.QLabel(text=f"{teamNumber} - {teamName}")
        self.teamLabel.setText(f"{teamNumber} - {teamName}")
        currentFont = self.teamLabel.font()
        currentFont.setStrikeOut(self.eliminated)
        self.teamLabel.setFont(currentFont)
        self.eliminateButton = QtWidgets.QPushButton(text="Eliminate", checkable=True)
        self.eliminateButton.clicked.connect(self.eliminate)
        self.eliminateButton.setChecked(self.eliminated)
        self.mainLayout.addWidget(self.teamLabel, stretch=1)
        if isFromAllTeamContainer:
            self.mainLayout.addWidget(self.eliminateButton)

    def mouseMoveEvent(self, e):
        if not self.eliminated and e.buttons() == QtCore.Qt.MouseButton.LeftButton:
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            drag.setMimeData(mime)
            pixmap = QtGui.QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec(QtCore.Qt.DropAction.MoveAction)
        return super().mouseMoveEvent(e)

    def eliminate(self):
        self.eliminated = self.eliminateButton.isChecked()
        if (self.eliminated):
            removeTeam(self.teamNumber)
        currentFont = self.teamLabel.font()
        currentFont.setStrikeOut(self.eliminated)
        self.teamLabel.setFont(currentFont)
        addNeedToSaveFlag()

class ClassificationContainer(QtWidgets.QWidget):
    def __init__(self, isAllTeamContainer=False, name="Untitled Classification", parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.isAllTeamContainer = isAllTeamContainer
        self.setFixedWidth(400)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.headerWidget = QtWidgets.QWidget()
        self.headerLayout = QtWidgets.QHBoxLayout()
        self.headerWidget.setLayout(self.headerLayout)
        self.nameEntry = QtWidgets.QLineEdit(text=name)
        self.nameEntry.textChanged.connect(self.nameChanged)
        self.headerLayout.addWidget(self.nameEntry, stretch=1)
        self.removeButton = QtWidgets.QPushButton(text="Remove")
        self.removeButton.clicked.connect(self.remove)
        self.headerLayout.addWidget(self.removeButton)
        if not isAllTeamContainer:
            self.mainLayout.addWidget(self.headerWidget)
        self.mainScrollArea = QtWidgets.QScrollArea()
        self.mainScrollArea.setWidgetResizable(True)
        self.teamListWidget = ClassificationTeamList(self.isAllTeamContainer)
        self.mainScrollArea.setWidget(self.teamListWidget)
        self.mainLayout.addWidget(self.mainScrollArea, stretch=1)
        self.setLayout(self.mainLayout)

    def addTeam(self, teamNumber, teamName, eliminated=False):
        self.teamListWidget.addTeam(teamNumber, teamName, eliminated, -1)
    
    def remove(self):
        self.parent().layout().removeWidget(self)
        addNeedToSaveFlag()

    def getTeams(self):
        return {
            "name": self.nameEntry.text(),
            "teams": self.teamListWidget.getTeams()
        }

    def emptyTeams(self):
        self.teamListWidget.emptyTeams()

    def nameChanged(self):
        addNeedToSaveFlag()

    def removeTeam(self, teamNumber):
        self.teamListWidget.removeTeam(teamNumber)

class ClassificationTeamList(QtWidgets.QWidget):
    def __init__(self, isAllTeamContainer=False, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setAcceptDrops(True)
        self.isAllTeamContainer = isAllTeamContainer
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addStretch()
        self.setLayout(self.mainLayout)
    
    def dragEnterEvent(self, e):
        if (type(e.source()) == TeamLabel):
            e.accept()

    def dropEvent(self, e):
        if (type(e.source()) == TeamLabel):
            widget = e.source()
            widgetToInsertBefore = -1
            for i in range(self.mainLayout.count()):
                currentWidget = self.mainLayout.itemAt(i).widget()
                if type(currentWidget) == TeamLabel and e.pos().y() < currentWidget.y() + currentWidget.size().height():
                    widgetToInsertBefore = i
                    break
            if not widget.isFromAllTeamContainer:
                widget.parent().layout().removeWidget(widget)
            if not self.isAllTeamContainer:
                self.addTeam(widget.teamNumber, widget.teamName, widget.eliminated, widgetToInsertBefore)
            addNeedToSaveFlag()
            e.accept()

    def addTeam(self, teamNumber, teamName, eliminated=False,  index=-1):
        teamLabel = TeamLabel(teamNumber, teamName, eliminated, self.isAllTeamContainer)
        if (index == -1):
            self.mainLayout.insertWidget(self.mainLayout.count() - 1, teamLabel)
        else:
            self.mainLayout.insertWidget(index, teamLabel)

    def getTeams(self):
        teams = []
        for i in range(self.mainLayout.count()):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel:
                teams.append({
                    "teamNumber": currentWidget.teamNumber,
                    "teamName": currentWidget.teamName,
                    "eliminated": currentWidget.eliminated
                })
        return teams
    
    def emptyTeams(self):
        for i in reversed(range(self.mainLayout.count())):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel:
                self.mainLayout.removeWidget(currentWidget)

    def removeTeam(self, teamNumber):
        for i in reversed(range(self.mainLayout.count())):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel and currentWidget.teamNumber == teamNumber:
                self.mainLayout.removeWidget(currentWidget)

class AutoPopulateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.teams = None
        self.filePath = None
        self.setWindowModality(True)
        self.setWindowTitle("Find Teams")
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.seasonInputLabel = QtWidgets.QLabel(text="Season")
        self.mainLayout.addWidget(self.seasonInputLabel)
        self.seasonInput = QtWidgets.QSpinBox(minimum=1000, maximum=3000, value=2025)
        self.mainLayout.addWidget(self.seasonInput)
        self.teamInputLabel = QtWidgets.QLabel(text="Team number")
        self.mainLayout.addWidget(self.teamInputLabel)
        self.teamInput = QtWidgets.QSpinBox(minimum=1, maximum=20000, value=4450)
        self.mainLayout.addWidget(self.teamInput)
        self.findEventsButton = QtWidgets.QPushButton(text="Find events")
        self.findEventsButton.clicked.connect(self.findEvents)
        self.mainLayout.addWidget(self.findEventsButton)
        self.eventLabel = QtWidgets.QLabel(text="Event")
        self.mainLayout.addWidget(self.eventLabel)
        self.eventInput = QtWidgets.QComboBox()
        self.eventInput.setEnabled(False)
        self.mainLayout.addWidget(self.eventInput)
        self.dialogButtons = QtWidgets.QDialogButtonBox()
        self.dialogButtons.setStandardButtons(QtWidgets.QDialogButtonBox.Open | QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.getTeams)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Open).clicked.connect(self.openPickListDialog)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.mainLayout.addWidget(self.dialogButtons)
        self.show()

    def findEvents(self):
        self.eventInput.clear()
        year = self.seasonInput.text()
        team = self.teamInput.text()
        response = json.loads(requests.get(f"https://www.thebluealliance.com/api/v3/team/frc{team}/events/{year}/simple", headers={"X-TBA-Auth-Key": TBAKey}).text)
        self.eventKeys = []
        for i in response:
            self.eventKeys.append(i["key"])
            self.eventInput.addItem(i["name"])
        if (len(self.eventKeys) > 0):
            self.eventInput.setEnabled(True)
            self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.eventInput.setEnabled(False)
            self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def getTeams(self):
        eventKey = self.eventKeys[self.eventInput.currentIndex()]
        response = json.loads(requests.get(f"https://www.thebluealliance.com/api/v3/event/{eventKey}/teams/simple", headers={"X-TBA-Auth-Key": TBAKey}).text)
        self.teams = {}
        for i in response:
            if i["team_number"] != int(self.teamInput.text()):
                self.teams[i["team_number"]] = i["nickname"]
        self.teams = dict(sorted(self.teams.items()))
        self.accept()

    def openPickListDialog(self):
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, filter="JSON files (*.json)")[0]
        if (filePath != ""):
            self.filePath = filePath
            self.accept()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filePath = None
        self.needToSave = False
        self.mainLayout = QtWidgets.QHBoxLayout()
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(self.mainLayout)
        self.setCentralWidget(centralWidget)
        self.teamListScrollArea = ClassificationContainer(True)
        self.mainLayout.addWidget(self.teamListScrollArea)
        self.teamClassificationListScrollArea = QtWidgets.QScrollArea()
        self.teamClassificationListScrollArea.setWidgetResizable(True)
        teamClassificationListWidget = QtWidgets.QWidget()
        self.classificationList = QtWidgets.QHBoxLayout()
        teamClassificationListWidget.setLayout(self.classificationList)
        self.teamClassificationListScrollArea.setWidget(teamClassificationListWidget)
        self.mainLayout.addWidget(self.teamClassificationListScrollArea)
        self.classificationList.addStretch()
        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        newAction = QtWidgets.QAction("New", self)
        newAction.triggered.connect(self.newPickList)
        fileMenu.addAction(newAction)
        openAction = QtWidgets.QAction("Open", self)
        openAction.triggered.connect(self.openPickListDialog)
        fileMenu.addAction(openAction)
        saveAction = QtWidgets.QAction("Save", self)
        saveAction.triggered.connect(self.savePickList)
        fileMenu.addAction(saveAction)
        saveAsAction = QtWidgets.QAction("Save as", self)
        saveAsAction.triggered.connect(self.savePickListAs)
        fileMenu.addAction(saveAsAction)
        fileMenu.addSeparator()
        exitAction = QtWidgets.QAction("Exit", self)
        exitAction.triggered.connect(self.saveAndExit)
        fileMenu.addAction(exitAction)
        classificationMenu = menu.addMenu("Classification")
        addClassificationAction = QtWidgets.QAction("Add classification", self)
        addClassificationAction.triggered.connect(lambda: self.addClassification("Untitled Classification", True))
        classificationMenu.addAction(addClassificationAction)
        self.setWindowTitle("Scouting Picklist")
        self.setMinimumSize(1000, 500)
        self.showMaximized()
        self.addClassification("Overall picks")
        autoPopulateDialog = AutoPopulateDialog(self)
        if autoPopulateDialog.exec() == 0:
            sys.exit()
        else:
            if autoPopulateDialog.filePath != None:
                self.filePath = autoPopulateDialog.filePath
                self.openPickList()
            elif autoPopulateDialog.teams != None:
                for teamNumber, teamName in autoPopulateDialog.teams.items():
                    self.addTeam(teamNumber, teamName)

    def addTeam(self, teamNumber, teamName, eliminated=False):
        self.teamListScrollArea.addTeam(teamNumber, teamName, eliminated)

    def addClassification(self, name="Untitled Classification", savingRequired=False):
        classificationContainer = ClassificationContainer(False, name)
        self.classificationList.insertWidget(self.classificationList.count() - 1, classificationContainer)
        if savingRequired:
            addNeedToSaveFlag()
        return classificationContainer
    
    def removeTeam(self, teamNumber):
        for i in reversed(range(self.classificationList.count())):
            currentWidget = self.classificationList.itemAt(i).widget()
            if type(currentWidget) == ClassificationContainer:
                currentWidget.removeTeam(teamNumber)
    
    def clearClassifications(self, addOveralPicks=True):
        self.teamListScrollArea.emptyTeams()
        for i in reversed(range(self.classificationList.count())):
            currentWidget = self.classificationList.itemAt(i).widget()
            if type(currentWidget) == ClassificationContainer:
                self.classificationList.removeWidget(currentWidget)
        if addOveralPicks:
            self.addClassification("Overall picks")

    def savePickListAs(self):
        filePath = QtWidgets.QFileDialog.getSaveFileName(self, filter="JSON files (*.json)")[0]
        if (filePath != ""):
            self.filePath = filePath
            self.savePickList()

    def savePickList(self):
        if (self.filePath == None):
            self.savePickListAs()
        else:
            allTeams = self.teamListScrollArea.getTeams()["teams"]
            allClassifications = []
            for i in range(self.classificationList.count()):
                currentWidget = self.classificationList.itemAt(i).widget()
                if (type(currentWidget) == ClassificationContainer):
                    allClassifications.append(currentWidget.getTeams())
            teamJson = json.dumps({
                "allTeams": allTeams,
                "classifications": allClassifications
            })
            file = open(self.filePath, "w")
            file.write(teamJson)
            file.close()
            self.needToSave = False

    def openPickList(self):
        file = open(self.filePath, "r")
        teamJson = json.loads(file.read())
        file.close()
        self.clearClassifications(False)
        self.needToSave = False
        for team in teamJson["allTeams"]:
            self.addTeam(team["teamNumber"], team["teamName"], team["eliminated"])
        for classification in teamJson["classifications"]:
            classificationContainer = self.addClassification(classification["name"])
            for team in classification["teams"]:
                classificationContainer.addTeam(team["teamNumber"], team["teamName"], team["eliminated"])

    def openPickListDialog(self):
        if self.confirmSave():
            filePath = QtWidgets.QFileDialog.getOpenFileName(self, filter="JSON files (*.json)")[0]
            if (filePath != ""):
                self.filePath = filePath
                self.openPickList()

    def newPickList(self):
        if self.confirmSave():
            autoPopulateDialog = AutoPopulateDialog(self)
            if autoPopulateDialog.exec() == 1:
                self.needToSave = False
                self.filePath = None
                if autoPopulateDialog.filePath != None:
                    self.filePath = autoPopulateDialog.filePath
                    self.openPickList()
                elif autoPopulateDialog.teams != None:
                    self.clearClassifications(True)
                    for teamNumber, teamName in autoPopulateDialog.teams.items():
                        self.addTeam(teamNumber, teamName)

    def closeEvent(self, e):
        if self.confirmSave():
            e.accept()
        else:
            e.ignore()

    def confirmSave(self):
        if self.needToSave:
            confirmationResult = QtWidgets.QMessageBox.warning(self, "Save Picklist", "Do you want to save this picklist before closing?", QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            if confirmationResult == QtWidgets.QMessageBox.Save:
                self.savePickList()
                return not self.needToSave
            elif confirmationResult == QtWidgets.QMessageBox.Discard:
                return True
            else:
                return False
        else:
            return True
        
    def saveAndExit(self):
        if self.confirmSave():
            sys.exit()

def addNeedToSaveFlag():
    mainWindow.needToSave = True

def removeTeam(teamNumber):
    mainWindow.removeTeam(teamNumber)

app = QtWidgets.QApplication(sys.argv)
mainWindow = MainWindow()
sys.exit(app.exec())