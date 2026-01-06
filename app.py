import sys
import requests
import json
import asyncio
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui
from os import path

programDirectory = Path(__file__).parent
configPath = programDirectory / "config.json"

if path.exists(configPath):
    try:
        file = open(configPath)
        TBAKey = json.loads(file.read())["tbaKey"]
        file.close()
    except:
        TBAKey = ""
else:
    TBAKey = ""

class TeamLabel(QtWidgets.QWidget):
    def __init__(self, teamNumber, teamName, eliminated=False, isFromAllTeamContainer=False, note="", parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.teamNumber = teamNumber
        self.teamName = teamName
        self.eliminated = eliminated
        self.note = note
        self.setMinimumHeight(50)
        self.isFromAllTeamContainer = isFromAllTeamContainer
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.teamLabel = QtWidgets.QLabel(text=f"{teamNumber} - {teamName}")
        self.teamLabel.setText(f"{teamNumber} - {teamName}")
        self.teamLabel.setWordWrap(True)
        currentFont = self.teamLabel.font()
        currentFont.setStrikeOut(self.eliminated)
        self.teamLabel.setFont(currentFont)
        self.eliminateButton = QtWidgets.QPushButton(text="Eliminate", checkable=True)
        self.eliminateButton.clicked.connect(self.eliminate)
        self.eliminateButton.setChecked(self.eliminated)
        self.noteButton = QtWidgets.QPushButton(text="Note")
        self.noteButton.clicked.connect(self.showNote)
        self.mainLayout.addWidget(self.teamLabel, stretch=1)
        if isFromAllTeamContainer:
            self.mainLayout.addWidget(self.eliminateButton)
        else:
            self.mainLayout.addWidget(self.noteButton)

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

    def highlightTeam(self, teamExists):
        if teamExists:
            self.teamLabel.setStyleSheet("color: red;")
        else:
            self.teamLabel.setStyleSheet("color: lime;")

    def unhighlightTeam(self):
        self.teamLabel.setStyleSheet("")

    def showNote(self):
        noteDialog = NoteDialog(self.note, mainWindow)
        if noteDialog.exec() == 1:
            self.note = noteDialog.noteText
            addNeedToSaveFlag()

class ClassificationContainer(QtWidgets.QWidget):
    def __init__(self, isAllTeamContainer=False, name="Untitled classification", selected=False, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.isAllTeamContainer = isAllTeamContainer
        self.setFixedWidth(400)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.headerWidget = QtWidgets.QWidget()
        self.headerLayout = QtWidgets.QHBoxLayout()
        self.headerWidget.setLayout(self.headerLayout)
        self.teamSelectionButton = QtWidgets.QCheckBox()
        self.teamSelectionButton.setChecked(selected)
        self.teamSelectionButton.clicked.connect(self.selectContainer)
        self.headerLayout.addWidget(self.teamSelectionButton)
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
        self.teamListWidget.teamDropped.signal.connect(self.updateSelection)
        self.teamListWidget.teamRemoved.signal.connect(self.updateSelection)
        self.mainScrollArea.setWidget(self.teamListWidget)
        self.mainLayout.addWidget(self.mainScrollArea, stretch=1)
        self.setLayout(self.mainLayout)

    def addTeam(self, teamNumber, teamName, eliminated=False, note=""):
        self.teamListWidget.addTeam(teamNumber, teamName, eliminated, note, -1)
    
    def remove(self):
        self.parent().layout().removeWidget(self)
        if self.teamSelectionButton.isChecked():
            mainWindow.unselectClassifications()
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

    def deselect(self):
        self.teamSelectionButton.setChecked(False)

    def selectContainer(self):
        if self.teamSelectionButton.isChecked():
            mainWindow.selectClassification(self)
        else:
            mainWindow.unselectClassifications()
        addNeedToSaveFlag()

    def updateSelection(self):
        if self.teamSelectionButton.isChecked():
            mainWindow.selectClassification(self)

    def getTeamNumbers(self):
        return self.teamListWidget.getTeamNumbers()
    
    def highlightTeams(self, teamNumbers):
        self.teamListWidget.highlightTeams(teamNumbers)

    def unhighlightTeams(self):
        self.teamListWidget.unhighlightTeams()

class ClassificationTeamDropSignalEmitter(QtCore.QObject):
    signal = QtCore.pyqtSignal()

class ClassificationTeamRemovedSingalEmitter(QtCore.QObject):
    signal = QtCore.pyqtSignal()

class ClassificationTeamList(QtWidgets.QWidget):
    def __init__(self, isAllTeamContainer=False, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.teamDropped = ClassificationTeamDropSignalEmitter()
        self.teamRemoved = ClassificationTeamRemovedSingalEmitter()
        self.setAcceptDrops(True)
        self.isAllTeamContainer = isAllTeamContainer
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addSpacing(50)
        self.mainLayout.addStretch()
        self.setLayout(self.mainLayout)
    
    def dragEnterEvent(self, e):
        if (type(e.source()) == TeamLabel):
            e.accept()

    def dropEvent(self, e):
        if (type(e.source()) == TeamLabel):
            widget = e.source()
            widgetToInsertBefore = -1
            if not self.isAllTeamContainer and widget.parent() != self and self.hasTeam(widget.teamNumber):
                QtWidgets.QMessageBox.warning(self, "Team Already Added", f"You already have {widget.teamNumber} - {widget.teamName} in this classification")
                e.accept()
            else:
                for i in range(self.mainLayout.count()):
                    currentWidget = self.mainLayout.itemAt(i).widget()
                    if type(currentWidget) == TeamLabel and e.pos().y() < currentWidget.y() + currentWidget.size().height():
                        widgetToInsertBefore = i
                        break
                if not widget.isFromAllTeamContainer:
                    widget.parent().layout().removeWidget(widget)
                    widget.parent().teamRemoved.signal.emit()
                if not self.isAllTeamContainer:
                    self.addTeam(widget.teamNumber, widget.teamName, widget.eliminated, widget.note, widgetToInsertBefore)
                addNeedToSaveFlag()
                self.teamDropped.signal.emit()
                e.accept()

    def addTeam(self, teamNumber, teamName, eliminated=False, note="",  index=-1):
        teamLabel = TeamLabel(teamNumber, teamName, eliminated, self.isAllTeamContainer, note)
        if (index == -1):
            self.mainLayout.insertWidget(self.mainLayout.count() - 2, teamLabel)
        else:
            self.mainLayout.insertWidget(index, teamLabel)

    def getTeams(self):
        teams = []
        for i in range(self.mainLayout.count()):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel:
                if self.isAllTeamContainer:
                    teams.append({
                        "teamNumber": currentWidget.teamNumber,
                        "teamName": currentWidget.teamName,
                        "eliminated": currentWidget.eliminated
                    })
                else:
                    teams.append({
                        "teamNumber": currentWidget.teamNumber,
                        "teamName": currentWidget.teamName,
                        "note": currentWidget.note
                    })
        return teams
    
    def getTeamNumbers(self):
        teams = []
        for i in range(self.mainLayout.count()):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel:
                teams.append(currentWidget.teamNumber)
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
            
    def highlightTeams(self, teamNumbers):
        for i in range(self.mainLayout.count()):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel:
                if currentWidget.teamNumber in teamNumbers:
                    currentWidget.highlightTeam(True)
                else:
                    currentWidget.highlightTeam(False)

    def unhighlightTeams(self):
        for i in range(self.mainLayout.count()):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel:
                currentWidget.unhighlightTeam()

    def hasTeam(self, teamNumber):
        for i in range(self.mainLayout.count()):
            currentWidget = self.mainLayout.itemAt(i).widget()
            if type(currentWidget) == TeamLabel and currentWidget.teamNumber == teamNumber:
                return True
        return False

class NoteDialog(QtWidgets.QDialog):
    def __init__(self, currentText="", parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setWindowModality(True)
        self.setWindowTitle("Picklist Note")
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.noteInput = QtWidgets.QTextEdit()
        self.noteInput.setAcceptRichText(False)
        self.noteInput.setPlainText(currentText)
        self.mainLayout.addWidget(self.noteInput)
        self.dialogButtons = QtWidgets.QDialogButtonBox()
        self.dialogButtons.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.dialogButtons)
        self.show()
    
    def accept(self):
        self.noteText = self.noteInput.toPlainText()
        return super().accept()

class AutoPopulateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.teams = None
        self.filePath = None
        self.eventKeys = []
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
        self.findEventsButton.clicked.connect(lambda: asyncio.run(self.findEvents()))
        self.mainLayout.addWidget(self.findEventsButton)
        self.eventLabel = QtWidgets.QLabel(text="Event")
        self.mainLayout.addWidget(self.eventLabel)
        self.eventInput = QtWidgets.QComboBox()
        self.eventInput.setEnabled(False)
        self.mainLayout.addWidget(self.eventInput)
        self.dialogButtons = QtWidgets.QDialogButtonBox()
        self.dialogButtons.setStandardButtons(QtWidgets.QDialogButtonBox.Open | QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(lambda: asyncio.run(self.getTeams()))
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Open).clicked.connect(self.openPickListDialog)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.mainLayout.addWidget(self.dialogButtons)
        self.show()

    async def findEvents(self):
        self.findEventsButton.setEnabled(False)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        try:
            year = self.seasonInput.text()
            team = self.teamInput.text()
            response = json.loads(requests.get(f"https://www.thebluealliance.com/api/v3/team/frc{team}/events/{year}/simple", headers={"X-TBA-Auth-Key": TBAKey}).text)
            self.eventKeys = []
            self.eventNames = []
            for i in response:
                self.eventKeys.append(i["key"])
                self.eventNames.append(i["name"])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
        else:
            self.eventInput.clear()
            for i in self.eventNames:
                self.eventInput.addItem(i)
        if (len(self.eventKeys) > 0):
            self.eventInput.setEnabled(True)
            self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.eventInput.setEnabled(False)
            self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.findEventsButton.setEnabled(True)

    async def getTeams(self):
        self.findEventsButton.setEnabled(False)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        eventKey = self.eventKeys[self.eventInput.currentIndex()]
        try:
            response = json.loads(requests.get(f"https://www.thebluealliance.com/api/v3/event/{eventKey}/teams/simple", headers={"X-TBA-Auth-Key": TBAKey}).text)
            self.teams = {}
            for i in response:
                if i["team_number"] != int(self.teamInput.text()):
                    self.teams[i["team_number"]] = i["nickname"]
            self.teams = dict(sorted(self.teams.items()))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
        else:
            self.accept()
        self.findEventsButton.setEnabled(True)
        self.dialogButtons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

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
        addClassificationAction.triggered.connect(lambda: self.addClassification("Untitled classification", True))
        classificationMenu.addAction(addClassificationAction)
        if path.exists("icon.ico"):
            self.setWindowIcon(QtGui.QIcon("icon.ico"))
        elif path.exists("_internal\\icon.ico"):
            self.setWindowIcon(QtGui.QIcon("_internal\\icon.ico"))
        self.setWindowTitle("Scouting Picklist")
        self.setMinimumSize(1000, 500)
        self.showMaximized()
        classification = self.addClassification("Overall picks")
        classification.teamSelectionButton.setChecked(True)
        self.newPickList(True, False)

    def addTeam(self, teamNumber, teamName, eliminated=False):
        self.teamListScrollArea.addTeam(teamNumber, teamName, eliminated)

    def addClassification(self, name="Untitled classification", savingRequired=False):
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
                if currentWidget.teamSelectionButton.isChecked():
                    self.selectClassification(currentWidget)
    
    def clearClassifications(self, addOveralPicks=True):
        self.teamListScrollArea.emptyTeams()
        for i in reversed(range(self.classificationList.count())):
            currentWidget = self.classificationList.itemAt(i).widget()
            if type(currentWidget) == ClassificationContainer:
                self.classificationList.removeWidget(currentWidget)
        if addOveralPicks:
            classification = self.addClassification("Overall picks")
            classification.teamSelectionButton.setChecked(True)
            self.selectClassification(classification)

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
            selectedClassification = -1
            for i in range(self.classificationList.count()):
                currentWidget = self.classificationList.itemAt(i).widget()
                if (type(currentWidget) == ClassificationContainer):
                    allClassifications.append(currentWidget.getTeams())
                    if currentWidget.teamSelectionButton.isChecked():
                        selectedClassification = i
            teamJson = json.dumps({
                "allTeams": allTeams,
                "classifications": allClassifications,
                "selectedClassification": selectedClassification
            })
            file = open(self.filePath, "w")
            file.write(teamJson)
            file.close()
            self.needToSave = False
            self.setWindowTitle("Scouting Picklist")

    def openPickList(self, filePath):
        allTeams = []
        classifications = []
        selectedClassification = -1
        try:
            file = open(filePath, "r")
            teamJson = json.loads(file.read())
            file.close()
            selectedClassification = teamJson["selectedClassification"]
            for team in teamJson["allTeams"]:
                allTeams.append({
                    "teamNumber": team["teamNumber"],
                    "teamName": team["teamName"],
                    "eliminated": team["eliminated"]
                })
            for classification in teamJson["classifications"]:
                classificationTeams = []
                for team in classification["teams"]:
                    classificationTeams.append({
                        "teamNumber": team["teamNumber"],
                        "teamName": team["teamName"],
                        "note": team["note"]
                    })
                classifications.append({
                    "name": classification["name"],
                    "teams": classification["teams"]
                })
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return False
        else:
            self.clearClassifications(False)
            for team in allTeams:
                self.addTeam(team["teamNumber"], team["teamName"], team["eliminated"])
            for i in range(len(classifications)):
                classificationContainer = self.addClassification(classifications[i]["name"])
                for team in classifications[i]["teams"]:
                    classificationContainer.addTeam(team["teamNumber"], team["teamName"], False, team["note"])
                if i == selectedClassification:
                    classificationContainer.teamSelectionButton.setChecked(True)
                    self.selectClassification(classificationContainer)
            self.filePath = filePath
            self.needToSave = False
            self.setWindowTitle("Scouting Picklist")
            return True

    def openPickListDialog(self):
        if self.confirmSave():
            filePath = QtWidgets.QFileDialog.getOpenFileName(self, filter="JSON files (*.json)")[0]
            if (filePath != ""):
                self.openPickList(filePath)

    def newPickList(self, closeOnDecline=False, confrimSave=True):
        if not confrimSave or self.confirmSave():
            autoPopulateDialog = AutoPopulateDialog(self)
            if autoPopulateDialog.exec() == 0:
                if closeOnDecline:
                    sys.exit()
            else:
                if autoPopulateDialog.filePath != None:
                    if not self.openPickList(autoPopulateDialog.filePath):
                        self.newPickList(closeOnDecline, False)
                elif autoPopulateDialog.teams != None:
                    self.needToSave = False
                    self.setWindowTitle("Scouting Picklist")
                    self.filePath = None
                    self.clearClassifications(True)
                    for teamNumber, teamName in autoPopulateDialog.teams.items():
                        self.addTeam(teamNumber, teamName)
                    self.selectClassification(self.classificationList.itemAt(0).widget())

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

    def addNeedToSaveFlag(self):
        self.needToSave = True
        self.setWindowTitle("*Scouting Picklist")

    def selectClassification(self, widget):
        for i in range(self.classificationList.count()):
            currentWidget = self.classificationList.itemAt(i).widget()
            if currentWidget != widget and type(currentWidget) == ClassificationContainer:
                currentWidget.deselect()
        teams = widget.getTeamNumbers()
        self.teamListScrollArea.highlightTeams(teams)

    def unselectClassifications(self):
        self.teamListScrollArea.unhighlightTeams()

def addNeedToSaveFlag():
    mainWindow.addNeedToSaveFlag()

def removeTeam(teamNumber):
    mainWindow.removeTeam(teamNumber)

app = QtWidgets.QApplication(sys.argv)
app.setStyle(QtWidgets.QStyleFactory.create("fusion"))
palette = QtGui.QPalette()
palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 255, 255))
palette.setColor(QtGui.QPalette.Button, QtGui.QColor(50, 50, 50))
palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Button, QtGui.QColor(33, 33, 33))
palette.setColor(QtGui.QPalette.Light, QtGui.QColor(75, 75, 75))
palette.setColor(QtGui.QPalette.Midlight, QtGui.QColor(62, 62, 62))
palette.setColor(QtGui.QPalette.Dark, QtGui.QColor(25, 25, 25))
palette.setColor(QtGui.QPalette.Mid, QtGui.QColor(33, 33, 33))
palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(255, 255, 255, 127))
palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 255, 255))
palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(255, 255, 255))
palette.setColor(QtGui.QPalette.Base, QtGui.QColor(0, 0, 0))
palette.setColor(QtGui.QPalette.Window, QtGui.QColor(50, 50, 50))
palette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(0, 0, 0))
palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(200, 174, 64))
palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 0, 0))
palette.setColor(QtGui.QPalette.Link, QtGui.QColor(200, 174, 64))
palette.setColor(QtGui.QPalette.LinkVisited, QtGui.QColor(200, 174, 64))
palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(25, 25, 25))
palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 220))
palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(0, 0, 0))
palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor(255, 255, 255, 127))
app.setPalette(palette)
mainWindow = MainWindow()
sys.exit(app.exec())