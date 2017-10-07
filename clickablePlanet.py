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
from pandac.PandaModules import *
import direct.directbase.DirectStart 
#for the events 

#for collision stuff 
from pandac.PandaModules import * 

#https://www.panda3d.org/manual/index.php/Configuring_Panda3D
winWidth, winHeight = 960, 720
loadPrcFileData('', 'win-size %d %d' % (winWidth,winHeight))


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        #color setup for galaxies
        self.r,self.g,self.b=20,32,15
        self.startColor=[0,0,self.r,self.g,self.b]
        self.endR,self.endG,self.endB=5,0,0
        self.endColor=[0,0,1,0,0]
        self.percentage=.001
        self.redDecrement=(self.r-self.endR) * self.percentage
        self.greenDecrement=(self.g-self.endG) * self.percentage
        self.blueDecrement=(self.b-self.endB) * self.percentage
        
        #planet setup 
        self.planetColor = [0,0,3,2,1]

        #load background, objects
        self.uniTime=0
        self.loadBackground()
        #load galaxies
        self.loadMiddleModel()
        self.galaxies={}
        step,self.counter = 1,1 
        self.loadGalaxies(step)
        #load planet
        self.planetYOffset, self.planetZOffset = 1.8, -.8
        self.loadPlanets()
        #make 2d elements
        self.makeHomeScreen()
        #self.createGUI()
        #self.drawMenu()
        
        #define movement and interaction
        self.defineIntervals()
        self.createKeyControls()
        self.createKeyControls()
        self.keyMap = {'left':0, 'right':0, 'up':0, 'down':0, 'counter':0, 'clock':0}

        #3D Object Clicking 
        mousePicker = Picker()
        mousePicker.makePickable(self.planet)

        #position camera 
        self.camera.setPos(0,0,0)
        self.x,self.y,self.z=0,0,0
        #base.disableMouse() 
        #^don't want camera to move

        #play music
        #https://www.panda3d.org/manual/index.php/Loading_and_Playing_Sounds_and_Music
        self.spaceMusic = base.loader.loadSfx('spaceMusic.ogg')
        self.spaceMusic.play()
        self.spaceMusic.setVolume(0.3)
        #self.spaceMusic.pause ##may want to use in help menu?? if mySound.status() == mySound.PLAYING: 

        pText='this is a demo'
        self.textObject= OnscreenText(text=pText, pos=(.3,.4), scale=.07, fg=(1,.5,.5,1), align=TextNode.ACenter, mayChange=1)

        #timer functions
        timer=.5
        #change user perspective
        taskMgr.doMethodLater(timer,self.move, "move")
        #color algorithm
        taskMgr.doMethodLater(timer,self.changeColorTask, "move")
        #change time scaler

        #keep planet in view 
        self.planetP = 0
        self.planetPInc = .1
        taskMgr.doMethodLater(timer, self.rotatePlanet, 'move')
        ###################

    
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

        self.accept('escape', sys.exit)

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
    
    def rotatePlanet(self,task):
        self.planetP+=self.planetPInc
        self.planet.setHpr(0, self.planetH, 0)
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


    ########## Background/Foreground ####################
    def makeHomeScreen(self):
        #WANT TO DISABLE MOUSE + KEY STUFF
        displayRegion = base.win.makeDisplayRegion()
        camNode = Camera('cam')
        camNP = NodePath(camNode)
        displayRegion.setCamera(camNP)

        #want separate render here
        camNP.reparentTo(base.camera)
        '''
        render2 = NodePath('render2')
        camNP.reparentTo(render2)
        env = loader.loadModel('models/environment')
        env.reparentTo(render2)
        '''
        # disable default display
        dr = base.camNode.getDisplayRegion(0)
        dr.setActive(0)

        pText='KAZOO'
        textObject= OnscreenText(text=pText, pos=(.2,.4), scale=.07, fg=(1,.5,.5,1), align=TextNode.ACenter, mayChange=1)


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
    ################# Draw Galaxies #####################
    def loadGalaxies(self, step):
        check = self.getGalaxyLayer(step)
        if check==True:
            self.loadGalaxies(step+1)
        #else do nothing and end func
    
    def getGalaxyLayer(self, step):
        try:
            positionSet = set()
            for pos in range(3):
                for stepTry in [-step,step]: #does this work?
                    name = 'gal' + str(self.counter)
                    position = [0*pos] + [stepTry]
                    position += [0*(3-len(position))] 
                    self.loadGalaxy(name,position)
                    positionSet.add(tuple(position))
                    print('position')
                    self.counter+=1
            result = self.permutePositions(step, positionSet)
            return result
        except:
            print('failed')
            return False
    
    def permutePositions(self,step, positionSet):
        for first in [-step,0,step]:
            for second in [-step,0,step]:
                for third in [-step,0,step]:
                    position = (first,second,third)
                    name = 'gal' + str(self.counter)
                    if position not in positionSet:
                        try:
                            self.loadGalaxy(name,position)
                            self.counter+=1
                            positionSet.add(position)
                        except:
                            return False 
        return True

    def loadGalaxy(self,name,position):
        self.galaxies[self.counter]=loader.loadModel('galaxies/%s' %(name))
        self.galaxies[self.counter].reparentTo(self.render)
        xyzPos = [i*10 for i in position]
        print(xyzPos)
        self.galaxies[self.counter].setPos(*xyzPos)
        self.galaxies[self.counter].setColor(*self.startColor)

    def loadMiddleModel(self):
    	self.teapot = loader.loadModel('galaxies/gal')
    	self.teapot.reparentTo(self.render) 
    	self.teapot.setPos (0,0,0)
    	self.teapot.setColor(*self.startColor)
    	#set texture 
    	#texture1 = loader.loadTexture('textures/randomTexture.png')

    ################## Draw Planets ###################
    def loadPlanets(self): # place planet in curr galaxy - which would actually just be the thing in center
        try: 
            self.planet = loader.loadModel('modelsMisc/planet3Small')
            self.planet.reparentTo(self.render)
            self.planet.reparentTo(base.camera)
            #self.planet.setPos(0,1.6,-.8) 
            self.planet.setPos(0,self.planetYOffset,self.planetZOffset)
            self.planet.setColor(*self.endColor)
            #self.planet.setTag('planet', '1')
            #load texture?
            print('loaded planet')
        except:
            print('failed to load planet')
   
    ############## Unused Code ##################
    #https://www.panda3d.org/manual/index.php/The_2D_Display_Region
    #https://www.panda3d.org/manual/index.php/DirectGUI
    def createGUI(self):
        self.dr = win.makeDisplayRegion()
        self.dr.setSort(20) 
        
        myCamera2d = NodePath(Camera('myCam2d'))
        lens = OrthographicLens()
        lens.setFilmSize(2,2)
        lens.setNearFar(-1000,1000)
        myCamera2d.node().setLens(lens)

        myRender2d = NodePath('myRender2d')
        myRender2d.setDepthTest(False)
        myRender2d.setDepthWrite(False)
        myCamera2d.reparentTo(myRender2d)
        self.dr.setCamera(myCamera2d)

        #create aspect 2d node for clicks
        aspectRation=base.getAspectRatio()
        myAspect2d=myRender2d.attachNewNode(PGTop('myAspect2d'))
        myAspect2d.setScale(1.0 / aspectRatio, 1.0, 1.0)
        myAspect2d.node().setMouseWatcher(base.mouseWatcherNode)

    def drawMenu(self):
        pText='this1 is a demo1'
        textObject= OnscreenText(text=pText, pos=(.3,.4), scale=.07, fg=(1,.5,.5,1), align=TextNode.ACenter, mayChange=1)


