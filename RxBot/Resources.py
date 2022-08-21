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

global scrollFurther
scrollFurther = False

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
        imageLocation = pyautogui.locateOnScreen("Resources/%s" % imgName, confidence=confidence)
        if not imageLocation:
            return False
        #print("Image found at " + str(imageLocation))
        return imageLocation

    def moveMouseToLocation(self, imageLocation):
        x, y = pyautogui.center(imageLocation)
        pyautogui.moveTo(x, y, 0.2)

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
    pyautogui.hotkey('f5')
    time.sleep(0.4)
    pyautogui.hotkey('enter')
    time.sleep(2)
    gotoTab("hitlist")
    print("Refreshed and reset to Hitlist tab")


def adjustCoords(point):
    #x = point[0] - 1920
    x = point[0]
    y = point[1]
    return x, y


def gotoTab(tab):  # tab.png
    tab = tab.lower()
    if resources.findImageOnScreen("%s.png" % tab, 0.8):
        resources.moveMouseToLocation(resources.findImageOnScreen("%s.png" % tab, 0.8))
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
    global scrollFurther
    #gotoTab('hitlist')

    count = 0

    pyautogui.scroll(1000)
    pyautogui.scroll(-385)
    time.sleep(0.2)
    if scrollFurther:
        pyautogui.scroll(-385)
    time.sleep(0.4)


    if not pyautogui.locateOnScreen('Resources/lottoListing.png', confidence=0.9):
        print("Lottery is likely over. Waiting a few seconds then trying again...")
        time.sleep(10)
        resetStartAgain()
        return

    for position in pyautogui.locateAllOnScreen('Resources/lottoListing.png', confidence=0.9):
        scrollFurther = False
        # TODO REMOVE THIS ITS JUST FOR TESTING
        point = adjustCoords(pyautogui.center(position))
        curUsername = getUsername(point)


        print("Checking %s" % curUsername.replace("\n", ""))

        if curUsername in hitlistBlacklist:
            print("User is blacklisted, skipping.")
        else:
            time.sleep(0.1)
            curBounty = getBounty(point)
            if curBounty > settings["MAX BOUNTY"]:
                print("Bounty too high!")
                hitlistBlacklist.append(curUsername)

            else:

                time.sleep(0.2)
                print("Bounty low enough... attacking!")
                # Store the username to easily find it again

                pyautogui.moveTo(point[0] + 600, point[1])
                pyautogui.click()
                time.sleep(0.4)

                # Determine if lost or not by looking for the you lose
                if resources.findImageOnScreen("attackAgain.png", 0.85):
                    print("Won! Attacking again...")

                    while resources.findImageOnScreen("attackAgain.png", 0.85):
                        resources.moveMouseToLocation(resources.findImageOnScreen("attackAgain.png", 0.85))
                        pyautogui.click()
                        time.sleep(0.2)

                    print("Can't attack again anymore, resetting.")
                    scrollFurther = True
                    hitlistBlacklist.append(curUsername)
                    return


                else:
                    scrollFurther = True
                    hitlistBlacklist.append(curUsername)  # Lost! Move onto the next person and try again.
                    return

    print("End of list!")
    resetStartAgain()




resources = resources()