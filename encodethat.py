import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text.markup import MarkupLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
import random as rd
from libdw import sm

class MainScreen(Screen):           #Home screen
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.populateUI()

    def populateUI(self):
        layout_main = BoxLayout(padding=(100,30),orientation="vertical")
        self.lblTitle = Label(text="[color=#baed91]Encode[/color] that!", font_size=70, size_hint=(1,0.4), halign = "center", valign="middle", markup=True)
        self.btnStart = Button(text="Start",font_size=35,size_hint=(1,0.2), on_press=self.startGameScreen, disabled=False)
        self.btnSettings = Button(text="How to play",font_size=35,size_hint=(1,0.2),  on_press=self.startHowTo, disabled=False)
        self.btnQuit = Button(text="Quit",font_size=35,size_hint=(1,0.2),  on_press=self.exitGame, disabled=False)
        layout_main.add_widget(self.lblTitle)
        layout_main.add_widget(self.btnStart)
        layout_main.add_widget(self.btnSettings)
        layout_main.add_widget(self.btnQuit)
        self.add_widget(layout_main)

    def toNextScreen(self, direction, page):
        self.manager.transition.direction = direction
        self.manager.current = page

    #Callback functions
    def startGameScreen(self, instance):
        self.toNextScreen("left","game_screen")

    def startHowTo(self, instance):
        popupLayout = BoxLayout(orientation="vertical")
        self.lblInstructions = Label(text="1) Encode the words shown in the center as fast as possible\n before the timer reaches 0!\n\n2) Control the dot and dash keys by either:\n- Pressing the dedicated keys below the game screen\nOR\n- The left (dot) & right (dash) arrow keys of the keyboard.\n\n3) Good luck & have fun!", font_size=20,  size_hint=(1, .8),  markup=True)
        self.btnCloseHTB = Button(text="Close",font_size=30,size_hint=(1, .2),on_press=self.closeHTB, disabled=False) #Padding: x,y
        popupLayout.add_widget(self.lblInstructions)
        popupLayout.add_widget(self.btnCloseHTB)
        self.popupHTB = Popup(title="Instructions",content=popupLayout,size_hint=(None, None), size=(600, 400),auto_dismiss=False)     #Show Dialog box
        self.popupHTB.open()

    def closeHTB(self, instance):
        self.popupHTB.dismiss()

    def exitGame(self, instance):
        App.get_running_app().stop()
        Window.close()