#https://www.panda3d.org/manual/index.php?title=Example_for_Clicking_on_3D_Objects&oldid=3196
class Picker (DirectObject.DirectObject):
    def __init__(self):
        self.picker = CollisionTraverser()
        self.queue = CollisionHandlerQueue()

        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())

        self.pickerRay = CollisionRay()

        self.pickerNode.addSolid(self.pickerRay)

        self.picker.addCollider(self.pickerNode, self.queue)

        self.pickedObj = None 

        self.accept('mouse1', self.printMe)

    def makePickable(self, newObj):
        newObj.setTag('pickable', 'true')

    def getObjectHit (self, mpos):
        self.pickedObj = None 
        self.pickerRay.setFromLens (base.camNode, mpos.getX(), mpos.getY())
        self.picker.traverse(render)
        if self.queue.getNumEntries() > 0:
            self.queue.sortEntries()
            self.pickedObj = self.queue.getEntry(0).getIntoNodePath()

            parent = self.pickedObj.getParent()
            self.pickedObj = None 

            while parent != render: 
                if parent.getTag('pickable')=='true':
                    self.pickedObj=parent 
                    return parent 
                else:
                    parent = parent.getParent() 
        return None

    def getPickedObj(self):
        return self.pickedObj 

    def printMe(self):
        self.getObjectHit (base.mouseWatcherNode.getMouse())
        print self.pickedObj


app=MyApp()
app.run()

