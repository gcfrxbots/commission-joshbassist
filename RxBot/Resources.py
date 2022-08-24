from Settings import *
from Initialize import *
import pyautogui
import mss
import mss.tools
from PIL import Image, ImageOps
import cv2
import numpy
import pyperclip
#pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
pyautogui.FAILSAFE = False  # Might cause nuclear apocalypse

res = settings["RESOLUTION MODIFIER"] / 100

scrollToLineUpBottomDistance = -240
scrollToMoveUpOneBarDistance = -54
timesToScrollUp = 8
portraitOffset = -40


def cvToPil(cvImg):
    cvImg = cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB)
    pilImg = Image.fromarray(cvImg)
    del cvImg
    return pilImg


def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)


class resources:
    def __init__(self):
        self.width, self.height = pyautogui.size()
        self.userText = None
        self.IdText = None
        self.buyInText = None
        self.profitText = None
        self.cachedIdImage = None
        self.handsText = None
        self.lastLeaderboardHandCounts = []
        self.currentLeaderboardHandCounts = []
        self.wipeNextScan = False
        self.oldTempCache = []

    def holdKey(self, key, duration):
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)

    def findImageOnScreen(self, imgName, confidence):
        imageLocation = pyautogui.locateOnScreen("Resources/%s" % imgName, confidence=confidence, grayscale=True)
        if not imageLocation:
            return False
        #print("Image found at " + str(imageLocation))
        return imageLocation

    def moveMouseToLocation(self, imageLocation):
        x, y = pyautogui.center(imageLocation)
        pyautogui.moveTo(x, y)

    # def imgToText(self, img):
    #     text = pytesseract.image_to_string(img, config='--psm 10 --oem 3').replace("-", "")
    #     #print("OCR TEXT: \n" + text + "\n")
    #     return text.strip()

    def screenshotRegion(self, top, left, width, height, invert, filter):
        if settings["ALTERNATIVE SCREENSHOT"]:
            with mss.mss() as sct:
                # The screen part to capture
                region = {'top': top, 'left': left, 'width': width, 'height': height}

                # Grab the data
                sctimg = sct.grab(region)
                img = Image.frombytes("RGB", sctimg.size, sctimg.bgra, "raw", "BGRX")
        else:
            img = pyautogui.screenshot(region=(left, top, width, height))
        newImg = img

        # Upscale
        if filter:
            imgSize = img.size
            img = img.resize((imgSize[0] * 2, imgSize[1] * 2), resample=Image.BOX)

            newImg = img



        if invert:
            img = ImageOps.invert(img)

        if filter == "Normal":
            img = change_contrast(img, 142)

            cvImg = numpy.array(img)
            cvImg = cvImg[:, :, ::-1].copy()

            gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
            revisedCvImg = cv2.fastNlMeansDenoising(gray, cvImg, 67.0, 7, 21)
            (thresh, blackAndWhiteImage) = cv2.threshold(revisedCvImg, (143 + settings["IMAGE OFFSET"]), 255, cv2.THRESH_BINARY)
            newImg = cvToPil(blackAndWhiteImage)

        if filter == "Hands":
            img = change_contrast(img, 142)

            cvImg = numpy.array(img)
            cvImg = cvImg[:, :, ::-1].copy()

            gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
            revisedCvImg = cv2.fastNlMeansDenoising(gray, cvImg, 67.0, 7, 21)
            (thresh, blackAndWhiteImage) = cv2.threshold(revisedCvImg, (143 + settings["HANDS OFFSET"]), 255, cv2.THRESH_BINARY)
            newImg = cvToPil(blackAndWhiteImage)

        if filter == "ID":
            img = change_contrast(img, 40)

            cvImg = numpy.array(img)
            cvImg = cvImg[:, :, ::-1].copy()

            gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
            (thresh, blackAndWhiteImage) = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
            revisedCvImg = cv2.fastNlMeansDenoising(gray, blackAndWhiteImage, 35.0, 7, 5)
            (thresh, blackAndWhiteImage) = cv2.threshold(revisedCvImg, (220 + settings["ID IMAGE OFFSET"]), 255, cv2.THRESH_BINARY)
            newImg = cvToPil(blackAndWhiteImage)

        #newImg.show()



        # thresh = 170
        # fn = lambda x: 255 if x > thresh else 0
        # img = img.convert('L').point(fn, mode='1')


        if settings["DEBUG SHOW IMAGE"]:
            newImg.show()
            print("Showed image, waiting for it to be closed or moved.")
            time.sleep(1)

        #newImg.show()
        return newImg


    def scrollDown(self):
        pyautogui.moveTo(int(resources.width / 2), int(resources.height / 2), 0.3)
        pyautogui.drag(0, int(scrollToMoveUpOneBarDistance * res), 0.8, button="left")
        time.sleep(1.8)


    def scrollUp(self):
        pyautogui.moveTo(int(resources.width / 2), int(resources.height / 2), 0.3)
        pyautogui.drag(0, 400, 0.8, button="left")
        time.sleep(1)



def resetStartAgain():
    pyautogui.scroll(1000)
    gotoTab("hitlist")
    pyautogui.click(pyautogui.center(resources.findImageOnScreen("refresh.png", 0.85)))
    time.sleep(0.5)
    print("Refreshed")


def adjustCoords(point):
    x = point[0] - 1920
    #x = point[0]
    x = x + 300
    y = point[1]
    return x, y


def gotoTab(tab):  # tab.png
    tab = tab.lower()
    location = pyautogui.locateOnScreen("Resources/%s.png" % tab, confidence=0.8)
    if location:
        resources.moveMouseToLocation(location)
        pyautogui.click()
        time.sleep(0.2)