class GameScreen(Screen):
    gTimerState = {"menuPause":False,"keysActive":False, "preGame":False, "mainGame":False}     #GameTimer: Pause game, Check for button press, preGame Countdown, main game
    timeLeft = {"game":0,"btnPress":0}                                                          #Time left: Main Game, milliseconds since last press
    game_totalScore = 0

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self._bindKeyboard()                                                               #Attach _keyboard
        self._loadConfig()                                                                 #Load gameConfig
        layout_game = BoxLayout(padding=20,orientation="vertical")                        #Add UI elements
        for sct in [self.addTopSection(),self.addMidSection(),self.addBtmSection()]:      #Add main widgets
            layout_game.add_widget(sct)
        self.add_widget(layout_game)
        #Init timers
        self.readyEventClock=None
        self.btnTrackClk=None
        self.gameEventClock=None
        self.beforeNextWordClk=None

    #=================#
    #       UI
    #================#
    def addTopSection(self):
        topSection = BoxLayout(padding=(40,0), size_hint=(1,0.15), orientation="horizontal")
        self.lblScore = Label(text="Score: ------", font_size=35,  size_hint=(0.35,1)) #Score
        self.btnMenu = Button(text="Menu",font_size=30,size_hint=(0.3,1),on_press=self.pausePress) #Padding: x,y
        self.lblTimer = Label(text="Timer: ---", font_size=35,  size_hint=(0.35,1)) #Time
        topSection.add_widget(self.lblScore)
        topSection.add_widget(self.btnMenu)
        topSection.add_widget(self.lblTimer)
        return topSection

    def addMidSection(self):
        midSection = BoxLayout(orientation="vertical")
        self.lblTestWord = Label(text="{} [color=#E5D209]{}[/color] {}".format("Press","Go","to begin..."), font_size=70,  size_hint=(1, .3),markup=True) #Score
        self.lblCodeOut = Label(text="", font_size=40,  size_hint=(1, .2), halign="center", markup=True) #Codeout
        self.lblUser = Label(text="<->", font_size=30,  size_hint=(1, .1)) #User
        self.btnGo = Button(text="Go",font_size=30,size_hint=(1,.15),on_press=self.goPress)
        midSection.add_widget(self.lblTestWord)
        midSection.add_widget(self.lblCodeOut)
        midSection.add_widget(self.lblUser)
        midSection.add_widget(self.btnGo)
        return midSection

    def addBtmSection(self):
        btmSection = BoxLayout(padding=(60,10), size_hint=(1,0.2), orientation="horizontal")
        self.btnDot = Button(text="•",size_hint=(0.5, 1),on_press=self.dotPress, disabled=True)                   #Dot button, Right side ends at 0.5 of screen
        self.btnDash = Button(text="—",size_hint=(0.5, 1),on_press=self.dashPress, disabled=True)                 #Dash btn
        btmSection.add_widget(self.btnDot)
        btmSection.add_widget(self.btnDash)
        return btmSection

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
        self.gTimerState["preGame"] = False
        self.gTimerState["mainGame"] = False
        self.gTimerState["keysActive"] = False
        self.pauseGameState(False)
        for tm in [self.readyEventClock,self.btnTrackClk,self.gameEventClock,self.beforeNextWordClk]:   #Cancel all active timers
            self.cancelTimer(tm)
        self.setScoreTimerText("-----","---")
        self.resetTypedText([self.lblCodeOut])
        self.game_totalScore = 0
        self.lblTestWord.text = "{} [color=#E5D209]{}[/color] {}".format("Press","Go","to begin...")
        self.showKeyGoBtn(False,True)

    def appendIntText(self,lblName,strToAdd, numZero):
        try:
            lblName.text+="{0:0{1:d}d}".format(strToAdd,numZero)
        except:
            lblName.text+=strToAdd

    #=================================#
    #       GAME STATE
    #=================================#
    def pauseGameState(self, stateActive):
        self.gTimerState["menuPause"] = stateActive

    def _bindKeyboard(self):
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

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
        self.setPlayerKeys("•")

    def dashPress(self, instance):
        self.setPlayerKeys("—")

    def goPress(self, instance):
        self.lblTestWord.text = "Ready?"
        self.gTimerState["preGame"] = True
        self.readyEventClock = self.countdownTime(3)
        self.loadWordList()
        self.showKeyGoBtn(False,False)

    def pausePress(self, instance):
        self.pauseGameState(True)
        popupLayout = BoxLayout(padding=(40,10), orientation="vertical")
        btnResume = Button(text="Resume",font_size=30,size_hint=(1, .5),on_press=self.resumePress, disabled=False) #Padding: x,y
        btnQuit = Button(text="Quit",font_size=30,size_hint=(1, .5),on_press=self.quitPress, disabled=False) #Padding: x,y
        popupLayout.add_widget(btnResume)
        popupLayout.add_widget(btnQuit)
        self.popupMenu = Popup(title="Game Paused",content=popupLayout,size_hint=(None, None), size=(400, 250),auto_dismiss=False)     #Show Dialog box
        self.popupMenu.open()

    def resumePress(self,instance):
        self.pauseGameState(False)
        self.popupMenu.dismiss()

    def quitPress(self,instance):
        self.popupMenu.dismiss()
        self.resetGame()
        self.manager.transition.direction = "right"
        self.manager.current = "main_screen"

    #==============================#
    #       DATA MANIPULATION
    #==============================#
    def _loadConfig(self):
        cg = open("res/game.cfg")
        self.gameConfig = {}
        for cfg in cg:
            if(cfg[0]!="#"):
                a = cfg.split(":")
                self.gameConfig[a[0]] = int(a[1].strip("\n").strip())

    def updateHighscore(self, new_score):
        lines = open("res/game.cfg").read().splitlines()
        lines[-1] = "highscore: "+ str(new_score)
        open("res/game.cfg", "w").write("\n".join(lines))

    def loadWordList(self):
        f = open("res/wordlist.txt", "r")
        self.wordList =  []                    #New list to store words
        for idx, wrd in enumerate(f):
            if(idx<int(self.gameConfig["LOAD_WORDS"])):
                self.wordList.append(wrd.strip("\n").upper())               #Remove newline and capitalize all char, append to list

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
            for a in range(len(targetString)):                          #Send the code
                codeToSend += str(mTranslate[targetString[a]])
            codeToSend+="2"                                             #Add delimiter
            smCode = MorseSM()
            return smCode.getCharacter(codeToSend)

    def checkCorrect(self, testWordStr, inputStr, decodedChar):
        if(self.gTimerState["mainGame"]):
            mainWord = MarkupLabel(testWordStr).markup[1]
            if(len(inputStr)>len(mainWord)):
                self.nextWord()                                 #Get new word, Reset text
            elif(len(inputStr)>0):                              #Highlight correct/wrong
                if(mainWord[len(inputStr)-1]==decodedChar):    #Extract text from markup, then extract char at index
                    textHighlight = "#baed91"                   #Correct, green
                    self.game_totalScore+=10
                else:
                    textHighlight = "#ff6961"                   #Wrong, red
                self.lblTestWord.text = "[color={}]{}[/color]".format(textHighlight,mainWord)
                self.lblScore.text = "Score: %05d"%self.game_totalScore
                if(len(inputStr)==len(mainWord)):               #Check if it's last word
                    self.cancelTimer(self.beforeNextWordClk)
                    self.beforeNextWordClk = Clock.schedule_once(self.loadNextWord,0.5)                     #Wait for 0.5 second before showing next word

    #========================#
    #       TIMER(S)
    #========================#
    #Duration to countdown, seconds
    def countdownTime(self,tm):
        self.timeLeft["game"] = tm
        self.gTimerState["menuPause"] = False
        return Clock.schedule_interval(self.onUpdateTime, 1) #Refresh every 1s

    def setScoreTimerText(self,score,timeRm):
        self.lblScore.text = "Score: "
        self.lblTimer.text = "Timer: "
        self.appendIntText(self.lblScore,score,5)
        self.appendIntText(self.lblTimer,timeRm,3)

    def onUpdateTime(self, dt): #Refresh duration -> dt
        if(self.gTimerState["preGame"]):        #Pregame countdown
            if(self.timeLeft["game"]>0):
                self.lblTestWord.text = str(self.timeLeft["game"])
            else:                                                                                     #When it hits 0
                self.setScoreTimerText(0,self.gameConfig["G_DURATION"])
                self.resetTypedText([self.lblCodeOut,self.lblTestWord,self.lblUser])                  #Set player text as empty
                self.showKeyGoBtn(True,False)                                                         #Enable keys
                self.nextWord()
                self.gTimerState["preGame"] = False
                self.gTimerState["mainGame"] = True
                self.cancelTimer(self.readyEventClock)                                               #Stop preGame clock
                self.gameEventClock = self.countdownTime(self.gameConfig["G_DURATION"])              #Start game timer

        elif(self.gTimerState["mainGame"]):
            if(self.timeLeft["game"]>0):
                self.setScoreTimerText(self.lblScore.text[7:], self.timeLeft["game"])
            else:
                f_score = self.game_totalScore
                self.resetGame()
                self.lblTestWord.text = "Game Over"
                self.lblCodeOut.text = "Highscore: {:05d}\nScore: [color=E5D209]{:05d}[/color]".format(self.gameConfig["highscore"],f_score)
                if(f_score>self.gameConfig["highscore"]):
                    self.updateHighscore(f_score)
                    self.gameConfig["highscore"]=f_score
                    self.lblCodeOut.text += "\n[color=E5D209]New Highscore![/color]"
                self.showKeyGoBtn(False,False)
        if(not self.gTimerState["menuPause"]):
            self.timeLeft["game"] -= 1

    #Keep track of button press, and to cross check if the character is decoded correctly
    def trackBtnTime(self):
        self.timeLeft["btnPress"] = self.gameConfig["resetTime"]        #Reset timing
        if(not self.gTimerState["keysActive"]):
            self.gTimerState["keysActive"] = True                       #Start btn timer tracking
            self.cancelTimer(self.btnTrackClk)
            self.btnTrackClk = Clock.schedule_interval(self.btnTimeTrackUpdate, self.gameConfig["chkBtnInterval"]/1000) #Refresh every 200ms

    def btnTimeTrackUpdate(self, dt):
        if(self.gTimerState["keysActive"]):
            if(self.timeLeft["btnPress"]!=0):
                self.timeLeft["btnPress"] -= self.gameConfig["chkBtnInterval"]
            else:
                decodedChar = self.decodeString(self.lblUser.text)                                       #Get decoded string
                if(decodedChar!=None):                                                                   #Only add valid characters
                    self.lblCodeOut.text += ("{}".format(decodedChar)) if len(decodedChar)<=1 else ""
                self.resetTypedText([self.lblUser])                                                      #Reset Users text
                self.checkCorrect(self.lblTestWord.text, self.lblCodeOut.text, decodedChar)              #Check text only when game is active
                self.gTimerState["keysActive"] = False
                self.cancelTimer(self.btnTrackClk)

    def loadNextWord(self,dt):
        if(self.gTimerState["mainGame"]):
            self.nextWord()
        self.cancelTimer(self.beforeNextWordClk)    #Unschedule clock once done

    def cancelTimer(self, timerName):
        if(timerName!=None):
            Clock.unschedule(timerName)

