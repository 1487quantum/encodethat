import kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
import random as rd
import MorseSM

#fx to simplify ui creation
class uiElementHandler():
    def makeLbl(self,title, phint, fsize=None):
        shint = (0.5,0.1)
        h_align = 'center'
        v_align = 'middle'
        mk_up = True        #Enable Markup for all text
        return Label(text=str(title), font_size=(fsize if fsize!=None else 30), size_hint=shint, pos_hint=phint, halign = h_align, valign=v_align, markup=mk_up)    #Set to 30 if fonsize not declared

    def makeBtn(self,title, phint, callback, enableBtn=None, shint=None, fsize=None):
        #Default font size:40,Default btnSize 25% of screen size, width height, deafult button is disabled
        return Button(text=title,font_size=(fsize if fsize!=None else 40),size_hint=(shint if shint!=None else (0.3,0.2) ), pos_hint = phint, on_press=callback, disabled=(not enableBtn if enableBtn!=None else True))

#Home screen
class MainScreen(Screen):
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        uiHdl = uiElementHandler()
        self.eList = []
        self.layout = FloatLayout()
        self.lblTitle = uiHdl.makeLbl("[color=#baed91]Encode[/color] that!", {"x":0.25,"top":0.9}, fsize=70)
        self.eList.append(self.lblTitle)
        self.btnStart = uiHdl.makeBtn("Start", {"x":0.25,"top":0.6}, self.startGameScreen, enableBtn=True, shint=(0.5,0.15))
        self.eList.append(self.btnStart)
        self.btnSettings = uiHdl.makeBtn("Settings", {"x":0.25,"top":0.4}, self.startSettingsScreen,enableBtn=True, shint=(0.5,0.15))
        self.eList.append(self.btnSettings)
        self.btnQuit = uiHdl.makeBtn("Quit", {"x":0.25,"top":0.2}, self.exitGame,enableBtn=True, shint=(0.5,0.15))
        self.eList.append(self.btnQuit)

        for k in self.eList:
            self.layout.add_widget(k)

        self.add_widget(self.layout)

    def startGameScreen(self, value):
        self.manager.transition.direction = 'left'
        self.manager.current = "game_screen"

    def startSettingsScreen(self, value):
        self.manager.transition.direction = 'up'
        self.manager.current = "settings_screen"

    def exitGame(self, value):
        App.get_running_app().stop()
        Window.close()