def stringToInt(string):
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
    if string[-1].isdigit(): # check if no suffix
        return int(string)
    mult = multipliers[string[-1]] # look up suffix to get multiplier
     # convert number to float, multiply by multiplier, then make int
    return int(float(string[:-1]) * mult)


def getBounty(point):
    bountyLeftSide = [point[0] + 120, point[1]]
    bountyRightSide = [point[0] + 230, point[1]]
    pyautogui.moveTo(bountyLeftSide[0], bountyLeftSide[1])
    pyautogui.dragTo(bountyRightSide[0], bountyRightSide[1], 0.3, button='left')
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    data = pyperclip.paste().replace(",", "")
    num = stringToInt(data.replace("$", ''))
    return num

def getUsername(point):
    bountyLeftSide = [point[0] - 100, point[1]]
    bountyRightSide = [point[0] + 125, point[1]]
    pyautogui.moveTo(bountyLeftSide[0], bountyLeftSide[1])
    pyautogui.dragTo(bountyRightSide[0], bountyRightSide[1], 0.3, button='left')
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    data = pyperclip.paste()
    return data



hitlistBlacklist = []




def startRequest():
    scrollFurther = False
    killCount = 0

    # -------------------------------------------- START DATA FILTERING FROM SITE
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.3)
    data = pyperclip.paste()

    # Split data up
    playerData = {}

    data = data.split("When")[1:]
    data = "".join(data)
    for i in enumerate(data.split("minutes")):
        count = i[0]
        i = i[1]
        userInfo = i.split("\n")
        del userInfo[0]
        #print(userInfo)
        if "Lotto Listing" in userInfo[0]:
            username = userInfo[1].replace("\r", "")
            bounty = userInfo[2].split("$")[1]
            bounty = stringToInt(bounty.split("MEGA")[0].replace(",", ""))

            if bounty <= settings["MAX BOUNTY"]:
                playerData[username] = count
                print("Added target %s | $%s" % (username, str(bounty)))


    if not playerData:  # Check if lotto not active
        print("Lotto likely not active (No (Lotto Listing) text found) or no valid users available, waiting 5s then trying again...")
        time.sleep(5)
        bankCash()
        resetStartAgain()
        return
    # ----------------------------------------------- DONE FILTERING FROM SITE, START LOOP

    for player in playerData:
        buttonLocations = []
        pyautogui.scroll(1000)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.scroll(-365)
        time.sleep(0.1)
        if scrollFurther:
            pyautogui.scroll(-385)
        time.sleep(0.4)

        for position in pyautogui.locateAllOnScreen('Resources/pimpin.png', confidence=0.9, grayscale=True):  # TODO ADD A REGION
            buttonLocations.append(adjustCoords(pyautogui.center(position)))  # Fill the buttonLocations list, index 0 should be player 0. Should be done after every attack to make sure locations are correct.


        index = playerData[player] + killCount
        # print(index)
        location = buttonLocations[index]
        print(location)
        # print(playerData)
        print(buttonLocations)

        #print(location)
        print("Attacking %s, index %s" % (player, index))
        time.sleep(0.2)
        pyautogui.click(location[0], location[1])  # Click the attack button

        # Determine if lost or not by looking for the you lose
        if not resources.findImageOnScreen("loser.png", 0.9):  # Skip the "keep attacking" loop if you lose and just go to the next player

            while True:
                location = pyautogui.locateOnScreen("Resources/attackAgain.png", confidence=0.85, grayscale=True)  # TODO ADD A REGION
                if not location:
                    break
                for x in range(5):
                    pyautogui.click(pyautogui.center(location))
                    time.sleep(0.1)


            scrollFurther = True
            if lookForPopups():  # Run after the Attack Again button isn't visible anymore
                resetStartAgain()
                scrollFurther = False
                return  # If the popup manager did something (like heal or stamina), refresh the page and fully start again.

        killCount += 1


    print("End of list!")
    resetStartAgain()
    return

def lookForPopups():

    if resources.findImageOnScreen("getHealed.png", 0.85):
        gotoTab("hospital")
        time.sleep(0.2)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("heal.png", 0.85)))
        time.sleep(0.4)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("closeHeal.png", 0.85)))
        time.sleep(0.4)
        return True

    staminaLocation = resources.findImageOnScreen("staminaRefill.png", 0.85)
    if staminaLocation:
        pyautogui.click(pyautogui.center(staminaLocation))
        time.sleep(0.3)
        return True

    return checkCiao()

def checkCiao():
    ciaoLocation = resources.findImageOnScreen("ciaoExp.png", 0.85)
    if ciaoLocation:
        pyautogui.click(pyautogui.center(ciaoLocation))
        time.sleep(0.3)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("ciaoConfirm.png", 0.85)))
        time.sleep(1)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("close.png", 0.85)))
        time.sleep(0.5)
        gotoTab("hospital")  # Heal after you CIAO
        time.sleep(0.2)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("heal.png", 0.85)))
        time.sleep(0.4)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("closeHeal.png", 0.85)))
        time.sleep(0.4)
        return True
    return False

def bankCash():
    if not resources.findImageOnScreen("cash0.png", 0.95):
        print("Banking cash!")
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("cash.png", 0.95)))
        time.sleep(0.3)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("bankYes.png", 0.85)))
        time.sleep(1)
        pyautogui.click(pyautogui.center(resources.findImageOnScreen("close.png", 0.85)))
        time.sleep(1)
        return


resources = resources()