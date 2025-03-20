import socket, threading, sys, json  # CORRECT
from functools import reduce

from mysql.connector import cursor

from client import db

playerlist = {}
gamebox = {}

serversocket = socket.socket()
hostname = ""
port = 7064

log = open("log.txt", "a")

try:
    serversocket.bind((hostname, port))
except Exception as e:
    print(e)
    print("server could not start")
    sys.exit(1)

print(" server running..."

      '''
          ((desctiptor,name),(desctiptor,name),(desctiptor,name),(desctiptor,name),(desctiptor,name))
      
      ''')


class Player:

    def __init__(self, socketDesc, name):
        self.name = name
        self.socketDesc = socketDesc
        self.isBusy = False
    # end player


class Game:
    def __init__(self, player1, player2):  # player objects
        self.player1 = player1
        self.player2 = player2
        self.shipsPlayer1 = []
        self.shipsPlayer2 = []
        self.attackedBlocksPlayer1 = []
        self.attackedBlocksPlayer2 = []

    def checkResult(self):
        # print reduce(lambda x,y : x+y, self.shipsPlayer1)
        # print self.attackedBlocksPlayer1
        # print "====="
        if len(reduce(lambda x, y: x + y, self.shipsPlayer1)) == len(self.attackedBlocksPlayer1):
            return self.player2, self.player1
        if len(reduce(lambda x, y: x + y, self.shipsPlayer2)) == len(self.attackedBlocksPlayer2):
            return self.player1, self.player2

        return None, None

    def attack(self, attacker, block):
        themap = None
        theattackedmap = None
        if attacker == self.player1:
            themap = self.shipsPlayer2
            theattackedmap = self.attackedBlocksPlayer2
        else:
            themap = self.shipsPlayer1
            theattackedmap = self.attackedBlocksPlayer1

        if block in reduce(lambda x, y: x + y, themap):
            if block not in theattackedmap:
                theattackedmap.append(block)
            else:
                log.write(" In attack function - block is already attacked once.! ")

        '''
        victim -> which player will get affected by the attack. (Opponent of the player which had turn)
               -> Player object
        block -> tupple of the cordinates of the attack (x,y)
        Drop bomb on block of victim's board
        Update board if block is part of ship
        Return True if attack successful and False otherwise
        '''

    def setBoats(self, player, boatCoords):
        '''
        player : object
        boatCoords : [[(x,y),(x,y),(x,y), ...],[(x,y),(x,y),(x,y), ...]]
        '''
        if player == self.player1:
            self.shipsPlayer1 = boatCoords
        else:
            self.shipsPlayer2 = boatCoords

    # end game


# end Game

def startNewGame(player1, player2):
    game = Game(player1, player2)
    return game


def sendMsg(msg, toclient):
    toclient.socketDesc.send(msg.encode())  # ✅ CORRECT (convert string to bytes)
    # end sendmsg


def sendlist():
    onlineplayers = []
    for each in playerlist:
        if not playerlist[each].isBusy:
            onlineplayers.append(each)

    # print onlineplayers
    brodmsg = {"type": "playerlist", "data": onlineplayers}
    brodmsg = json.dumps(brodmsg)

    for each in playerlist:
        if not playerlist[each].isBusy:
            sendMsg(brodmsg, playerlist[each])