class GameScreen(Screen):
    elemList = []

    #Timer
    cTimerActive = False                   #Countdown timer state
    pauseTimer = False
    timeLeft = 0                           #Time left before timer expiry

    #Timer activity identifier ID constants
    READY_COUNTDOWN = 156                #ID for countdown before game start
    GAME_COUNTDOWN = 201                #ID for main game countdown

    #Game var
    DURATION_GAME = 10                 #Game duration
    WORDS_TOLOAD = 100                #Number of words to load
    gameActive = False

    #Button timing/setting
    isBtnTimerActive = False
    timeAfterPress = 0
    btnTimerUpdateInterval = 100 #How often the timer updates
    timeSpacing = 300      #Wait n milliseconds before resting text

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.layout = FloatLayout()
        #Add UI elements
        self.elemList = self.initUIElem(self.elemList)
        #Add widgets
        for el in self.elemList:
            self.layout.add_widget(el)
        self.add_widget(self.layout)

    def initUIElem(self,eList):     #Layout, element_list
        self.uiHandle = uiElementHandler()
        #Score
        self.lblScore = self.uiHandle.makeLbl("Score: 000000", {"x":0, "top":1})
        eList.append(self.lblScore)

        #Score
        self.lblTimer = self.uiHandle.makeLbl("Timer: ---", {"x":0.5, "top":1})
        eList.append(self.lblTimer)

        #Word to code
        self.lblTestWord = self.uiHandle.makeLbl('{} [color=#E5D209]{}[/color] {}'.format("Press","Go","to begin..."), {"x":0.25, "y":0.66}, fsize=70)
        eList.append(self.lblTestWord)

        #Code output
        self.lblCodeOut = self.uiHandle.makeLbl('{} Code'.format("<>"), {"x":0.25, "y":0.5}, fsize=60)
        eList.append(self.lblCodeOut)

        #User entry
        self.lblUser = self.uiHandle.makeLbl("<—>", {"x":0.25, "y":0.25}, )
        eList.append(self.lblUser)

        #Dot
        self.btnDot = self.uiHandle.makeBtn(
            '•',
            {"x":0, "right":0.5},  #Right ends at 0.5 of screen
            self.dotPress
            )
        eList.append(self.btnDot)

        #Dash
        self.btnDash = self.uiHandle.makeBtn(
            '—',
            {"x":0.5, "left":0},  #Right ends at 0.5 of screen
            self.dashPress
            )
        eList.append(self.btnDash)

        #Start btn ontop of usercode
        self.btnGo = self.uiHandle.makeBtn(
            'Go',
            {"x":0.25,"y":0.25},
            self.goPress,
            enableBtn = True,
            shint=(0.5,0.15)
        )
        eList.append(self.btnGo)

        self.btnPause = self.uiHandle.makeBtn(
            'Menu',
            {"x":0.4,"top":1},
            self.pausePress,
            enableBtn = True,
            shint=(0.2,0.1),
            fsize=30
        )
        eList.append(self.btnPause)

        return eList

    def dotPress(self, instance):
        print('\a')
        self.setUserText("•",self.lblUser)
        self.trackBtnTime()

    def dashPress(self, instance):
        self.setUserText("—",self.lblUser)
        self.trackBtnTime()

    def setUserText(self, text, lbl):
        lbl.text += text
        if(len(lbl.text)>5):
            self.resetTypedText(lbl)   #Reset text after more than 5 char

    #Clear text
    def resetTypedText(self, lbl):
        lbl.text = ""

    def showKeyGoBtn(self,showKeys, showGo):
        #Enable main btns
        self.btnDot.disabled = not showKeys
        self.btnDash.disabled = not showKeys
        self.btnGo.disabled = not showGo            #Hide go btn
        self.btnGo.opacity = 100 if showGo else 0   #Hide go button when active is true
        self.lblUser.text = "<->" if showGo else "" #Show placeholder text while waiting


    def resetGame(self):
        if(self.cTimerActive):
            Clock.unschedule(self.onUpdateTime) #Stop timer
            self.cTimerActive = False
        self.lblTimer.text = "Timer: ---"
        self.lblTestWord.text = '{} [color=#E5D209]{}[/color] {}'.format("Press","Go","to begin...")
        self.showKeyGoBtn(False,True)

    #=================================#
    #       BUTTON CALLBACK(S)
    #=================================#

    def goPress(self, instance):
        #Change game title, countdown from 3 then start
        self.lblTestWord.text = "Ready?"
        self.readyEvent = self.countdownTime(3,self.READY_COUNTDOWN)
        self.loadWordList()
        self.showKeyGoBtn(False,False)

    def pausePress(self, instance):
        if(self.cTimerActive):
            self.pauseTimer = True
        emList = []
        popupLayout = FloatLayout()
        btnResume = self.uiHandle.makeBtn(
        'Resume',
        {"x":0.25, "top":0.9},  #Right ends at 0.5 of screen
        self.resumePress,
        shint=(0.5,0.4),
        enableBtn=True
        )
        emList.append(btnResume)

        btnQuit = self.uiHandle.makeBtn(
        'Quit',
        {"x":0.25, "top":0.45},  #Right ends at 0.5 of screen
        self.quitPress,
        shint=(0.5,0.4),
        enableBtn=True
        )
        emList.append(btnQuit)

        for el in emList:
            popupLayout.add_widget(el)

        self.popupMenu = Popup(title='Game Paused',
            content=popupLayout,
            size_hint=(None, None), size=(400, 250),
            auto_dismiss=False)

        self.popupMenu.open()

    def resumePress(self,instance):
        if(self.cTimerActive):
            self.pauseTimer = False
        self.popupMenu.dismiss()

    def quitPress(self,instance):
        self.popupMenu.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = "main_screen"
        self.resetGame()


    #========================#
    #       GAME DATA
    #========================#
    def loadWordList(self):
        f = open("wordlist.txt", "r")
        self.wordList =  []                    #New list to store words
        for idx, wrd in enumerate(f):
            if(idx<int(self.WORDS_TOLOAD)):
                self.wordList.append(wrd.strip('\n').upper())               #Remove newline and capitalize all char, append to list
        print(self.wordList)


    def pickRandomWord(self):
        rd_num = rd.randint(0,self.WORDS_TOLOAD)
        self.WORDS_TOLOAD-=1
        return self.wordList.pop(rd_num)


    #========================#
    #       TIMER(S)
    #========================#

    #Duration to countdown, seconds
    #Label to update
    def countdownTime(self,tm, call_id):
        self.timeLeft = tm
        self.countdown_act_id = call_id         #Register current
        self.cTimerActive = True
        self.pauseTimer = False
        return Clock.schedule_interval(self.onUpdateTime, 1) #Refresh every 1s

    def onUpdateTime(self, dt): #Refresh duration -> dt
        #self.elemList[2].text = 'Time: {:03d}'.format(self.t)
        if(self.cTimerActive):
            if(self.timeLeft>=0):
                if(self.countdown_act_id == self.READY_COUNTDOWN):
                    if(self.timeLeft==0):
                        self.lblTestWord.text = "Begin!"
                        self.lblTimer.text = "Timer: ---"
                        self.showKeyGoBtn(True,False)
                    else:
                        self.lblTestWord.text = str(self.timeLeft)
                elif(self.countdown_act_id == self.GAME_COUNTDOWN):
                    if(self.timeLeft==0):
                        self.lblTestWord.text = "Game Over"
                        self.lblTimer.text = "Timer: ---"
                        self.showKeyGoBtn(False,False)
                    else:
                        self.lblTimer.text = "Timer: %03d"%(self.timeLeft)
                        if(len(self.lblCodeOut.text)>len(self.lblTestWord.text)):
                            self.lblTestWord.text = self.pickRandomWord()
                            self.lblCodeOut.text = ""

                if(not self.pauseTimer):
                    self.timeLeft -= 1
            else:
                if(self.countdown_act_id == self.READY_COUNTDOWN):
                    self.lblTestWord.text = ""
                    self.resetTypedText(self.elemList[3])                                           #Set player text as empty
                    self.readyEvent.cancel() #Stop timer
                    self.lblTimer.text = "Timer: %03d"%(self.DURATION_GAME)
                    self.gameEvent = self.countdownTime(self.DURATION_GAME-1,self.GAME_COUNTDOWN)    #Start game timer
                if(self.countdown_act_id == self.READY_COUNTDOWN):
                    self.gameEvent.cancel()                                                         #Stop Game timer



    #Keep track of button press
    def trackBtnTime(self):
        #Reset timing
        self.timeAfterPress = self.timeSpacing
        if(not self.isBtnTimerActive):
            self.isBtnTimerActive = True         #Start btn timer tracking
            Clock.schedule_interval(self.btnTimeTrackUpdate, self.btnTimerUpdateInterval/1000) #Refresh every 200ms

    def btnTimeTrackUpdate(self, dt):
        if(self.isBtnTimerActive):
            if(self.timeAfterPress!=0):
                self.timeAfterPress -= 100
            else:
                Clock.unschedule(self.btnTimeTrackUpdate)
                mTranslate = {'•':0,'—':1}
                morseToDecode =  self.lblUser.text
                if(morseToDecode!=None):
                    codeToSend = ""
                    for a in range(len(morseToDecode)):
                        codeToSend += str(mTranslate[morseToDecode[a]])
                    codeToSend+='2'                                      #Add delimiter
                    #print(codeToSend)
                    #Decode the morse
                    smCode = MorseSM.MorseSM()
                    decodedChar = smCode.getCharacter(codeToSend)
                    if(decodedChar!=None):                                 #Only add valid characters
                        self.lblCodeOut.text += decodedChar if decodedChar!="Idle" else ""
                self.lblUser.text = ""                          #Reset Users text
                self.isBtnTimerActive = False
                Clock.unschedule(self.btnTimeTrackUpdate)


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
        sm.add_widget(ms)
        sm.add_widget(gs)

        #sm.add_widget(st)
        sm.current = "main_screen"
        return sm


if __name__ == "__main__":
    encodeThat().run()
