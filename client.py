from PyQt5 import QtCore, QtNetwork, QtMultimedia, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QListWidget, QPushButton, QMessageBox, \
    QDialog, QInputDialog
from PyQt5.QtMultimedia import QSoundEffect
import socket, sys, threading, json, mysql.connector
import os
from PyQt5.QtCore import QUrl

ships = None
name = None


# MySQL Connection Setup
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="R$E#W@Q!",
    database="BattleShip"
)
cursor = db.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS matches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player1 VARCHAR(255),
    player2 VARCHAR(255),
    winner VARCHAR(255)
)
''')
db.commit()

def getMyShips(name):
    '''
    Return the ship list of the requester
    '''
    global ships
    return ships[name]


def getOpponentShips(name):
    '''
    Return the ship list of opponent of the requester
    '''
    global ships
    for player in ships:
        if player != name:
            return ships[player]


class battle(QWidget):
    '''
    The main gameplay Widget
    '''

    def __init__(self):
        super(battle, self).__init__()
        self.initUI()
        self.setMouseTracking(True)
        self.customInit()

        print("init sounds")

        base_path = os.path.abspath(os.path.dirname(__file__))  # Gets the current script folder
        hit_path = os.path.join(base_path, "soundfile", "hit.wav")
        miss_path = os.path.join(base_path, "soundfile", "miss.wav")

        self.soundhit = QSoundEffect()
        self.soundhit.setSource(QtCore.QUrl.fromLocalFile(hit_path))
        self.soundhit.setVolume(0.5)

        self.soundmiss = QSoundEffect()
        self.soundmiss.setSource(QtCore.QUrl.fromLocalFile(miss_path))
        self.soundmiss.setVolume(0.5)
        # QSound doesn't have is_playing method, so we'll use a simple flag system
        self.hit_playing = False
        self.miss_playing = False
        print("sound initialized")

    def customInit(self):
        '''
        To initialize the data that are dependent on
        components not loading before the __init__ is called
        '''
        self.myAttackedBlocks = []
        self.opponentAttackedBlocks = []
        self.turn = False
        self.mouseOn = [9999, 9999]

    def resetMouseOn(self):
        self.mouseOn = [9999, 9999]

    def setMouseOn(self, x, y):
        self.mouseOn = [x, y]

    def myInit(self):
        '''

        '''
        global name
        self.myShips = getMyShips(name)
        self.opponentShips = getOpponentShips(name)

    def initTurn(self):
        '''
        Initialize the turn variable
        '''
        self.turn = True

    def initUI(self):
        '''
        Set default dimensions and title for the window
        '''
        self.setGeometry(50, 50, 1050, 500)
        self.setWindowTitle('Battle captains ..!')
        self.show()

    def paintEvent(self, e):
        '''
        Update the board drawings
        '''
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawBoards(qp)
        qp.end()

        # No need to check if sound is playing with QSound

    def drawBoards(self, qp):
        '''
        handles the drawing part

        Input : painter object
        Output : Updatation of the canvas
        '''
        pen = QtGui.QPen(QtCore.Qt.white, 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)

        # if opponent's turn I fade to white
        fade = 140
        try:
            if not self.turn:
                fade = 255
            else:
                fade = 140
        except:
            print("")

        # draw my board
        for x in range(10):
            for y in range(10):
                qp.setBrush(QtGui.QColor(150, 170, 255, fade))
                pen = QtGui.QPen(QtCore.Qt.white, 2, QtCore.Qt.SolidLine)
                qp.setPen(pen)

                # draw the attacked blocks in red
                flag = True
                if [x, y] in self.myAttackedBlocks:
                    qp.setBrush(QtGui.QColor(255, 100, 100, fade))
                    flag = False

                if flag:
                    for ship in self.myShips:
                        if [x, y] in ship:
                            pen = QtGui.QPen(QtGui.QColor(0, 0, 0), 2, QtCore.Qt.SolidLine)
                            qp.setPen(pen)
                            qp.setBrush(QtGui.QColor(255, 255, 255, fade))
                            break

                qp.drawRect(x * 50, y * 50, 50, 50)

                # draw the ship blocks in white. Keep border black
                pen = QtGui.QPen(QtGui.QColor(0, 0, 0), 2, QtCore.Qt.SolidLine)
                qp.setPen(pen)
                qp.setBrush(QtGui.QColor(255, 255, 255, fade))
                for ship in self.myShips:
                    for coord in ship:
                        qp.drawRect(coord[0] * 50, coord[1] * 50, 50, 50)

                for coord in self.myAttackedBlocks:
                    qp.setBrush(QtGui.QColor(255, 100, 100, fade))
                    qp.drawRect(coord[0] * 50, coord[1] * 50, 50, 50)

                    # keep the part of the current turn holder normal
        # and other's faded
        fade = 255
        try:
            if self.turn:
                fade = 255
            else:
                fade = 140
        except:
            print("")

        # draw opponent board
        pen = QtGui.QPen(QtCore.Qt.white, 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)

        for x in range(10):
            for y in range(10):
                qp.setBrush(QtGui.QColor(150, 170, 255, fade))

                # change the color of block on which
                # the mouse pointer is
                if [x + 11, y] == self.mouseOn and self.turn:
                    qp.setBrush(QtGui.QColor(255, 69, 0, 140))
                if [x, y] in self.opponentAttackedBlocks:
                    qp.setBrush(QtGui.QColor(255, 100, 100, fade))
                qp.drawRect((x + 11) * 50, y * 50, 50, 50)

        # print whose turn is it currently
        if not self.turn:
            opponentsString = "OPPONENT'S"
            turnString = "TURN"
            pen = QtGui.QPen(QtCore.Qt.white, 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.setBrush(QtGui.QColor(255, 0, 0))
            for x in range(len(opponentsString)):
                qp.drawText((x + 11) * 50 + 25, 4 * 50 - 25, opponentsString[x])
            for x in range(len(turnString)):
                qp.drawText((x + 11) * 50 + 25, 5 * 50 - 25, turnString[x])

        else:
            turnString = "YOUR TURN"
            pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.setBrush(QtGui.QColor(255, 0, 0))
            for x in range(len(turnString)):
                qp.drawText((x) * 50 + 25, 4 * 50 - 25, turnString[x])

    def mousePressEvent(self, event):
        """
        Todo's when player clicks
        """
        button = event.button()
        x = event.x() // 50
        y = event.y() // 50

        qp1 = QtGui.QPainter()
        qp1.begin(self)
        qp1.setBrush(QtGui.QColor(255, 100, 100))
        qp1.drawRect((x) * 50, y * 50, 50, 50)
        qp1.end()

        # if player has turn
        # consider click as an attack
        x = x - 11
        if self.turn:
            if x in range(10) and y in range(10):
                self.attackOnOpponent([x, y])

                # send message of attack to server
                dictData = {
                    'type': 'attack',
                    'data': {
                        'coordinates': (x, y)
                    }
                }
                jsonData = json.dumps(dictData)
                mysocket.send(jsonData.encode())  # encode to bytes

    def mouseMoveEvent(self, event):
        '''
        Handle todo's with the current mouse position
        '''
        x = event.x() // 50
        y = event.y() // 50
        self.setMouseOn(x, y)
        self.update()

    def attackOnMe(self, coords):
        '''
        Event when the client is attacked
        '''
        print("i am attacked")
        for ship in self.myShips:
            if coords in ship:
                self.myAttackedBlocks.append(coords)
                self.soundhit.play()
            else:
                self.soundmiss.play()

        self.turn = True
        self.update()

    def attackOnOpponent(self, coords):
        '''
        Event when client's opponent is attacked
        '''
        for ship in self.opponentShips:
            if coords in ship:
                self.opponentAttackedBlocks.append(coords)
                self.soundhit.play()
            else:
                self.soundmiss.play()

        self.turn = False
        self.update()

    def get(self):
        return self.myShips


class setBoats(QtWidgets.QWidget):
    '''
    The widget where player arranges his ships
    '''

    def __init__(self):
        super(setBoats, self).__init__()
        self.initUI()
        self.setMouseTracking(True)
        self.myInit()

    def myInit(self):
        '''
        Handle initialization of dependent attributes
        '''
        self.boats = [5, 4, 3, 2]
        self.currentBoat = 0
        self.selectedBlocks = []
        self.selectedBoats = []
        self.orientation = 0  # 0->horizontal and 1->vertical

        self.brownBoxes = []
        self.clickable = True
        self.update()

    def initUI(self):
        self.setGeometry(50, 50, 500, 500)
        self.setWindowTitle('Pen styles')
        self.show()

    def paintEvent(self, e):
        '''
        The painter
        '''
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLines(qp)
        qp.end()

    def drawLines(self, qp):
        '''
        Handle drawing of blocks on board
        '''
        pen = QtGui.QPen(QtCore.Qt.white, 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)

        # draw 10x10 grid
        for x in range(10):
            for y in range(10):
                # if a block isn't part of arranged ship keep it blue
                # and white otherwise
                if (x, y) not in self.brownBoxes and (x, y) not in self.selectedBlocks:
                    qp.setBrush(QtGui.QColor(150, 170, 255))
                    qp.drawRect(x * 50, y * 50, 50, 50)
                else:
                    qp.setBrush(QtGui.QColor(255, 255, 255))
                    qp.drawRect(x * 50, y * 50, 50, 50)

        # type sensile messages to keep player informed
        pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        font = qp.font()
        font.setPointSize(15)
        qp.setFont(font)

        if len(self.boats[self.currentBoat:]) > 1:
            ship_sizes = [str(size) for size in self.boats[self.currentBoat:]]
            setShipText = "Size of ships you have: " + ", ".join(ship_sizes)
        elif len(self.boats[self.currentBoat:]) == 1:
            setShipText = "Size of ships you have: " + str(self.boats[self.currentBoat:][0])
        else:  # when player puts all his ships before his opponent, he waits
            setShipText = "Waiting for opponent while he prepares for battle"

        qp.drawText(10, 11 * 50, setShipText)

    def updateBoxes(self, headBoxX, headBoxY):
        '''
        Maintain the state of boats
        '''
        self.clickable = True
        self.brownBoxes = []
        for i in range(self.boats[self.currentBoat]):
            if self.orientation == 0:
                if headBoxX + i > 9 or (headBoxX + i, headBoxY) in self.selectedBlocks:
                    self.clickable = False
                self.brownBoxes.append((headBoxX + i, headBoxY))
            if self.orientation == 1:
                if headBoxY + i > 9 or (headBoxX, headBoxY + i) in self.selectedBlocks:
                    self.clickable = False
                self.brownBoxes.append((headBoxX, headBoxY + i))

        self.update()

    def mousePressEvent(self, event):
        """
        mouse clicks events
        """
        button = event.button()

        # if it's a right click, change orientation of boats
        if button == QtCore.Qt.RightButton:  # Changed from 2 to Qt.RightButton
            if self.orientation == 0:
                self.orientation = 1
            else:
                self.orientation = 0
            self.update()
            return

        if self.clickable:  # when user leftclicks
            self.selectedBoats.append(self.brownBoxes)
            self.selectedBlocks += self.brownBoxes
            self.currentBoat += 1

        # when user clicks, tell server he set a boat
        if self.currentBoat == len(self.boats):
            dictData = {
                'type': 'setBoats',
                'data': {
                    'coords': self.selectedBoats
                }
            }

            jsonData = json.dumps(dictData)
            mysocket.send(jsonData.encode())  # encode to bytes

    def mouseMoveEvent(self, event):
        '''
        Move ships along with mouse
        '''
        if len(self.boats) == self.currentBoat:
            return
        self.clickable = True
        headX = event.x()
        headY = event.y()
        headBoxX = headX // 50
        headBoxY = headY // 50
        self.updateBoxes(headBoxX, headBoxY)


class WinLoseMsg(QtWidgets.QDialog):
    '''
    MessageBox for Win or Lose Message
    '''

    def __init__(self, iswin, game, parent=None):
        super(WinLoseMsg, self).__init__(parent)

        self.game = game
        msgBox = QtWidgets.QMessageBox()

        # Determine winner and loser
        player1 = self.game.selectplayerwidget.parent.playerlistwidget.item(0).text()
        player2 = self.game.selectplayerwidget.parent.playerlistwidget.item(1).text()
        winner = player1 if iswin else player2

        # Send match result to server
        match_result = {
            "type": "saveMatch",
            "data": {
                "player1": player1,
                "player2": player2,
                "winner": winner
            }
        }
        jsonData = json.dumps(match_result)
        mysocket.send(jsonData.encode())  # Send result to the server

        # Show message box
        if iswin:
            msgBox.setText('         You win')
        else:
            msgBox.setText('         You lose')

        anotherplayerbutton = QtWidgets.QPushButton('  Play with another player ')
        anotherplayerbutton.clicked.connect(self.anotherplayerclicked)

        msgBox.addButton(anotherplayerbutton, QtWidgets.QMessageBox.YesRole)
        msgBox.exec_()

    def anotherplayerclicked(self):
        '''
        Close the messagebox when another player accept the challenge
        '''
        self.game.hide()
        self.game.selectplayerwidget.show()

class SelectPlayerWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(SelectPlayerWidget, self).__init__()

        self.parent = parent
        self.VBox = QtWidgets.QVBoxLayout()  # Changed from QtGui.QVBoxLayout
        parent.playerlistwidget = QtWidgets.QListWidget()  # Changed from QtGui.QListWidget
        self.ChallangeButton = QtWidgets.QPushButton("Challange")  # Changed from QtGui.QPushButton

        # Updated signal/slot connection
        self.ChallangeButton.clicked.connect(parent.sendChallenge)

        self.VBox.addWidget(parent.playerlistwidget)
        self.VBox.addWidget(self.ChallangeButton)
        self.setLayout(self.VBox)
        self.setWindowTitle("Player List")

    def closeEvent(self, event):
        # do stuff
        global mysocket

        print(" < I am Out >")
        msg = {"type": "iAmOut", "data": None}
        msg = json.dumps(msg)

        mysocket.send(msg.encode())  # encode to bytes

        event.accept()  # let the window close


class Game(QMainWindow):
    def __init__(self, master=None):
        super().__init__()
        self.setWindowTitle("BattleShip")

        self.createUI()

        self.hide()
        self.enterName()

        base_path = os.path.abspath(os.path.dirname(__file__))  # Gets the current script folder
        start_path = os.path.join(base_path, "soundfile", "start.wav")

        self.startsound = QSoundEffect()
        self.startsound.setSource(QtCore.QUrl.fromLocalFile(start_path))
        self.startsound.setVolume(0.5)

        self.selectplayerwidget.show()

    def createUI(self):
        self.widget = QtWidgets.QWidget(self)  # Changed from QtGui.QWidget
        self.container = QtWidgets.QVBoxLayout()  # Changed from QtGui.QVBoxLayout
        self.setCentralWidget(self.widget)

        self.selectplayerwidget = SelectPlayerWidget(self)
        self.selectBoatWidget = setBoats()
        self.selectBoatWidget.hide()
        self.battlewidget = battle()
        self.battlewidget.hide()

        self.container.addWidget(self.selectBoatWidget)
        self.container.addWidget(self.battlewidget)
        self.widget.setLayout(self.container)

    def closeEvent(self, event):
        global mysocket
        print(" < aborting game >")
        msg = {"type": "abortGame", "data": None}
        msg = json.dumps(msg)

        mysocket.send(msg.encode())  # encode to bytes

        self.selectplayerwidget.show()
        self.hide()

        event.ignore()  # let the window close

    def enterName(self):
        '''
        Input Dialog for the name
        '''
        global name

        name, ok = QtWidgets.QInputDialog.getText(self, 'name', 'Enter your name:')  # Changed from QtGui.QInputDialog
        name = str(name)
        if not ok:
            self.close()
            sys.exit(1)
        else:
            self.sendName()

    def sendName(self):
        '''
        Send the name when user enters the name and press button
        '''
        global name
        msg = {"type": "register", "data": name}
        msg = json.dumps(msg)

        mysocket.send(msg.encode())  # encode to bytes

    def sendChallenge(self):
        '''
        send challenge message when user select the user and press button
        '''

        if self.playerlistwidget.currentItem() and self.playerlistwidget.currentItem().isSelected():
            toname = self.playerlistwidget.currentItem().text()
            msg = {"type": "sendChallenge", "data": {"to": str(toname)}}
            msg = json.dumps(msg)
            mysocket.send(msg.encode())  # encode to bytes

            print("challange request sending to server")

            class customMsg(QtWidgets.QDialog):  # Changed from QtGui.QDialog
                def __init__(self, parent=None):
                    super(customMsg, self).__init__(parent)
                    self.msgBox = QtWidgets.QMessageBox()  # Changed from QtGui.QMessageBox
                    self.msgBox.setText('waiting for opponent...')
                    self.msgBox.addButton(QtWidgets.QMessageBox.NoButton)  # Changed from QtGui.QMessageBox.NoButton

            self.waitbox = customMsg()
            self.waitbox.msgBox.open()

            print("before wait")
            print("after wait")

        else:
            msg = QtWidgets.QMessageBox()  # Changed from QtGui.QMessageBox
            msg.setText("please select an online player")
            msg.show()
            msg.exec_()

    def gotChallenge(self, mysocket, playername):
        result = QtWidgets.QMessageBox.question(self, 'challenge',
                                                playername + " challenged you \n\n accept challange ?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.Yes)  # Changed QtGui to QtWidgets
        if result == QtWidgets.QMessageBox.Yes:  # Changed from QtGui.QMessageBox.Yes
            msg = {"type": "acceptChallenge", "data": {"player1": playername, "player2": name}}
            msg = json.dumps(msg)
            mysocket.send(msg.encode())  # encode to bytes
            print(" challange accepted :D")
        else:
            msg = {"type": "declineChallenge", "data": {"challenger": playername}}
            msg = json.dumps(msg)
            mysocket.send(msg.encode())  # encode to bytes

    def cpu(self, msg):
        try:
            global mysocket
        except:
            print("mysocket is not gloabal lol  ")

        # PyQt5 directly passes strings, no need to convert QString
        msg = json.loads(msg)
        msgtype = msg["type"]
        msgdata = msg["data"]

        global ships
        if msgtype == "playerlist":
            '''
            got new player list, update the listWidget
            '''
            print("got player list")
            self.playerlist = msgdata
            self.playerlistwidget.clear()

            for each in self.playerlist:
                if each != name:
                    self.playerlistwidget.addItem(each)

        elif msgtype == "sendChallenge":
            '''
            got a challenge from the player
            '''
            print("got challange from " + msgdata["from"])
            self.gotChallenge(mysocket, msgdata["from"])

        elif msgtype == "startGame":
            '''
            when challenge is accepted start the game window and start widget to get the ships
            '''
            if hasattr(self, 'waitbox'):
                self.waitbox.msgBox.accept()
            else:
                "no waitbox in self"

            self.startsound.play()
            self.selectplayerwidget.hide()
            self.battlewidget.hide()
            self.show()
            self.selectplayerwidget.repaint()
            self.selectBoatWidget.myInit()
            self.selectBoatWidget.show()

        elif msgtype == "beginBattle":
            '''
            ship is set of both players, now start the game
            '''
            # No need to stop QSound as it stops automatically
            ships = msgdata['shipData']

            self.selectBoatWidget.hide()
            self.battlewidget.customInit()
            self.battlewidget.myInit()
            self.battlewidget.repaint()

            if name == msgdata['turn']:
                self.battlewidget.initTurn()

            self.battlewidget.show()

        elif msgtype == "oppIsOut":
            '''
            opponent is out when user was playing a game
            '''
            print("opponent is out")
            self.selectBoatWidget.hide()
            self.battlewidget.hide()
            self.hide()
            self.selectplayerwidget.show()

        elif msgtype == "verdict":
            winflag = False
            if msgdata["result"] == "win":
                winflag = True

            result = WinLoseMsg(winflag, self)
            result.open()

        elif msgtype == "updateAttackCoords":
            coords = msgdata['coordinates']
            self.battlewidget.attackOnMe([coords[0], coords[1]])

        elif msgtype == "challengeDeclined":
            if hasattr(self, 'waitbox'):
                self.waitbox.msgBox.setText("Challenge Rejected..")

        else:
            print("unhandled msgtype :" + msgtype)


# PyQt5 signals changed to use the new style
class ListenerThread(QtCore.QThread):
    # Define a new signal
    gamecpu = QtCore.pyqtSignal(str)

    def __init__(self, mysocket, game):
        QtCore.QThread.__init__(self)
        self.mysocket = mysocket
        self.game = game

    def listener(self, mysocket, game):
        while True:
            try:
                msg = mysocket.recv(2048).decode('utf-8')  # decode bytes to string
                if msg == "":
                    return

                self.gamecpu.emit(msg)
            except Exception as e:
                print(f"Error receiving message: {e}")
                return

    def run(self):
        self.listener(self.mysocket, self.game)


if __name__ == "__main__":
    mysocket = socket.socket()
    host = socket.gethostname()
    port = 7064

    try:
        mysocket.connect((host, port))
    except Exception as e:
        print(e)
        print("could not connect to server")
        sys.exit(1)

    print("connected")
    app = QApplication(sys.argv)
    game = Game()

    listenerthread = ListenerThread(mysocket, game)
    # Connect using new-style signals
    listenerthread.gamecpu.connect(game.cpu)
    listenerthread.start()

    game.resize(1200, 680)
    sys.exit(app.exec())