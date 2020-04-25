import kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text.markup import MarkupLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup

import random as rd
import MorseSM

#fx to simplify ui creation
class uiElementHandler():
    def makeLbl(self,title, phint, fsize=None):
        shint = (0.5,0.1)
        h_align = "center"
        v_align = "middle"
        mk_up = True        #Enable Markup for all text
        return Label(text=str(title), font_size=(fsize if fsize!=None else 30), size_hint=shint, pos_hint=phint, halign = h_align, valign=v_align, markup=mk_up)    #Set to 30 if fonsize not declared

    def makeBtn(self,title, phint, callback, enableBtn=None, shint=None, fsize=None):
        #Default font size:40,Default btnSize 25% of screen size, width height, deafult button is disabled
        return Button(text=title,font_size=(fsize if fsize!=None else 35),size_hint=(shint if shint!=None else (0.3,0.2) ), pos_hint = phint, on_press=callback, disabled=(not enableBtn if enableBtn!=None else True))

#Home screen
class MainScreen(Screen):
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.uiHdl = uiElementHandler()
        eList = []
        self.layout_main = FloatLayout()
        self.lblTitle = self.uiHdl.makeLbl("[color=#baed91]Encode[/color] that!", {"x":0.25,"top":0.9}, fsize=70)
        eList.append(self.lblTitle)
        self.btnStart = self.uiHdl.makeBtn("Start", {"x":0.25,"top":0.6}, self.startGameScreen, enableBtn=True, shint=(0.5,0.15))
        eList.append(self.btnStart)
        self.btnSettings = self.uiHdl.makeBtn("How to play?", {"x":0.25,"top":0.4}, self.startHowTo,enableBtn=True, shint=(0.5,0.15))
        eList.append(self.btnSettings)
        self.btnQuit = self.uiHdl.makeBtn("Quit", {"x":0.25,"top":0.2}, self.exitGame,enableBtn=True, shint=(0.5,0.15))
        eList.append(self.btnQuit)
        for k in eList:
            self.layout_main.add_widget(k)
        self.add_widget(self.layout_main)

    def startGameScreen(self, instance):
        self.toNextScreen("left","game_screen")

    def startHowTo(self, instance):
        #  New layout for dialog box
        popupLayout = FloatLayout()
        self.lblInstructions = self.uiHdl.makeLbl("1) Encode the words shown in the center as fast as possible\n before the timer reaches 0!\n\n2) Control the dot and dash keys by either:\n- Pressing the dedicated keys below the game screen\nOR\n- The left (dot) & right (dash) arrow keys of the keyboard.\n\n3) Good luck & have fun!", {"x":0.25,"top":0.7}, fsize=20)
        popupLayout.add_widget(self.lblInstructions)
        self.btnCloseHTB = self.uiHdl.makeBtn("Close", {"x":0.25,"top":0.2}, self.closeHTB, enableBtn=True, shint=(0.5,0.15), fsize=30)
        popupLayout.add_widget(self.btnCloseHTB)
        self.popupHTB = Popup(title="Instructions",content=popupLayout,size_hint=(None, None), size=(600, 400),auto_dismiss=False)     #Show Dialog box
        self.popupHTB.open()

    def toNextScreen(self, direction, page):
        self.manager.transition.direction = direction
        self.manager.current = page

    def closeHTB(self, instance):
        self.popupHTB.dismiss()

    def exitGame(self, value):
        App.get_running_app().stop()
        Window.close()

