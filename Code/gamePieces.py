#this file contains the code that creates all of the game pieces:
#ball, player, target, powerups

import random
from cmu_112_graphics import *

class Ball(object):
    def __init__(self, x, y,r):
        self.x = x
        self.y = y
        self.r = r #radius

    def draw(self, canvas):
        canvas.create_oval(self.x-self.r,self.y-self.r,self.x+self.r,self.y+self.r, fill = 'red')
    
    def move(self,app):
        #move the ball

        #max horizontal ball speed cap
        self.x += app.balldx
        if app.balldx > 100:
            app.balldx = 50
        elif app.balldx < -100:
            app.balldx = -50       

        #gravity simulation (g = 9.8 m/s^2)
        self.y += app.vel*app.dy
        app.vel = app.vel + 9.8*app.dy
        if self.x + self.r >= 900:
            self.x = 900 - self.r
            app.balldx *= -1
        if self.x - self.r <= 100:
            self.x = 100 + self.r
            app.balldx *= -1
        if self.y < 100:
            self.y = 100
            app.vel *= -1

class Player(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.h = 20 #height
        self.w = 6 #width
        self.dirR = True #True = right;False = left
    
    def draw(self, app, canvas):
        #use a run cycle/sprite sheet to animate running
        sprite = app.sprites[app.spriteCounter]
        if self.dirR:
            canvas.create_image(self.x, self.y-24, image=ImageTk.PhotoImage(sprite))
        else:
            sprite = sprite.transpose(Image.FLIP_LEFT_RIGHT)
            canvas.create_image(self.x, self.y-24, image=ImageTk.PhotoImage(sprite))
    
    def fall(self, app):
        #calculates falling velocity and position for player bounded by surface
        if self.y < 800:
            self.y += app.pvel*app.pdy
            app.pvel = app.pvel + 9.8*app.pdy
            app.jump = False
        if self.y >800:
            self.y = 800
            app.pvel = 40
        
        for i in range(len(app.surface)):
            if len(app.surface[i]) == 4:
                x0,y0,x1,y1 = app.surface[i]
                m = (y1-y0)/(x1-x0)
                ybound = m*(self.x - x1) + y1
                if x0 < self.x <= x1:
                    if self.y > ybound:
                        self.y = ybound
                        app.pvel = 40            
            elif len(app.surface[i]) == 8:
                x0,y0,x1,y1,x2,y2,x3,y3 = app.surface[i]
                if x0<= self.x <=x1:
                    m = (y1-y0)/(x1-x0)
                    ybound = m*(self.x - x1) + y1
                    if self.y > ybound:
                        self.y = ybound
                        app.pvrl = 40
                if x2< self.x <=x3:
                    m = (y3-y2)/(x3-x2)
                    ybound = m*(self.x - x2) + y2
                    if self.y > ybound:
                        self.y = ybound
                        app.pvrl = 40
                


    def walk(self,app,dirx):
        #move the player
        if dirx == 1: #to the right
            self.x += 10
            self.dirR = True
            if self.x >= 880:
                self.x -= 10
        else:  #to the left
            self.x -= 10
            self.dirR = False
            if self.x < 120:
                self.x += 10

    def jump(self, app):
        app.pvel *= -1
        self.y += app.pvel*app.pdy
        app.pvel = app.pvel + 9.8*app.pdy

class GamePiece(object):
    #game pieces parent class
    
    def __init__(self):
        #randomize location
        self.x = random.randint(100,900)
        self.y = random.randint(400,800)
        self.r = 12

    def spawnPiece(self):
        #spawn/despawn the piece on the board at a random time and random place
        correct = 10
        test = random.randint(0,100)
        if correct == test:
            self.spawned = not self.spawned
            self.x = random.randint(170,820)
            self.y = random.randint(400,800)
          

class Target(GamePiece):
    #Target piece

    def __init__(self):
        super().__init__()

    def drawPiece(self, app,canvas):
            canvas.create_oval(self.x-self.r,self.y-self.r,self.x+self.r,self.y+self.r, fill = 'red')
            canvas.create_oval(self.x-0.75*self.r,self.y-0.75*self.r,self.x+0.75*self.r,self.y+0.75*self.r, fill = 'white')
            canvas.create_oval(self.x-0.5*self.r,self.y-0.5*self.r,self.x+0.5*self.r,self.y+0.5*self.r, fill = 'red')
            canvas.create_oval(self.x-0.25*self.r,self.y-0.25*self.r,self.x+0.25*self.r,self.y+0.25*self.r, fill = 'white')

class FreezePower(GamePiece):
    #freeze power piece

    def __init__(self):
        super().__init__()
        self.spawned = False

    def drawPiece(self,app,canvas):
        if self.spawned == True:
            canvas.create_image(self.x, self.y, image = ImageTk.PhotoImage(app.freezePowerImage))

class MagnetPower(GamePiece):
    #magnet power piece

    def __init__(self):
        super().__init__()
        self.spawned = False

    def drawPiece(self,app,canvas):
        if self.spawned == True:
            canvas.create_image(self.x,self.y, image = ImageTk.PhotoImage(app.magnetPowerImage))

class MousePower(GamePiece):
    #mouse power piece

    def __init__(self):
        super().__init__()
        self.spawned = False

    def drawPiece(self,app,canvas):
        if self.spawned == True:
            canvas.create_image(self.x, self.y, image = ImageTk.PhotoImage(app.mousePowerImage))