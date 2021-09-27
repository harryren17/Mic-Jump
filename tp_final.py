import pyaudio
import numpy as np
import time
import aubio
import math
import random
import wave
import threading
from cmu_112_graphics import *
from wavplay import *
from AltScreens import *
from gamePieces import *

#main file for the game

# taken from https://github.com/aubio/aubio/issues/78
# Aubio's pitch detection.
pDetection = aubio.pitch("default", 2048, 2048//2, 44100)
pDetection.set_unit("Hz")
pDetection.set_silence(-50)

class GameMode(Mode):

    def showBarVol(app):
        #returns a number corresponding to the current volume input to the mic
        #adapted from https://swharden.com/blog/2016-07-19-realtime-audio-visualization-in-python/
        data = np.frombuffer(app.stream.read(2**10), dtype=np.int16)
        peak=np.average(np.abs(data))*2
        bar = int(peak)
        
        return app.sens*100*bar/2**10

    def showBarPitch(app):
        #returns a number corresponding to the current pitch input to the mic
        #adapted from https://www.makeartwithpython.com/blog/vocal-range-python-music21/
        data = app.stream.read(1024, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=aubio.float_type)
        pitch = pDetection(samples)[0]
        return pitch/10

    def appStarted(app):

        #terrain data
        app.rects = 20 #number of rectangles that make up the terrain
        app.bars = [0]*app.rects #list of current bar height values
        app.barHeight = 10
        app.HeightsList = [] #list of peak vilumes read from the mic
        app.timerDelay= 1
        app.terrainMoving = False
        app.totaltime = 0
        app.sens = 1 #sensitivity scaler for volume inputs
        app.mouseY = 0 #y cord of mouse used in mouse mode

        #stores the start, end, and width of the terrain pieces
        app.rectStartx = 100
        app.rectStarty = 800
        app.rectWidth = 800/app.rects

        #ball data
        app.ball = Ball(app.width/2,400,10) #create an instance
        app.balldx = 10 
        app.dy = 1
        app.vel = 0 #ball velocity
        app.dif = 0 #ball.y - surface; used to calculate bounce physics
        app.moveObjects = True 


        #player data
        app.pvel = 0 #player velocity
        app.pdy = 1 #player position change
        app.player = Player(200, 600) #instance of player
        app.jump = False

        #surface data
        app.surface = [] #list of tuples that represent points forming a surface
        for i in range(app.rects):
            left = app.rectStartx+app.rectWidth*i
            top = app.rectStarty-app.bars[i] if app.rectStarty-app.bars[i]>100 else 100
            right = app.rectStartx + app.rectWidth+app.rectWidth*i
            app.surface.append((left,top,right,top))
        
        
        #Power up data
        app.gameObjects = []
        target = Target()
        app.freezeObj = FreezePower()
        app.magnetObj = MagnetPower()
        app.mouseObj = MousePower()
        app.gameObjects.append(target)
        app.gameObjects.append(app.freezeObj)
        app.gameObjects.append(app.magnetObj)
        app.gameObjects.append(app.mouseObj)
        app.hasFreeze = True #enables/disables freeze power
        app.hasMag = True #enables/disables magnet power
        app.hasMouse = True #enables/disables mouse power
        app.ftimer = 0 #freeze power timer
        app.mtimer = 0 #magnet power timer
        app.mousetimer = 0 #mouse power timer
        app.magnet = False #turns on/off the freeze power effect
        app.freeze = False #turns on/off the magnet power effect
        app.mouse = False #turns on/off the mouse power effect

        #toggle volume/pitch mode        
        app.vol = True
        
        #game data
        app.score = 0
        app.lives = 5
        app.gameOver = False
        app.prevScore = 0
        app.settingsScreen = True

        #Images       
        app.onImage = app.loadImage('onswitch.png')
        app.offImage = app.loadImage('offswitch.png')
        app.settingsImage= app.scaleImage(app.loadImage('settings.png'),1/4)
        app.mousePowerImage = app.loadImage('mousePower.png')
        app.freezePowerImage = app.scaleImage(app.loadImage('freezePower.png'), 1/2)
        app.magnetPowerImage = app.scaleImage(app.loadImage('magnetPower.png'),1)
        app.gameBackGroundImage = app.scaleImage(app.loadImage('back2.jpg'),2)    

        #adapted from https://www.cs.cmu.edu/~112/notes/notes-animations-part3.html
        app.spriteStrip = app.loadImage('adjusteds.png')
        app.sprites = []
        for i in range(10):
            sprite = app.scaleImage(app.spriteStrip.crop((75*i, 3, 75+75*i, 100)),1/2)
            app.sprites.append(sprite)
        app.spriteCounter = 0

        #Audio processing data
        app.wavFile = None
        app.filedelay = 0
        app.fileBars = []
        app.nowPlaying = 'Press 1 to load in your own music'
        CHUNK = 2**10
        RATE = 44100
        #taken from https://swharden.com/blog/2016-07-19-realtime-audio-visualization-in-python/
        app.p=pyaudio.PyAudio()
        app.stream=app.p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input = True,
              frames_per_buffer=CHUNK)

    def bounce(app):
        #calculates the collision and physics of the ball

        if app.balldx > 20: #slows the horiz speed gradually to a set max speed
            app.balldx -= 1
        if app.balldx < -20:
            app.balldx += 1

        for i in range(len(app.surface)):
            if len(app.surface[i]) == 4:
                x0,y0,x1,y1 = app.surface[i]
                m = (y1-y0)/(x1-x0)
                ybound = m*(app.ball.x - x1) + y1
                theta = math.pi/2 - math.atan(m)
                if x0 < app.ball.x <= x1:
                    if app.ball.y >= ybound:
                        app.dif = app.ball.y - ybound
                        app.ball.y = ybound - app.ball.r
                        app.vel = -app.vel + app.dif
                        if math.cos(theta) > .1: #line with a negitave slope         
                            if app.balldx < 0: #approaches the slope from the left; x speed should increase
                                app.balldx = app.balldx-app.vel*(math.cos(theta))
                                app.vel *= math.sin(theta)
                                if math.cos(theta) > 0.70: #this is the flip case for an angle greater than 45 deg
                                    #a sharp angle flips the direction of the x vel scaled by the cos of the angle
                                    app.balldx = -app.vel*(math.cos(theta))
                            else: #approaches the slope from the right; x speed should decrease
                                app.balldx += abs(app.vel*(math.cos(theta)))  
                        if math.cos(theta) < -.1: #line with a positive slope
                            theta = math.pi/2 - (math.pi - theta)
                            if app.balldx > 0: #approaches the slope from the right; x speed should increase
                                app.balldx = app.balldx+app.vel*(math.cos(theta))
                                app.vel *= math.sin(theta)
                                if math.cos(theta) > 0.70: #flip case
                                    app.balldx = app.vel*(math.cos(theta))
                            else: #approaches the slope from the left; x speed should decrease
                                app.balldx -= abs(app.vel *(math.cos(theta)))
                           
                        break

            if len(app.surface[i]) == 8:
                x0,y0,x1,y1,x2,y2,x3,y3 = app.surface[i]
                if x0<= app.ball.x<=x1:
                    if app.ball.y >= y0:
                        app.dif = app.ball.y - y0
                        app.ball.y = y0 - app.ball.r
                        app.vel = -app.vel + app.dif
                elif x2<= app.ball.x <= x3:
                    if app.ball.y >= y2:
                        app.dif = app.ball.y - y2
                        app.ball.y = y2 - app.ball.r
                        app.vel = -app.vel + app.dif

    def timerFired(app):
        app.timerDelay = 1
        if not app.gameOver:
            if not app.settingsScreen:
                for elem in app.gameObjects: #spawn game pieces
                    try:
                        elem.spawnPiece()
                    except:
                        continue
                if app.jump: #player jump
                    app.player.jump(app)
                if app.moveObjects: #game is unpaused
                    app.ball.move(app)
                    app.bounce()
                    app.player.fall(app)
                    app.checkObjectIntersection()
                if app.terrainMoving and app.wavFile == None: #get data from mic inputs
                    app.barShiftvol()
                elif app.wavFile != None: #get data from audio file
                    app.barShiftFile()
                    app.timerDelay = app.filedelay

            app.checkftimer()
            app.checkmtimer()
            app.checkmousetimer()

            #decrease powerup timers
            if app.ftimer > 0: 
                app.ftimer -= .1
            if app.mtimer > 0:
                app.mtimer -= .1
            if app.mousetimer > 0:
                app.mousetimer -= .1

    def checkftimer(app): 
        #toggles freeze power up
        if app.ftimer > 0 and app.freeze:    
                app.terrainMoving = False
        else:
            app.terrainMoving = True
    
    def checkmtimer(app):
        # toggles magnet power up
        if app.mtimer > 0 and app.magnet:    
                app.magnetize()
    
    def checkmousetimer(app):
        # toggles mouse power up
        if app.mousetimer > 0 and app.mouse:
            app.mouse = True
        else:
            app.mouse = False

    def magnetize(app):
        #magnet power up effect
        for elem in app.gameObjects:
            if isinstance(elem,Target):
                dist = math.sqrt((app.player.x - elem.x)**2 + (app.player.y - elem.y)**2)
                if dist < 200:
                    if elem.x < app.player.x:
                        elem.x += 3
                    if elem.x > app.player.x:
                        elem.x -=3
                    if elem.y < app.player.y:
                        elem.y += 3
                    if elem.y > app.player.y:
                        elem.y -= 3

    def checkObjectIntersection(app):
        #checks player-ball and player-powerup collision

        #player-ball
        balldist = math.sqrt((app.player.x - app.ball.x)**2 + (app.player.y - app.ball.y)**2)
        if balldist < 2*app.ball.r:
            app.lives -= 1
            app.player.jump(app)
            if app.balldx > 0:
                app.player.x += 10
            if app.balldx < 0:
                app.player.x -= 10
            if app.lives == 0:
                app.gameOver = True
                app.prevScore = app.score

        #player-powerup
        for elem in app.gameObjects:
            dist = math.sqrt((app.player.x - elem.x)**2 + (app.player.y - elem.y)**2)
            if dist < 2*elem.r:
                if isinstance(elem,Target):
                    app.score += 1
                    elem.x = random.randint(100,900)
                    elem.y = random.randint(400,800)
                    if app.ball.r < 50:
                        app.ball.r += 10
                else:
                    if elem.spawned:
                        elem.spawned = False
                        if(isinstance(elem, FreezePower)):
                            app.freeze = True
                            app.ftimer = 10.0
                        elif(isinstance(elem, MagnetPower)):
                            app.magnet = True
                            app.mtimer = 10.0
                        elif(isinstance(elem, MousePower)):
                            app.mouse = True
                            app.mousetimer = 10.0
       
    
    def mouseMoved(app,event): 
        #gets mouse coordinates for mouse power
        app.mouseY = 800-event.y
        if app.mouseY > 800:
            app.mouseY = 800

    def getMouse(app):
        #wrapper function for mouse power
        return app.mouseY

    def barShiftvol(app):
        #sets bar height based on volume data from mic
        app.timerDelay = 1
        if app.mouse:
            app.HeightsList.append(app.getMouse())
        elif app.vol:
            app.HeightsList.append(app.showBarVol())
        elif not app.vol:
            app.HeightsList.append(app.showBarPitch())

        try:
            for i in range(app.rects):
                app.bars[i] = app.HeightsList[i]
            app.HeightsList.pop(0)
        except:
                pass  
    
    def barShiftFile(app):
        #sets bar hieght based on volume data from audio files
        app.HeightsList.append(app.fileBars[0]*2)
        app.fileBars.pop(0)
        if len(app.fileBars) != 0:
            try:
                for i in range(app.rects):
                    app.bars[i] = app.HeightsList[i]
                app.HeightsList.pop(0)
            except:
                    pass  
        else:
            app.wavFile = None
            app.nowPlaying = 'Press 1 to load in your own music'

    def setAudioFileData(app):
        #retrieves various data from audio file in order to convert into barheights
        time = 0
        l = getDataLength(app.wavFile)
        time, app.fileBars, app.filedelay = genBarHeights(l,app.wavFile)

    def keyPressed(app,event):
        if event.key == '1': #load in your own audio file to the program
            try:
                app.wavFile = app.getUserInput('input audio file name (wav):')
                app.setAudioFileData()
                app.nowPlaying = app.wavFile
                playaudio = threading.Thread(target=playFile, args = [app.wavFile])
                playaudio.start()
            except:
                app.nowPlaying = 'Error: please make sure your file is spelled correctly and ends in .wav'
                app.wavFile = None
        
        if event.key == 's': #toggle pitch/volume mode
            app.vol = not app.vol
            app.streamControl()
        
        if event.key == 'r': #reset game
            app.gameOver = False
            app.ball.r =  10
            app.lives = 8
            app.score = 0
            app.freeze = False
            app.magnet = False
            app.mouse = False
        
        if event.key == 'g': # God Mode: unlimited mouse power used to test feautres
            app.mouse = True
            app.mousetimer = 1000.0
        
        if event.key == 'f':
            app.freeze = True
            app.ftimer = 10

        if event.key == 'h':
            app.magnet = True
            app.mtimer = 10

        #control the player
        if event.key == 'Right':
            app.player.walk(app,1)
            #https://www.cs.cmu.edu/~112/notes/notes-animations-part3.html
            app.spriteCounter = (1 + app.spriteCounter) % len(app.sprites)
        if event.key == 'Left':
            app.player.walk(app,0)
            #https://www.cs.cmu.edu/~112/notes/notes-animations-part3.html
            app.spriteCounter = (1 + app.spriteCounter) % len(app.sprites)
        if event.key == 'Up':
            app.jump = True  

        #debugging
        if event.key == '8': #freeze all moving objects
            app.moveObjects = not app.moveObjects
        if event.key == '9': #step the terrain generation
            app.barShiftvol()
        if event.key == '0': #step the object movement
            app.ball.move(app)
            app.bounce()
            app.checkObjectIntersection()
        

    
    def mousePressed(app,event):
        #controlls all of the buttons
        if 925<event.x< 975 and 875<event.y<925: #open settings page
            app.settingsScreen = True
        
        if app.settingsScreen: 
            if 300<event.x < 330 and 450 <event.y < 475:
                #up arrow in settings page increase rectangles
                app.rects += 1
                app.bars.append(0)
                app.rectWidth = 800/app.rects
                app.surface = []
                for i in range(app.rects):
                    left = app.rectStartx+app.rectWidth*i
                    top = app.rectStarty-app.bars[i] if app.rectStarty-app.bars[i]>100 else 100
                    right = app.rectStartx + app.rectWidth+app.rectWidth*i
                    app.surface.append((left,top,right,top))
            if 300<event.x <330 and 525< event.y <550:
                #down arrow in settings page decrease rectangles
                app.rects -= 1
                app.bars.append(0)
                app.rectWidth = 800/app.rects
                app.surface = []
                for i in range(app.rects):
                    left = app.rectStartx+app.rectWidth*i
                    top = app.rectStarty-app.bars[i] if app.rectStarty-app.bars[i]>100 else 100
                    right = app.rectStartx + app.rectWidth+app.rectWidth*i
                    app.surface.append((left,top,right,top))

            #powerup on/off switches
            if 625<event.x<775 and 400-15<event.y<415:
                app.hasFreeze = not app.hasFreeze
                if not app.hasFreeze:
                    app.gameObjects.remove(app.freezeObj)
                else:
                    app.gameObjects.append(app.freezeObj)
            if 625<event.x<775 and 450-15<event.y<450+15:
                app.hasMag = not app.hasMag
                if not app.hasMag:
                    app.gameObjects.remove(app.magnetObj)
                else:
                    app.gameObjects.append(app.magnetObj)
            if 625<event.x<775 and 500-15<event.y<515:
                app.hasMouse = not app.hasMouse
                if not app.hasMouse:
                    app.gameObjects.remove(app.mouseObj)
                else:
                    app.gameObjects.append(app.mouseObj)
            
            #play button
            if 450<event.x<550 and 550<event.y<590:
                app.settingsScreen = False

    def streamControl(app):
        #stop and end the current stream and instance of pyaudio
        app.stream.stop_stream()
        app.stream.close()
        app.p.terminate()

        if app.vol:
            #open stream with 16bit int data for volume
            app.p=pyaudio.PyAudio()
            app.stream=app.p.open(format=pyaudio.paInt16,
                channels=1,rate=44100,input = True,
                frames_per_buffer=1024)
        else:
            #open stream with 32bit float data for aubio pitch detection
            app.p = pyaudio.PyAudio()
            app.stream = app.p.open(format=pyaudio.paFloat32,
                channels=1, rate=44100, input=True,
                frames_per_buffer=4096)

    def drawRects(app,canvas):
        #draws the rectangles that make up the terrain
        for i in range(app.rects):
            left = app.rectStartx+app.rectWidth*i
            top = app.rectStarty-app.bars[i] if app.rectStarty-app.bars[i]>150 else 150
            right = app.rectStartx + app.rectWidth+app.rectWidth*i
            bottom =  app.rectStarty+20
            canvas.create_rectangle(left, top , right, bottom
                                   ,fill = 'brown',outline = 'brown')

            # code below smooths the curve, each smoothing line coords are appended to a list representing the surface
            if i == 0 or i == app.rects-1: #first and last bar
                app.surface.append((left,top,right,top))
                app.surface.pop(0)
            elif app.rectStarty-app.bars[i-1] < top < app.rectStarty-app.bars[i+1]: #if the left bar is higher and the right bar is lower
                canvas.create_line(left,app.rectStarty-app.bars[i-1] if app.rectStarty-app.bars[i-1]>150 else 150,right,top)
                canvas.create_polygon(left,app.rectStarty-app.bars[i-1] if app.rectStarty-app.bars[i-1]>150 else 150,right,top,left,top,fill = 'brown',outline = 'brown')
                app.surface.append((left,app.rectStarty-app.bars[i-1] if app.rectStarty-app.bars[i-1]>150 else 150,right,top))
                app.surface.pop(0)
            elif app.rectStarty-app.bars[i-1] > top > app.rectStarty-app.bars[i+1]: #if the right bar is higher and the left bar is lower
                canvas.create_line(left,top,right,app.rectStarty-app.bars[i+1] if app.rectStarty-app.bars[i+1]>150 else 150)
                canvas.create_polygon(left,top,right,app.rectStarty-app.bars[i+1] if app.rectStarty-app.bars[i+1]>150 else 150,right,top, fill = 'brown', outline = 'brown')
                app.surface.append((left,top,right,app.rectStarty-app.bars[i+1] if app.rectStarty-app.bars[i+1]>150 else 150))
                app.surface.pop(0)
            elif app.rectStarty-app.bars[i-1] < top > app.rectStarty-app.bars[i+1]: #if bars on both sides are higher
                canvas.create_line(left,app.rectStarty-app.bars[i-1] if app.rectStarty-app.bars[i-1]>150 else 150,right-app.rectWidth//2,top)
                canvas.create_polygon(left,app.rectStarty-app.bars[i-1] if app.rectStarty-app.bars[i-1]>150 else 150,right-app.rectWidth//2,top,left,top,fill = 'brown', outline = 'brown')
                app.surface.append((left,app.rectStarty-app.bars[i-1] if app.rectStarty-app.bars[i-1]>150 else 150,right-app.rectWidth//2,top,left+app.rectWidth//2,top,right,app.rectStarty-app.bars[i+1] if app.rectStarty-app.bars[i+1]>150 else 150))
                app.surface.pop(0)
                canvas.create_line(left+app.rectWidth//2,top,right,app.rectStarty-app.bars[i+1] if app.rectStarty-app.bars[i+1]>150 else 150)
                canvas.create_polygon(left+app.rectWidth//2,top,right,app.rectStarty-app.bars[i+1] if app.rectStarty-app.bars[i+1]>150 else 150,right,top, fill = 'brown', outline = 'brown')
            else: #no height difference
                app.surface.append((left,top,right,top))
                app.surface.pop(0)

    def drawSurface(app,canvas):
        #draws the surface representation; use for debugging only
        try:
            for i in range(len(app.surface)):
                if len(app.surface[i]) == 4:
                    (x0,y0,x1,y1) = app.surface[i]
                    canvas.create_line(x0,y0,x1,y1, width = 10)
                else:
                    (x0,y0,x1,y1,x2,y2,x3,y3) = app.surface[i]
                    canvas.create_line(x0,y0,x1,y1, width = 10) 
                    canvas.create_line(x2,y2,x3,y4, width = 10)
        except:
            pass
   
    def drawSlider(app,canvas):
        #draws all of the features underneath the game window
        canvas.create_line (100,900,300,900, fill = 'black')
        canvas.create_line (700,900,900,900, fill = 'black')
        canvas.create_rectangle(300,850,700,950)
        canvas.create_text(305,950, text = f'Previous score: {app.prevScore}', anchor = 'sw', font = 'ariel 12')
        canvas.create_text(305,850, text = 'Currently Playing:', anchor = 'nw', font = 'ariel 12')
        canvas.create_text(500,880, text = f'{app.nowPlaying}')
        canvas.create_text(695,935, text = 'press s to toggle', anchor = 'se')
        if app.vol:
            canvas.create_text(695,950, text = 'Mode: Volume', anchor = 'se')
        else:
            canvas.create_text(695,950, text = 'Mode: Pitch', anchor = 'se')
        
    def drawPieces(app,canvas):
        #draw game Pieces
        for elem in app.gameObjects:
            elem.drawPiece(app,canvas)

    def drawTimers(app,canvas):
        #draw powerup timers, score, and lives
        if app.hasFreeze:
            if app.ftimer>0:
                canvas.create_text(100,830,text = f'Freeze: On {app.ftimer}', anchor = 'nw', fill = 'green', font = 'ariel 10')
            else:
                canvas.create_text(100,830,text = "Freeze: Off", anchor = 'nw', fill = 'red', font = 'ariel 10')
        else:
            canvas.create_text(100,830,text = f'Freeze: disabled', anchor = 'nw', fill = 'black', font = 'ariel 10')
        if app.hasMag:
            if app.mtimer>0:
                canvas.create_text(100,850,text = f'Magnet: On {app.mtimer}', anchor = 'nw', fill = 'green', font = 'ariel 10')
            else:
                canvas.create_text(100,850,text = "Magnet: Off", anchor = 'nw', fill = 'red', font = 'ariel 10')
        else:
            canvas.create_text(100,850,text = "Magnet: disabled", anchor = 'nw', fill = 'black', font = 'ariel 10')
        if app.hasMouse:
            if app.mousetimer>0:
                canvas.create_text(100,870,text = f"Mouse Mode: On {app.mousetimer}", anchor = 'nw', fill = 'green', font = 'ariel 10')
            else:
                canvas.create_text(100,870,text = "Mouse Mode: Off", anchor = 'nw', fill = 'red', font = 'ariel 10')
        else:
            canvas.create_text(100,870,text = "Mouse Mode: disabled", anchor = 'nw', fill = 'black', font = 'ariel 10')
        canvas.create_text(100,100, text = f'Score: {app.score}', anchor = 'sw', font = 'ariel')
        canvas.create_text(900,100, text = f'lives: {app.lives}', anchor = 'se', font = 'ariel')


    def drawsettingsPage(app,canvas):
        #draws the settings page

            #screen
            canvas.create_rectangle(200,300,800,600, fill = 'white')
            canvas.create_text(500,310, text = 'Setup Page', font = 'ariel 18', anchor = 'n')
            canvas.create_text(315, 400, text = "# of Rectangles", font = 'ariel 20')
            #playbutton
            canvas.create_rectangle(450,550,550,590, fill = 'red')
            canvas.create_text(500,570, text = 'PLAY', font = 'ariel 20')
            #rectangle setting components
            canvas.create_polygon(300, 475, 330, 475, 315, 450, fill = 'black')
            canvas.create_text(315, 500, text = f'{app.rects}', font = 'ariel 20')
            canvas.create_polygon(300,525, 330, 525, 315, 550, fill = 'black')
            #powerup toggles
            canvas.create_text(545,400, text = 'Freeze Power:', font = 'ariel 17')
            canvas.create_text(545,450, text = 'Magnet Power:', font = 'ariel 17')
            canvas.create_text(545,500, text = 'Mouse Power:', font = 'ariel 17')
            if app.hasFreeze:
                canvas.create_image(700, 400, image = ImageTk.PhotoImage(app.onImage))
            else:
                canvas.create_image(700, 400, image = ImageTk.PhotoImage(app.offImage))

            if app.hasMag:
                canvas.create_image(700, 450, image = ImageTk.PhotoImage(app.onImage))
            else:
                canvas.create_image(700, 450, image = ImageTk.PhotoImage(app.offImage))

            if app.hasMouse:
                canvas.create_image(700, 500, image = ImageTk.PhotoImage(app.onImage))
            else:
                canvas.create_image(700, 500, image = ImageTk.PhotoImage(app.offImage))

    def redrawAll(app,canvas):
        #background, game window, settings icon
        canvas.create_image(500,500, image = ImageTk.PhotoImage(app.gameBackGroundImage))    
        canvas.create_rectangle(100,100,900,820, fill = 'cyan')
        canvas.create_image(950,900, image = ImageTk.PhotoImage(app.settingsImage))
        #everyting else
        app.player.draw(app,canvas)
        app.drawPieces(canvas)
        if not app.settingsScreen:
            app.drawRects(canvas)
        app.drawSlider(canvas)
        app.ball.draw(canvas)
        app.drawTimers(canvas)
        if app.settingsScreen:
            app.drawsettingsPage(canvas)
        if app.gameOver:
            canvas.create_text(500,500,text =' GAME OVER!!!', font= 'ariel 30', fill = 'red')
            canvas.create_text(500,600,text = 'press r to restart', font = 'ariel 25', fill = 'red')


class MyModalApp(ModalApp):
    def appStarted(app):
        app.GameMode = GameMode()
        app.MenuMode = MenuMode()
        app.HelpMode = HelpMode()
        app.setActiveMode(app.MenuMode)

app = MyModalApp(width = 1000, height = 1000)



