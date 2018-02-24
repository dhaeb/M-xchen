import socket
import sys
import random
from threading import Lock
from threading import current_thread
import thread

class Maexchen:

    def wuerfel(self):
        return random.randint(1,6)

    def eval_maexchen(self, x, y):
        if x == y:
            return ("pasch", int(str(x) + str(y)))
        elif x == 2 and y == 1 or x == 1 and y == 2:
            return ("maexchen", 21)
        else:
            if x > y:
                z = int(str(x) + str(y))
                return ("normal", z)
            else:
                z = int(str(y) + str(x))
                return ("normal", z)

    def is_lower_or_equal(self, maex1, maex2):
        if maex2[0] == "pasch" and maex1[0] == "normal":
            return True
        elif maex2[0] == maex1[0]:
            return maex2[1] > maex1[1]
        else:
            return  maex1 == maex2

    def maex_to_string(self, maex):
        return str(maex[1])

    def get_max(self):
        return self.eval_maexchen(self.wuerfel(), self.wuerfel())

    def __init__(self):
        thread.start_new_thread(self.register_thread, ())
        self.start_server()
        self.reset_vars()

    def start_server(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the port
        # 192.168.102.94
        server_address = ('0.0.0.0', 10000)
        self.sock.bind(server_address)
        # Listen for incoming connections
        self.sock.listen(1)
        self.spieler = {}
        self.spieler_liste = []

    def reset_vars(self):
        self.game_is_on = False
        self.wuerfler = ""
        self.aktuell_am_zug = ""
        self.aktuell_gewuerfelt = tuple()
        self.aktuell_bekannt = ("normal", 31)
        self.nachfolger = ""


    def get_random_index(self, len_of_array, filtered_indexes):
        indexes = list(range(0, len_of_array))
        l = list(filter(lambda i: i not in filtered_indexes, indexes))
        upper = len(l) - 1
        return l [random.randint(0,upper)]

    def broadcast(self, message):
        for s in self.spieler:
            c = self.spieler[s]
            c.sendall(message)

    def wuerfeln_zug(self, name, connection, nachfolger):
        self.broadcast("Ein Spiel beginnt!\n")
        self.game_is_on = True
        self.aktuell_gewuerfelt = self.get_max()
        if self.aktuell_gewuerfelt[0] == "maexchen":
            self.reset_vars()
            self.broadcast("{0} hat ein Maexchen! Die Runde ist beendet! \n".format(name))
        else:
            self.aktuell_am_zug = name
            self.wuerfler = name
            self.nachfolger = nachfolger
            self.broadcast("{0} spielt mit {1}, es wird gewuerfelt...\n".format(name, nachfolger))
            connection.sendall("Du hast eine: " + self.maex_to_string(self.aktuell_gewuerfelt) + "\n")
            connection.sendall("Bitte mit --aufnahme:XX Deine Zahlen an den Gegner schicken...\n")

    def socket_handler(self, connection, client_address):
        name = "Unbekannt..."
        while True:
            data = connection.recv(1024).rstrip()
            print("LOG: " + data)
            lock = Lock()
            lock.acquire() # will block if lock is already held
            if data.startswith("--name:"):
                name = data.split(":")[1]
                self.spieler[name] = connection
                self.spieler_liste.append(name)
                connection.sendall("Name erfolgreich gesetzt!\n")
                self.broadcast("Neuer Spieler: " + name + " eingeloggt!\n")
            elif data == "--start"  and not self.game_is_on and len(self.spieler_liste) > 1:
                i = self.spieler_liste.index(name)
                ri = self.get_random_index(len(self.spieler_liste), [i])
                nachfolger = self.spieler_liste[ri]
                self.wuerfeln_zug(name, connection, nachfolger)
            elif data == "--status":
                connection.sendall("Spiel laeuft aktuell {}\n".format(self.game_is_on))
                if self.game_is_on:
                    connection.sendall("Die hoechste wuerfelzahl aktuell liegt bei: {}\n".format(self.maex_to_string(self.aktuell_bekannt)))
                    connection.sendall("An der Reihe ist aktuell: {}\n".format(self.aktuell_am_zug))
                else:
                    pass
            elif data.startswith("--aufnahme:") and self.aktuell_am_zug == name and self.wuerfler == name:
                s = data.split(":")
                max_as_string = s[1]
                try:
                    m = self.eval_maexchen(int(max_as_string[0]),int(max_as_string[1]))
                    if self.is_lower_or_equal(m, self.aktuell_bekannt):
                        connection.sendall("Deine Angabe ergibt keinen Sinn! ")
                    else:
                        self.aktuell_bekannt = m
                        self.broadcast("{0} meint, folgendes gewuerfelt zu haben: {1}\n".format(name, self.maex_to_string(m)))
                        c_nachfolger = self.spieler[self.nachfolger]
                        c_nachfolger.sendall("Glaubst du das?\n")
                        c_nachfolger.sendall("Bestaetige bitte mit --wahr bzw. --falsch\n")
                        self.aktuell_am_zug = self.nachfolger
                except:
                    connection.sendall("Deine Angabe ergibt keinen Sinn! ")

            elif data == "--wahr" and self.aktuell_am_zug == name and self.nachfolger == name:
                ri = self.get_random_index(len(self.spieler_liste), [self.spieler_liste.index(name)])
                neuer_nachfolger = self.spieler_liste[ri]
                self.broadcast("{1} glaubt {0}, dass Spiel geht weiter! {1} wuerfelt jetzt und {2} ist danach an der Reihe!\n".format(name, self.wuerfler, neuer_nachfolger))
                self.wuerfeln_zug(name, connection, neuer_nachfolger)
            elif data == "--falsch" and self.aktuell_am_zug == name and self.nachfolger == name:
                if self.aktuell_bekannt == self.aktuell_gewuerfelt:
                    self.broadcast("{0} hat nicht gelogen! {0} gewinnt!\n".format(self.wuerfler))
                    self.reset_vars()
                else:
                    self.broadcast("{0} hat nicht die Wahrheit gesagt!\n".format(self.wuerfler))
                    self.reset_vars()
                pass

            lock.release()

    def register_thread(self):
        while True:
            # Wait for a connection
            print >>sys.stderr, 'waiting for a connection'
            connection, client_address = self.sock.accept()
            print('Connected by ', client_address)
            thread.start_new_thread(self.socket_handler, (connection, client_address))

    def __del__(self):
        self.broadcast("Server faehrt herunter...")
        for s in self.spieler:
            c = self.spieler[s]
            c.close()
        self.sock.close()

game = Maexchen()
raw_input("Druecken Sie eine beliebige Taste zum Beenden des Programms....")
del game