class MorseSM(sm.SM):
    def __init__(self):
        #Input: 0->Dot, 1->Dash
        #Dictionary of traversal paths => Elem: 0->Dot, 1->Dash, 2->Return val to program
        self.fsmTree = {
                    'Idle':['E','T','*'],       #Lv 0
                    'E':['I','A','*'],          #Lv 1
                    'T':['N','M','*'],
                    'I':['S','U','*'],          #Lv 2
                    'A':['R','W','*'],
                    'N':['D','K','*'],
                    'M':['G','O','*'],
                    'S':['H','V','*'],          #Lv 3
                    'U':['F','*','*'],
                    'R':['L','*','*'],
                    'W':['P','J','*'],
                    'D':['B','X','*'],
                    'K':['C','Y','*'],
                    'G':['Z','Q','*'],
                    'O':['*','*','*'],
                    '*':['*','*','*']
                    }
        charToAdd = ['H','V','F','L','P','J','B','X','C','Y','Z','Q']                   #Add level 4 items for remaining characters
        for ch in charToAdd:
            self.fsmTree[ch] = ['*','*','*']
        self.start_state = 'Idle'

    def get_next_values(self, state, inp):
        if state in self.fsmTree:            #If state exist in dict
            charToReturn = self.fsmTree[state][int(inp)]
            if(charToReturn=='*'):
                if(inp=='0' or inp=='1'):
                    res = 'NA', 'NA'        #If both state = * and input is 1/2, return None (Invalid)
                else:
                    res = state, state        #Return state as result if it's *
            else:
                res = self.fsmTree[state][int(inp)], inp
        else:
            res = None, None
        return res

    def getCharacter(self, codeStr):
        if(len(codeStr)<6):                                     #Accept only less than 5 numbers and numbers only
            if(codeStr.isdigit()):
                if(codeStr[-1]=="2"):
                    return MorseSM().transduce(codeStr)[-1]    #Return only last character
                else:
                    return 'Error: Missing back delimiter!'
            else:
                return 'Error: Not all char are digit(s)!'
        else:
            return 'Error: String length exceeded!'

    # def testAllCharacters(self):
    #     res = []
    #     for i in range(5):
    #         for j in range(2**i):
    #             testCode = "%0*d2"%(i,int(bin(j)[2:]))       #Remove 1st 2 char, convert back to int
    #             res_char = MorseSM().transduce(testCode)[-1]
    #             print("%s: %s"%(testCode, res_char))
    #             res.append(res_char)
    #     return res

    # def exceptionTest(self):                    #Test error catching
    #     res = ["010111","011@","011","01112"]
    #     for el in res:
    #         print('Test','Pass->' if len(gg.getCharacter(el))==1 else 'Fail->',gg.getCharacter(el))

class encodeThat(App):
    def build(self, **kwargs):
        super(encodeThat, self).__init__(**kwargs)
        Window.size = (800, 500)    #Set window size
        self.title = "Encode that!"
        sm = ScreenManager()
        ms = MainScreen(name="main_screen")
        gs = GameScreen(name="game_screen")
        sm.add_widget(ms)               #Add screens
        sm.add_widget(gs)
        sm.current = "main_screen"
        return sm

if __name__ == "__main__":
    encodeThat().run()
