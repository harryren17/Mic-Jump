#this file contains the code for the menu screen and help screen

from cmu_112_graphics import *
import pyaudio
import numpy as np

class MenuMode(Mode):
    #main menu

    def appStarted(mode):
        #variables borrowed from main file used for the audio visualization
        mode.rects = 50
        mode.bars = [0]*mode.rects
        mode.barHeight = 10
        mode.HeightsList = []
        mode.rectStartx = 250
        mode.rectStarty = 500
        mode.rectWidth = 500/mode.rects
        mode.sens = 1
        mode.timerDelay = 1
        mode.p=pyaudio.PyAudio()
        mode.stream=mode.p.open(format=pyaudio.paInt16,channels=1,rate=44100,input = True,
              frames_per_buffer=1024)

        #images
        mode.backgroundImage = mode.scaleImage(mode.loadImage('background.jpg'), 3)
        mode.settingsIcon = mode.scaleImage(mode.loadImage('settings.png'),1/3)
        mode.playButtonIcon = mode.scaleImage(mode.loadImage('playbutton.png'),1)
        mode.helpButtonIcon = mode.scaleImage(mode.loadImage('helpbutton.png'),1)

    def keyPressed(mode,event):
        if event.key == 'p': #play game
            mode.app.setActiveMode(mode.app.GameMode)
        if event.key == 'h': #help screen
            mode.app.setActiveMode(mode.app.HelpMode)
    
    def mousePressed(mode,event):
        #play button
        if 500-125 < event.x < 500+125 and 700-50< event.y < 700+50:
            mode.app.setActiveMode(mode.app.GameMode)
        #help button
        if 500-125 < event.x < 500+125 and 900-50< event.y < 900+50:
            mode.app.setActiveMode(mode.app.HelpMode)

    def showBarVol(app): 
        #borrowed from main file used for the audio visualization 
        data = np.frombuffer(app.stream.read(2**10),dtype=np.int16)
        peak=np.average(np.abs(data))*2
        bar = int(peak)
        return app.sens*100*bar/2**10

    def barShiftvol(mode):
        #borrowed from main file used for the audio visualization
        mode.timerDelay = 1
        mode.HeightsList.append(mode.showBarVol())
        try:
            for i in range(mode.rects):
                mode.bars[i] = mode.HeightsList[i]
            mode.HeightsList.pop(0)
        except:
                pass  
        
    def drawRects(mode,canvas):
        #borrowed from main file used for the audio visualization
        for i in range(mode.rects):
            left = mode.rectStartx+mode.rectWidth*i
            top = mode.rectStarty-mode.bars[i] if mode.rectStarty-mode.bars[i]>400 else 400
            right = mode.rectStartx + mode.rectWidth+mode.rectWidth*i
            bottom =  mode.rectStarty
            canvas.create_rectangle(left, top , right, bottom
                                   ,fill = 'brown',outline = 'brown')
            if i == 0 or i == mode.rects-1:
                pass
            elif mode.rectStarty-mode.bars[i-1] < top < mode.rectStarty-mode.bars[i+1]: #if the left bar is higher and the right bar is lower
                canvas.create_line(left,mode.rectStarty-mode.bars[i-1] if mode.rectStarty-mode.bars[i-1]>400 else 400,right,top)
                canvas.create_polygon(left,mode.rectStarty-mode.bars[i-1] if mode.rectStarty-mode.bars[i-1]>400 else 400,right,top,left,top,fill = 'brown',outline = 'brown')

            elif mode.rectStarty-mode.bars[i-1] > top > mode.rectStarty-mode.bars[i+1]: #if the right bar is higher and the left bar is lower
                canvas.create_line(left,top,right,mode.rectStarty-mode.bars[i+1] if mode.rectStarty-mode.bars[i+1]>400 else 400)
                canvas.create_polygon(left,top,right,mode.rectStarty-mode.bars[i+1] if mode.rectStarty-mode.bars[i+1]>400 else 400,right,top, fill = 'brown', outline = 'brown')

            elif mode.rectStarty-mode.bars[i-1] < top > mode.rectStarty-mode.bars[i+1]: #if bars on both sides are higher
                canvas.create_line(left,mode.rectStarty-mode.bars[i-1] if mode.rectStarty-mode.bars[i-1]>400 else 400,right-mode.rectWidth//2,top)
                canvas.create_polygon(left,mode.rectStarty-mode.bars[i-1] if mode.rectStarty-mode.bars[i-1]>400 else 400,right-mode.rectWidth//2,top,left,top,fill = 'brown', outline = 'brown')

                canvas.create_line(left+mode.rectWidth//2,top,right,mode.rectStarty-mode.bars[i+1] if mode.rectStarty-mode.bars[i+1]>400 else 400)
                canvas.create_polygon(left+mode.rectWidth//2,top,right,mode.rectStarty-mode.bars[i+1] if mode.rectStarty-mode.bars[i+1]>400 else 400,right,top, fill = 'brown', outline = 'brown')

    def drawBotRects(mode,canvas):
        #borrowed from main file used for the audio visualization
        #adapted to draw below the centerline
        for i in range(mode.rects):
            left = mode.rectStartx+mode.rectWidth*i
            top = mode.rectStarty
            right = mode.rectStartx + mode.rectWidth+mode.rectWidth*i
            bottom =  mode.rectStarty+mode.bars[i] if mode.rectStarty+mode.bars[i]<600 else 600
            canvas.create_rectangle(left, top , right, bottom
                                   ,fill = 'brown',outline = 'brown')
            if i == 0 or i == mode.rects-1:
                pass
            elif mode.rectStarty+mode.bars[i-1] > bottom > mode.rectStarty+mode.bars[i+1]: #if the left bar is higher and the right bar is lower
                canvas.create_line(left,mode.rectStarty+mode.bars[i-1] if mode.rectStarty+mode.bars[i-1]<600 else 600,right,bottom)
                canvas.create_polygon(left,mode.rectStarty+mode.bars[i-1] if mode.rectStarty+mode.bars[i-1]<600 else 600,right,bottom,left,bottom,fill = 'brown',outline = 'brown')

            elif mode.rectStarty+mode.bars[i-1] < bottom < mode.rectStarty+mode.bars[i+1]: #if the right bar is higher and the left bar is lower
                canvas.create_line(left,bottom,right,mode.rectStarty+mode.bars[i+1] if mode.rectStarty+mode.bars[i+1]<600 else 600)
                canvas.create_polygon(left,bottom,right,mode.rectStarty+mode.bars[i+1] if mode.rectStarty+mode.bars[i+1]<600 else 600,right,bottom, fill = 'brown', outline = 'brown')

            elif mode.rectStarty+mode.bars[i-1] > bottom < mode.rectStarty+mode.bars[i+1]: #if bars on both sides are higher
                canvas.create_line(left,mode.rectStarty+mode.bars[i-1] if mode.rectStarty+mode.bars[i-1]<600 else 600,right-mode.rectWidth//2,bottom)
                canvas.create_polygon(left,mode.rectStarty+mode.bars[i-1] if mode.rectStarty+mode.bars[i-1]<600 else 600,right-mode.rectWidth//2,bottom,left,bottom,fill = 'brown', outline = 'brown')

                canvas.create_line(left+mode.rectWidth//2,bottom,right,mode.rectStarty+mode.bars[i+1] if mode.rectStarty+mode.bars[i+1]<600 else 600)
                canvas.create_polygon(left+mode.rectWidth//2,bottom,right,mode.rectStarty+mode.bars[i+1] if mode.rectStarty+mode.bars[i+1]<600 else 600,right,bottom, fill = 'brown', outline = 'brown')

    def timerFired(mode):
        mode.barShiftvol()

    def redrawAll(mode,canvas):
        canvas.create_image(500,500, image = ImageTk.PhotoImage(mode.backgroundImage))
        canvas.create_image(500,700, image = ImageTk.PhotoImage(mode.playButtonIcon))
        canvas.create_image(500,900, image = ImageTk.PhotoImage(mode.helpButtonIcon))
        mode.drawRects(canvas)
        mode.drawBotRects(canvas)
        canvas.create_text(500,200,text = 'Mic-Jump', font = 'ariel 100', fill = 'white')

class HelpMode(Mode):
    #Help Page

    def appStarted(mode):
        mode.screen = mode.scaleImage(mode.loadImage('helpscreen.png'),1)

    def keyPressed(mode,event):
        #play game
        if event.key == 'p':
            mode.app.setActiveMode(mode.app.GameMode)

    def redrawAll(mode,canvas):
        canvas.create_rectangle(0,0,1000,1000, fill = 'cyan')
        canvas.create_image(500,500,image = ImageTk.PhotoImage(mode.screen))
