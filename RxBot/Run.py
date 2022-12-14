from threading import Thread
from Initialize import *
initSetup()
from Resources import *


def main():
    print("Starting... Please go to PlayersRevenge in your browser")

    time.sleep(5)
    resetStartAgain()
    while True:
        try:
            startRequest()

        except IndexError:
            print("Reached end of screen, refreshing!")
            resetStartAgain()

        except Exception as e:
            print("Error detected - Trying again.")
            print(e)
            resetStartAgain()


def tick():
    prevTime = datetime.datetime.now()
    while True:
        time.sleep(0.4)

        if misc.timerActive:
            for timer in misc.timers:
                if datetime.datetime.now() > misc.timers[timer]:
                    misc.timerDone(timer)
                    break

        # Timers that send stuff every X seconds

        # if datetime.datetime.now() > prevTime + datetime.timedelta(minutes=settings["TIMER DELAY"]):
        #     chatConnection.sendToChat(resources.askChatAQuestion())
        #     prevTime = datetime.datetime.now()


if __name__ == "__main__":
    t1 = Thread(target=main)
    t2 = Thread(target=tick)

    t1.start()
    t2.start()