def cpu(player, msgtype, msgdata):
    global gamebox, playerlist

    if msgtype == "register":
        """
        "Register":
        -register the client to the server
        ->data: {
                    "name": <name of the client>
                }
        """
        name = msgdata
        return registerClient(player, name)

    elif msgtype == "sendChallenge":
        '''
        expected message format : data :  {
                                            'to' : name
                                            }
        '''
        frm = player.name  # name
        to = playerlist[msgdata['to']]  # an object

        # message the opponent about the incoming challenge
        dictData = {
            "type": "sendChallenge",
            "data": {
                "from": frm  # name
            }
        }
        jsonData = json.dumps(dictData)
        sendMsg(jsonData, to)

    elif msgtype == "acceptChallenge":
        '''
        expected message format : data : {
                                        'player1' : name,
                                        'player2' : name  
                                    }
        '''
        data = msgdata
        player1 = playerlist[data['player1']]  # objeect
        player2 = playerlist[data['player2']]  # object

        player1.isBusy = True
        player2.isBusy = True

        sendlist()

        # register new game
        game = startNewGame(player1, player2)
        gamebox[player1] = game
        gamebox[player2] = game

        # message the players to begin the game
        dictData = {
            'type': 'startGame',
            'data': {

            }
        }
        jsonData = json.dumps(dictData)
        sendMsg(jsonData, player1)
        sendMsg(jsonData, player2)

    elif msgtype == "declineChallenge":
        '''
        expected message format : data : {
                                        'challenger' : name 
                                    }
        '''
        data = msgdata
        challenger = playerlist[data['challenger']]

        # message the challenger if his challenge is declined
        dictData = {
            'type': 'challengeDeclined',
            'data': {}
        }
        jsonData = json.dumps(dictData)
        sendMsg(jsonData, challenger)

    elif msgtype == 'iAmOut':
        '''
        expected message format : data : {

                                            }
        '''

        print(" got i am out from " + player.name)
        player.socketDesc.close()

        if player.name in playerlist:
            del playerlist[player.name]

    elif msgtype == "saveMatch":
        cursor.execute(
            "INSERT INTO matches (player1, player2, winner) VALUES (%s, %s, %s)",
            (msgdata["player1"], msgdata["player2"], msgdata["winner"])
        )
        db.commit()
        print(f"Match saved: {msgdata['player1']} vs {msgdata['player2']}, Winner: {msgdata['winner']}")

        sendlist()

        # send message on both sides to abort the game and return to initial stage


    elif msgtype == "abortGame":

        oppmsg = {"type": "oppIsOut", "data": None}
        oppmsg = json.dumps(oppmsg)

        if player in gamebox:
            game = gamebox[player]

            game.player2.isBusy = False
            game.player1.isBusy = False

            if player == game.player1:
                sendMsg(oppmsg, game.player2)
            else:
                sendMsg(oppmsg, game.player1)

        sendlist()


    elif msgtype == "setBoats":  # arranging done, now register my boat positions
        '''
        Message type : data : {
                            coords : [[],[]]
                        }
        '''
        data = msgdata
        boatcoords = data["coords"]

        game = gamebox[player]
        game.setBoats(player, boatcoords)

        if len(game.shipsPlayer1) != 0 and len(game.shipsPlayer2) != 0:  # both have set their ships
            # send begin battle message
            dictData = {
                'type': 'beginBattle',
                'data': {
                    'shipData': {
                        game.player1.name: game.shipsPlayer1,
                        game.player2.name: game.shipsPlayer2,
                    },
                    'turn': game.player1.name
                }
            }
            jsonData = json.dumps(dictData)

            sendMsg(jsonData, game.player1)
            sendMsg(jsonData, game.player2)

    elif msgtype == "attack":
        """
        "msgtype":"attack":
            a player will attack on the perticular cordinates (x,y).

        "msgdata:":{"coordinates":(x,y)}

        """
        game = gamebox[player]
        game.attack(player, msgdata["coordinates"])

        winner, loser = game.checkResult()
        if winner != None and loser != None:
            print("sending verdict")

            msgcontainerforwinner = {"type": "verdict", "data": {"result": "win"}}
            msgcontainerforloser = {"type": "verdict", "data": {"result": "loose"}}

            msgforwinner = json.dumps(msgcontainerforwinner)
            msgforloser = json.dumps(msgcontainerforloser)

            # winner.socketDesc.send(msgforwinner)
            # loser.socketDesc.send(msgforloser)

            sendMsg(msgforwinner, winner)
            sendMsg(msgforloser, loser)

        else:  # send coordinates to client as well
            dictData = {
                'type': 'updateAttackCoords',
                'data': {
                    'coordinates': msgdata['coordinates']
                }
            }
            jsonData = json.dumps(dictData)

            game = gamebox[player]
            if player == game.player1:
                sendMsg(jsonData, game.player2)

            if player == game.player2:
                sendMsg(jsonData, game.player1)
    else:
        print("Unhandled MsgType..!!!")

    # end cpu


def registerClient(client, name):
    """
        -will make a new object of the Player class and will append to the playerList.
        -to maintain the list of the online players.
    """

    player = Player(client, name)
    playerlist[name] = player

    msgdata = {"type": "playerlist", "data": list(playerlist.keys())}  # ✅ CORRECT
    msg = json.dumps(msgdata)

    for key in playerlist:
        # print "sending to " + str(key)
        sendMsg(msg, playerlist[key])

    # print "new player added :) hello "
    # print  playerlist

    return player


def handleClient(client):
    """
    -will receive the message from the client and will send it to the cpu for parsing and further process
    -msg is received as a json. so message parsing is mendetory

    Message Structure::

    {"type":<type> , "data" : <data for particular type of message>}


    """
    while True:

        if isinstance(client, Player):
            try:
                data = client.socketDesc.recv(2048)
            except:
                print(" someone closed the connection")
                return
            if data == "":
                client.socketDesc.close()
                return
        else:
            data = client.recv(2048)
            if data == "":
                client.close()
                return

        # data = data.data().decode('utf-8')
        if not data:
            continue
        if not data:
            print(f"Client {client} sent empty data. Closing connection.")
            client.close()
            return  # Stop execution if no data received

        try:
            message = json.loads(data.decode("utf-8").strip())  # ✅ Safely decode
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}, received data: {data}")  # Debugging
            client.close()
            return

        msgtype = message["type"]
        msgdata = message["data"]

        if isinstance(client, Player):
            cpu(client, msgtype, msgdata)
        else:

            if msgtype != "register":
                log.write("unregistered client is trying to send unvalid messages : " + msgtype)
                sys.exit(1)

            client = cpu(client, msgtype, msgdata)

    # end handleClient


serversocket.listen(5)

"""
Receiver:
    -it will wait for the new connections.when a new connection is made it will start listening to the particular client

"""

while True:
    client, address = serversocket.accept()
    threading.Thread(target=handleClient, args=(client,)).start()

    # end reciever

# close the log file
log.close()
