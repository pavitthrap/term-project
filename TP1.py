#!/usr/bin/env python

from direct.showbase.ShowBase import ShowBase 
from direct.task.Task import Task
from random import randint, choice, random
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
import math
import sys,os
import colorsys
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.interval.LerpInterval import *
import time



class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        #color setup
        self.r,self.g,self.b=20,32,15
        self.startColor=[0,0,self.r,self.g,self.b]
        self.endR,self.endG,self.endB=5,0,0
        self.endColor=[0,0,1,0,0]
        self.percentage=.001
        self.redDecrement=(self.r-self.endR) * self.percentage
        self.greenDecrement=(self.g-self.endG) * self.percentage
        self.blueDecrement=(self.b-self.endB) * self.percentage
        
        #load background, objects
        self.loadBackground()
        self.loadBB8()
        
        #define movement and interaction
        self.defineIntervals()
        self.createKeyControls()
        self.createKeyControls()
        self.keyMap = {'left':0, 'right':0, 'up':0, 'down':0, 'counter':0, 'clock':0}

        #position camera 
        self.camera.setPos(0,0,0)
        self.x,self.y,self.z=0,0,0

        #timer functions
        timer=.5
        taskMgr.doMethodLater(timer,self.move, "move") #change val in stirng?
        taskMgr.doMethodLater(timer,self.changeColorTask, "move")
    
    def setKey(self, key, value):
    	self.keyMap[key]=value 

    def createKeyControls(self):
    	self.accept('l',self.setKey, ['counter',1])
    	self.accept('r',self.setKey, ['clock',1])
    	self.accept('arrow_up',self.setKey, ['up',1])
    	self.accept('arrow_down',self.setKey, ['down',1])
    	self.accept('arrow_left',self.setKey, ['left',1])
    	self.accept('arrow_right',self.setKey,['right',1])
    	
    	# stop moving on key release
    	self.accept('arrow_up-up',self.setKey, ['up',0])
    	self.accept('arrow_down-up',self.setKey, ['down',0])
    	self.accept('arrow_left-up',self.setKey, ['left',0])
    	self.accept('arrow_right-up',self.setKey, ['right',0])
    	self.accept('l-up',self.setKey, ['counter',0])
    	self.accept('r-up',self.setKey, ['clock',0])

    ############TASKS################
    def changeColorTask(self,task):
    	if int(self.r)>self.endR:
	    	self.r=self.r-self.redDecrement
	    	self.g=self.g-self.greenDecrement
	    	self.b=self.b-self.blueDecrement
	    	div=max(self.r,self.g,self.b)
	    	intR,intG,intB=(self.r/div),(self.g/div),(self.b/div)
	    	currColor=[intR, intG, intB]
    	else:
    		currColor=self.endColor
    	self.teapot.setColor(*currColor) #consider setColorScale
	   
    	return Task.cont

    def move (self,task): 
    	inc=1
    	if self.keyMap['up']>0:
    		(dx,dy,dz)=(0,inc, 0)
    	elif self.keyMap['down']>0:
    		(dx,dy,dz)=(0,-inc, 0)
    		self.teapot.setColor(*self.endColor)
    	elif self.keyMap['left']>0:
    		(dx,dy,dz)=(-inc,0,0)
    	elif self.keyMap['right']>0:
    		(dx,dy,dz)=(inc,0,0)
    	elif self.keyMap['counter']>0:
    		(dx,dy,dz)=(0,0,inc)
    	elif self.keyMap['clock']>0:
    		(dx,dy,dz)=(0,0,-inc)
    	else:
    		(dx,dy,dz)=(0,0,0)

    	(self.x,self.y,self.z)=self.x+dx,self.y+dy,self.z+dz
    	#camera angle documentation 
    	#https://www.panda3d.org/manual/index.php/Controlling_the_Camera
    	self.camera.setHpr(self.x,self.y,self.z)
    	self.dlnp.setHpr(self.x,self.y,self.z)
    	
    	return task.cont
    
    def defineIntervals(self):
    	self.teapotTurnInterval= Sequence(
    		self.teapot.hprInterval(.3, (0,50,0)), #try changing this stuff
    		self.teapot.hprInterval(2,(20,-30,0))
    		)

    def createMovementLoop(self):
    	loop = Parallel(
    		self.teapotTurnInterval,
    		)
    	loop.start()

    def loadBackground(self):
    	#lighting documentation 
    	#https://www.panda3d.org/manual/index.php/Lighting#Ambient_Lights
    	
    	#point light
    	plight1= PointLight('plight')
    	plight1.setColor(VBase4(1,40,1,1))
    	plight1NodePath=render.attachNewNode(plight1)
    	plight1NodePath.setPos(0,0,500)  
    	render.setLight(plight1NodePath)

    	plight2= PointLight('plight')
    	plight2.setColor(VBase4(10,70,16,1))
    	plight2NodePath=render.attachNewNode(plight2)
    	plight2NodePath.setPos(0,500,500) #try changing these values 
    	render.setLight(plight2NodePath)
    	
    	#directional light
    	dlight1 = DirectionalLight('dlight1')
    	dlight1.setColor(VBase4(1,1,1,1))
    	self.dlnp = render.attachNewNode(dlight1)
    	self.dlnp.setHpr(0,0,0)
    	render.setLight(self.dlnp)

    	dlight2 = DirectionalLight('dlight2')
    	dlight2.setColor(VBase4(1,1,1,1))
    	self.dlnp2 = render.attachNewNode(dlight2)
    	self.dlnp2.setHpr(180,180,0)
    	render.setLight(self.dlnp2)

    	#ambient light
    	ambientL=AmbientLight('ambientL')
    	ambientL.setColor(VBase4(0.2,0.2,0.2,1))
    	alnp = render.attachNewNode(ambientL)
    	render.setLight(alnp)

    	self.setBackgroundColor((0, 0, 0, 1))

    
    def loadBB8(self):
    	self.teapot = loader.loadModel('glaxyTry')
    	self.teapot.reparentTo(self.render) 
    	self.teapot.setPos (0,10,0)
    	self.teapot.setColor(*self.startColor)
    	#set texture 
    	#texture1 = loader.loadTexture('textures/randomTexture.png')


app=MyApp()
app.run()