class GameScreen(Screen):
    #Timer activity identifier ID constants
    READY_COUNTDOWN = 156                #ID for countdown before game start
    GAME_COUNTDOWN = 201                #ID for main game countdown

    gameConfig = {"G_DURATION":60,"LOAD_WORDS":200, "chkBtnInterval":100, "resetTime": 300}     #Game config: Game duration (seconds), Num of words to load, Check button interval (How often to check button state change, milliseconds), Key input reset (How long to wait before resetting the dot and dash input, milliseconds)
    gTimerState = {"menuPause":False,"keysActive":False, "preGame":False, "mainGame":False}     #GameTimer: Pause game, Check for button press, preGame Countdown, main game
    timeLeft = {"game":0,"btnPress":0}                                                          #Time left: Main Game, milliseconds since last press

    game_totalScore = 0

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        #Attach _keyboard
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.layout_game = FloatLayout()
        for el in self.initUIElem():                       #Add UI elements, then Add widgets to layout from list
            self.layout_game.add_widget(el)
        self.add_widget(self.layout_game)

    def initUIElem(self):       #Layout, element_list
        eList = []              #Temp list
        self.uiHandle = uiElementHandler()
        self.lblScore = self.uiHandle.makeLbl("Score: ------", {"x":0, "top":1})        #Score
        eList.append(self.lblScore)
        self.lblTimer = self.uiHandle.makeLbl("Timer: ---", {"x":0.5, "top":1})         #Timer
        eList.append(self.lblTimer)
        self.lblTestWord = self.uiHandle.makeLbl("{} [color=#E5D209]{}[/color] {}".format("Press","Go","to begin..."), {"x":0.25, "y":0.66}, fsize=70)          #Test Word
        eList.append(self.lblTestWord)
        self.lblCodeOut = self.uiHandle.makeLbl("", {"x":0.25, "y":0.5}, fsize=60)                              #Decoded Morse output
        eList.append(self.lblCodeOut)
        self.lblUser = self.uiHandle.makeLbl("<—>", {"x":0.25, "y":0.25}, )                                                         #User entry
        eList.append(self.lblUser)
        #           BUTTONS             #
        self.btnDot = self.uiHandle.makeBtn("•",{"x":0, "right":0.5},self.dotPress)                                                 #Dot button, Right side ends at 0.5 of screen
        eList.append(self.btnDot)
        self.btnDash = self.uiHandle.makeBtn("—",{"x":0.5, "left":0},self.dashPress)                                                #Dash btn
        eList.append(self.btnDash)
        self.btnGo = self.uiHandle.makeBtn("Go",{"x":0.25,"y":0.25},self.goPress,enableBtn = True,shint=(0.5,0.15))                 #Start btn, ontop of usercode and shown before game starts
        eList.append(self.btnGo)
        self.btnPause = self.uiHandle.makeBtn("Menu",{"x":0.4,"top":1},self.pausePress,enableBtn = True,shint=(0.2,0.1),fsize=30)   #Menu button
        eList.append(self.btnPause)
        return eList

    #=================#
    #       UI
    #================#
    def setPlayerKeys(self,text):
        self.setUserText(text,self.lblUser)
        self.trackBtnTime()

    def setUserText(self, text, lbl):
        lbl.text += text
        if(len(lbl.text)>5):
            self.resetTypedText([lbl])   #Reset text after more than 5 char

    #Clear list of text
    def resetTypedText(self, lblList):
        for e in lblList:
            e.text = ""

    def showKeyGoBtn(self,showKeys, showGo):
        #Enable main btns
        self.btnDot.disabled = not showKeys
        self.btnDash.disabled = not showKeys
        self.btnGo.disabled = not showGo            #Hide go btn
        self.btnGo.opacity = 100 if showGo else 0   #Hide go button when active is true
        self.lblUser.text = "<->" if showGo else "" #Show placeholder text while waiting

    def resetGame(self):
        if(self.gTimerState["preGame"]):
            self.readyEventClock.cancel() #Stop timer
            self.gTimerState["preGame"] = False
        if(self.gTimerState["mainGame"]):
            self.btnTrackClk.cancel()
            if(self.lblUser.text!=""):
                self.gameEventClock.cancel()
                self.beforeNextWordClk.cancel()
        self.setScoreTimerText("-----","---")
        self.resetTypedText([self.lblCodeOut])
        self.game_totalScore = 0
        self.lblTestWord.text = "{} [color=#E5D209]{}[/color] {}".format("Press","Go","to begin...")
        self.showKeyGoBtn(False,True)
        self.gTimerState["preGame"] = False

    #=================================#
    #       GAME STATE
    #=================================#
    def pauseGameState(self, stateActive):
        if(self.gTimerState["preGame"]):
            self.gTimerState["menuPause"] = stateActive

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if(self.gTimerState["mainGame"]):
            if keycode[1] == "left":
                self.dotPress(None)
            elif keycode[1] == "right":
                self.dashPress(None)
        return True

    #=================================#
    #       BUTTON CALLBACK(S)
    #=================================#
    def dotPress(self, instance):
        print("\a")
        self.setPlayerKeys("•")

    def dashPress(self, instance):
        self.setPlayerKeys("—")

    def goPress(self, instance):
        #Change game title, countdown from 3 then start
        self.lblTestWord.text = "Ready?"
        self.readyEventClock = self.countdownTime(3,self.READY_COUNTDOWN)
        self.loadWordList()
        self.showKeyGoBtn(False,False)

    def pausePress(self, instance):
        self.pauseGameState(True)
        emList = []
        #  New layout for dialog box
        popupLayout = FloatLayout()
        btnResume = self.uiHandle.makeBtn("Resume",{"x":0.25, "top":0.9},  self.resumePress,shint=(0.5,0.4),enableBtn=True)           #Resumes game,
        emList.append(btnResume)
        btnQuit = self.uiHandle.makeBtn("Quit",{"x":0.25, "top":0.45}, self.quitPress,shint=(0.5,0.4),enableBtn=True)                 #Return to main menu
        emList.append(btnQuit)
        for el in emList:
            popupLayout.add_widget(el)
        self.popupMenu = Popup(title="Game Paused",content=popupLayout,size_hint=(None, None), size=(400, 250),auto_dismiss=False)     #Show Dialog box
        self.popupMenu.open()

    def resumePress(self,instance):
        self.pauseGameState(False)
        self.popupMenu.dismiss()

    def quitPress(self,instance):
        self.popupMenu.dismiss()
        # self.manager.transition.direction = "right"
        # self.manager.current = "main_screen"
        # self.resetGame()
        App.get_running_app().stop()
        Window.close()

    #==============================#
    #       DATA MANIPULATION
    #==============================#
    def loadWordList(self):
        f = open("wordlist.txt", "r")
        self.wordList =  []                    #New list to store words
        for idx, wrd in enumerate(f):
            if(idx<int(self.gameConfig["LOAD_WORDS"])):
                self.wordList.append(wrd.strip("\n").upper())               #Remove newline and capitalize all char, append to list
        print(self.wordList)

    def pickRandomWord(self):
        rd_num = rd.randint(0,self.gameConfig["LOAD_WORDS"]-1)
        self.gameConfig["LOAD_WORDS"]-=1
        return self.wordList.pop(rd_num)

    def nextWord(self):
        self.lblTestWord.text = "[color={}]{}[/color]".format("#FFFFFF",self.pickRandomWord())
        self.resetTypedText([self.lblCodeOut])                       #Reset Users text

    def decodeString(self, targetString):
        if(targetString!=None):
            mTranslate = {"•":0,"—":1}
            codeToSend = ""
            #Send the code
            for a in range(len(targetString)):
                codeToSend += str(mTranslate[targetString[a]])
            codeToSend+="2"                                      #Add delimiter
            #print(codeToSend)
            smCode = MorseSM.MorseSM()
            return smCode.getCharacter(codeToSend)

    def checkCorrect(self, testWordStr, inputStr, decodedChar):
        if(self.gTimerState["mainGame"]):
            mainWord = MarkupLabel(testWordStr).markup[1]
            if(len(inputStr)>len(mainWord)):
                self.nextWord()                                 #Get new word, Reset text
            elif(len(inputStr)>0):                              #Highlight correct/wrong
                #self.lblScore.text = str(mainWord[len(inputStr)-1])
                if(mainWord[len(inputStr)-1]==decodedChar):    #Extract text from markup, then extract char at index
                    textHighlight = "#baed91"               #Correct, green
                    self.game_totalScore+=10
                else:
                    textHighlight = "#ff6961"               #Wrong, red
                self.lblTestWord.text = "[color={}]{}[/color]".format(textHighlight,mainWord)
                self.lblScore.text = "Score: %05d"%self.game_totalScore
                if(len(inputStr)==len(mainWord)):         #Check if it's last word
                    self.beforeNextWordClk = Clock.schedule_once(self.loadNextWord,0.5)                     #Wait for 0.5 second before showing next word

    #========================#
    #       TIMER(S)
    #========================#
    #Duration to countdown, seconds
    #Label to update
    def countdownTime(self,tm, call_id):
        self.timeLeft["game"] = tm
        self.countdown_act_id = call_id         #Register current
        self.gTimerState["preGame"] = True
        self.gTimerState["menuPause"] = False
        return Clock.schedule_interval(self.onUpdateTime, 1) #Refresh every 1s

    def setScoreTimerText(self,score,timeRm):
        self.lblScore.text = "Score: "
        self.lblTimer.text = "Timer: "
        try:
            self.lblScore.text+="{:05d}".format(score)
            self.lblTimer.text+= "{:03d}".format(timeRm)
        except:
            self.lblScore.text+=score
            self.lblTimer.text+=timeRm

    def onUpdateTime(self, dt): #Refresh duration -> dt
        #self.elemList[2].text = 'Time: {:03d}'.format(self.t)
        if(self.gTimerState["preGame"]):
            if(self.timeLeft["game"]>=0):
                if(self.countdown_act_id == self.READY_COUNTDOWN):
                    if(self.timeLeft["game"]==0):
                        self.lblTestWord.text = "Begin!"
                        self.setScoreTimerText(0,0)
                    else:
                        self.lblTestWord.text = str(self.timeLeft["game"])
                elif(self.countdown_act_id == self.GAME_COUNTDOWN):
                    if(self.timeLeft["game"]==0):
                        self.lblTestWord.text = "Game Over"
                        self.lblCodeOut.text = "[color=E5D209]"+self.lblScore.text+"[/color]"
                        self.setScoreTimerText("-----","---")
                        self.gTimerState["mainGame"] = False
                        self.showKeyGoBtn(False,False)
                    else:
                        self.lblTimer.text = "Timer: %03d"%(self.timeLeft["game"])
                        self.gTimerState["mainGame"] = True
                if(not self.gTimerState["menuPause"]):
                    self.timeLeft["game"] -= 1
            else:
                if(self.countdown_act_id == self.READY_COUNTDOWN):
                    self.resetTypedText([self.lblCodeOut,self.lblTestWord,self.lblUser])                  #Set player text as empty
                    self.readyEventClock.cancel()                                                #Stop clock
                    self.lblTimer.text = "Timer: {:03d}".format(self.gameConfig["G_DURATION"])
                    self.nextWord()
                    self.showKeyGoBtn(True,False)                                                         #Enable keys
                    self.gameEventClock = self.countdownTime(self.gameConfig["G_DURATION"]-1,self.GAME_COUNTDOWN)    #Start game timer

    #Keep track of button press, and to cross check if the character is decoded correctly
    def trackBtnTime(self):
        #Reset timing
        self.timeLeft["btnPress"] = self.gameConfig["resetTime"]
        if(not self.gTimerState["keysActive"]):
            self.gTimerState["keysActive"] = True         #Start btn timer tracking
            self.btnTrackClk = Clock.schedule_interval(self.btnTimeTrackUpdate, self.gameConfig["chkBtnInterval"]/1000) #Refresh every 200ms

    def btnTimeTrackUpdate(self, dt):
        if(self.gTimerState["keysActive"]):
            if(self.timeLeft["btnPress"]!=0):
                self.timeLeft["btnPress"] -= 100
            else:
                decodedChar = self.decodeString(self.lblUser.text)            #Get decoded string
                if(decodedChar!=None):                                 #Only add valid characters
                    self.lblCodeOut.text += ("{}".format(decodedChar)) if len(decodedChar)<=1 else ""
                self.resetTypedText([self.lblUser])                       #Reset Users text
                #Check text only when game is active
                self.checkCorrect(self.lblTestWord.text, self.lblCodeOut.text, decodedChar)
                self.gTimerState["keysActive"] = False
                self.btnTrackClk.cancel()

    def loadNextWord(self,dt):
        if(self.gTimerState["mainGame"]):
            self.nextWord()
        self.beforeNextWordClk.cancel()   #Unschedule clock once done

class encodeThat(App):
    #Set screen size
    SWIDTH = 800
    SHEIGHT = 500

    def build(self):
        Window.size = (self.SWIDTH, self.SHEIGHT)    #Set window size
        self.title = "Encode that!"
        sm = ScreenManager()
        ms = MainScreen(name="main_screen")
        gs = GameScreen(name="game_screen")
        #st = SettingsScreen(name='settings_screen')
        sm.add_widget(ms)               #Add screens
        sm.add_widget(gs)
        sm.current = "main_screen"
        return sm

if __name__ == "__main__":
    encodeThat().run()
