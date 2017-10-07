#!/usr/bin/env python

from direct.showbase.ShowBase import ShowBase 
from direct.task.Task import Task
from random import randint, choice, random
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectSlider import DirectSlider
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
import math
import sys,os
import colorsys
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.interval.LerpInterval import *
import time

#https://www.panda3d.org/manual/index.php/Configuring_Panda3D
winWidth, winHeight = 960, 720
loadPrcFileData('', 'win-size %d %d' % (winWidth,winHeight))


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        #color setup for galaxies
        self.r,self.g,self.b=180,210,150
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
        self.loadTextures()
        
        #load galaxies
        #self.currMiddleModel = 0
        #self.loadMiddleModel(self.currMiddleModel)
        self.galaxies={}
        step,self.counter = 1,0 
        self.loadGalaxies(step)
        
        #load planet
        self.planetYOffset, self.planetZOffset = 1.8, -.8
        self.loadPlanets()
        
        '''
        #init planet fog - hide this at click!!!!
        #http://www.panda3d.org/forums/viewtopic.php?p=40880
        self.colorFog = (0.5,0.8,0.8)
        self.planetFog = Fog('Planet Fog')
        self.planetFog.setColor(*self.colorFog)
        self.planetFog.setLinearRange(0,300) #change second val to change distance 
        self.planetFog.setLinearFallback(45,160,320)
        self.cloudEffect = render.attachNewNode(self.planetFog)
        self.cloudEffect.setPos(0,0,0) #get pos from planet??
        render.setFog(self.planetFog)
        '''
        
        #load plane
        self.drawTerrain()
        
        #make 2d elements
        self.drawMenu()
        self.drawSlider()
        self.drawEscapeText()
        self.drawHelpButton()
        self.drawResetButton()
        self.drawGalaxyButton()
        
        #define movement and interaction
        self.defineIntervals()
        self.createKeyControls()
        self.createKeyControls()
        self.keyMap = {'left':0, 'right':0, 'up':0, 'down':0, 'counter':0, 'clock':0}

        #collision - put in sep func
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        self.planet.setTag('myObjectTag', '1')
        self.planetHover = False


        '''
        #init fog - doesnt work wo objects in scene
        #taken from Panda3d - samples/infinite-tunnel
        self.fog = Fog('distanceFog')
        self.fog.setColor(1, 1, 1)
        self.fog.setExpDensity(.5)
        render.setFog(self.fog)
        '''

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

        #mouse functions 
        self.planetHidden = False
        self.mouseTask = taskMgr.add(self.mouseTask, 'mouseTask')
        self.accept('mouse1', self.planetClick)

        ############ timer functions ###############
        self.timer=.5
        
        #change user perspective
        taskMgr.doMethodLater(self.timer,self.move, "move") #should this pause w help menu
        
        #color algorithm
        taskMgr.doMethodLater(self.timer,self.changeColorTask, "changeColor")
        
        #change time scaler
        self.maxYear = 13.8 
        self.currYear = 0 
        self.yearInc = 0.003
        taskMgr.doMethodLater(self.timer, self.incYear, 'changeYear')
        
        #keep planet in view 
        self.planetP = 0
        self.planetPInc = .1
        taskMgr.doMethodLater(self.timer, self.rotatePlanet, 'rotatePlanet')
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

    ############ MOUSE FUNCTIONS ############
    def planetClick(self):
        if self.planetHover == True: 
            print('planet clicked')
            taskMgr.remove('changeYear')
            taskMgr.remove('move')
            taskMgr.remove('changeColor')
            taskMgr.remove('rotatePlanet')
            self.planet.hide()
            self.planetHidden = True

            #load inf plane 
            #NEED new move function 
            #3 hor, 2 ver
            
            self.showTerrain()
        else: 
            print('other click')
            if self.planetHidden == True:
                self.planet.show()
                self.planetHidden = False

                taskMgr.doMethodLater(self.timer,self.move, "move") #should this pause w help menu
                taskMgr.doMethodLater(self.timer,self.changeColorTask, "changeColor")
                taskMgr.doMethodLater(self.timer, self.incYear, 'changeYear')
                taskMgr.doMethodLater(self.timer, self.rotatePlanet, 'rotatePlanet')

                self.hideTerrain()
    ############TASKS################
    def changeColorTask(self,task):
        end = 0.5
        
        currR, currG, currB = self.getCurrColor(end)
        #self.galaxies[0].setColor(1.0*currR/256, 1.0*currG/256, 1.0*currB/255,1) #consider setColorScale

        for gal in self.galaxies:
            squares = list(map(lambda x: (x//10)**2, self.galaxies[gal].getPos()))
            distance = (sum(squares))**0.5  #use func to find ACTUAL distance of obj from center
            if distance != 0: 
                modifier = min(1, math.log(distance)/1.8)
            else: modifier = 0
            #print(distance,modifier)
            currR, currG, currB = self.getCurrColor(end + modifier)
            #print(gal, currR)
            self.galaxies[gal].setColor(1.0*currR/255, 1.0*currG/255, 1.0*currB/255,1)

    	return Task.cont

    def move (self,task): 
    	inc=1
    	if self.keyMap['up']>0:
    		(dx,dy,dz)=(0,inc, 0)
    	elif self.keyMap['down']>0:
    		(dx,dy,dz)=(0,-inc, 0)
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
    
    def moveInPlane (self,task): 
        inc=.05
        if self.keyMap['up']>0:
            self.up+=1
            self.down-=1
            (dx,dy,dz)=(0,-inc, 0)
        elif self.keyMap['down']>0:
            self.up-=1
            self.down+=1
            (dx,dy,dz)=(0,inc, 0)
        elif self.keyMap['left']>0:
            (dx,dy,dz)=(inc,0,0)
            self.left +=1
            self.right -=1
        elif self.keyMap['right']>0:
            (dx,dy,dz)=(-inc,0,0)
            self.right += 1
            self.left -= 1
        else:
            (dx,dy,dz)=(0,0,0)
        pos = (dx,dy,dz)
        
        for i in range(3):
            self.playerTerrainPos[i] += pos[i]
        
        for plane in self.land:
            x,y,z=self.land[plane].getPos()
            self.land[plane].setPos(x+dx,y+dy,z+dz)
        
        #print(self.up,self.down)
        self.modTerrain()

        return task.cont
    
    def containsMultipleThree(self,newVal,oldVal):
        high = math.floor(max(newVal, oldVal))
        low = math.floor(min(newVal, oldVal))
        if high!=low:
            return high%self.blenderPlaneDim==0
        return False

    def modTerrain(self):
        x,y,z = self.playerTerrainPos
        if self.containsMultipleThree(x,self.oldX): #use almost equal
            if self.right> self.left: #take tile on left and move to right
                #take gals with least x vals 
                planeIndices, posVals=self.getPlanesWithLeastValue('x')
                newX = max(posVals) + self.blenderPlaneDim
                self.repositionGals(planeIndices,newX, 0)
                self.right, self.left = 0,0
                print(planeIndices, posVals, newX)
            elif self.left>self.right:
                planeIndices, posVals= self.getPlanesWithGreatestValue('x')
                newX = min(posVals) - self.blenderPlaneDim
                self.repositionGals(planeIndices,newX, 0)
                print(planeIndices, posVals, newX)
            #have to figure out if left or right 
                self.right, self.left = 0,0  
        #print(y, self.up, self.down)
        if self.containsMultipleThree(y,self.oldY): #almost equal 
            #print(self.up, self.down,y)
            if self.up > self.down:
                planeIndices, posVals=self.getPlanesWithLeastValue('y')
                newY = max(posVals) + self.blenderPlaneDim
                self.repositionGals(planeIndices,newY,1)
                self.up,self.down = 0, 0
            
            elif self.down > self.up: 
                planeIndices, posVals = self.getPlanesWithGreatestValue('y')
                newY = min(posVals) - self.blenderPlaneDim 
                self.repositionGals(planeIndices,newY, 1)
                self.up,self.down = 0, 0
        self.oldX,self.oldY,self.oldZ = x,y,z
    
    def repositionGals(self,planeIndices, newPos, index):
        for plane in planeIndices:
            currPos = self.land[plane].getPos()
            currPos[index] = newPos
            self.land[plane].setPos(*currPos)

    def getPlanesWithLeastValue(self,dir):
        index = 0 if dir=='x' else 1
        leastValPlanes = []
        leastValue = None
        posVals = set()

        for plane in self.land: #check name
            pos = self.land[plane].getPos()
            currX = pos[index]
            posVals.add(int(round(currX)))
            if leastValue == None:
                leastValPlanes = [plane]
                leastValue = currX
            elif self.almostEqual(currX,leastValue):
                leastValPlanes.append(plane)
            elif currX<leastValue:
                leastValPlanes = [plane]
                leastValue = currX
        return leastValPlanes, posVals

    def getPlanesWithGreatestValue(self,dir):
        index = 0 if dir=='x' else 1
        greatestValPlanes = []
        greatestValue = None
        posVals = set()

        for plane in self.land: #check name
            pos = self.land[plane].getPos()
            currX = pos[index]
            posVals.add(round(currX))
            if greatestValue == None:
                greatestValPlanes = [plane]
                greatestValue = currX
            elif self.almostEqual(currX,greatestValue):
                greatestValPlanes.append(plane)
            elif currX>greatestValue:
                greatestValPlanes = [plane]
                greatestValue = currX
        return greatestValPlanes, posVals




    def rotatePlanet(self,task):
        self.planetP+=self.planetPInc
        self.planet.setHpr(0, self.planetP, 0)
        return task.cont

    def defineIntervals(self):
    	self.midGalaxyTurnInterval= Sequence(
    		self.galaxies[0].hprInterval(.3, (0,50,0)), #try changing this stuff
    		self.galaxies[0].hprInterval(2,(20,-30,0))
    		)

    def createMovementLoop(self):
    	loop = Parallel(
    		self.midGalaxyTurnInterval,
    		)
    	loop.start()

    def mouseTask(self,task):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.camNode,mpos.getX(),mpos.getY())
            #collision pass 
            self.picker.traverse(self.planetRoot)
            if self.pq.getNumEntries()>0:
                self.planetHover = True
            else: 
                self.planetHover = False
        return Task.cont
    
    def incYear(self, task):
        if self.currYear < self.maxYear:
            self.currYear+=self.yearInc
            #make call to set slider to change its value 
            self.setTimeSliderValue (self.currYear)
            #make call to color change func
        return Task.cont





    ########## :DATA STUFF #################
    def setTimeSliderValue(self, year):
        new = (year/self.maxYear)
        self.yearSlider.guiItem.setValue(new)
        #this needs to modify the slider (use self var?)

    def resetTime(self):
        self.setTimeSliderValue(0)

    def changeYear(self):
        fraction = self.yearSlider.guiItem.getValue()
        self.currYear = fraction * self.maxYear

    def getCurrColor(self,end):
        frac = (self.currYear/self.maxYear)
        redInterval = (self.r - self.endR)*end
        greenInterval = (self.g - self.endG)*end
        blueInterval = (self.b - self.endB)*end

        rPos,gPos,bPos = (redInterval*frac), (greenInterval*frac), (blueInterval*frac)
        retR, retG, retB = int(self.r-rPos), int(self.g-gPos), int(self.b-bPos)
        return retR, retG, retB

    def closeHelpMenu(self):
        self.helpFrame.hide()
        taskMgr.doMethodLater(self.timer,self.move, "move") #should this pause w help menu
        taskMgr.doMethodLater(self.timer,self.changeColorTask, "changeColor")
        taskMgr.doMethodLater(self.timer, self.incYear, 'changeYear')
        taskMgr.doMethodLater(self.timer, self.rotatePlanet, 'rotatePlanet')

    def closeGalaxyMenu(self):
        #parse selected galaxy
        if self.newMiddleGal != 'Current': #then we need to switch gal
            num = int(self.newMiddleGal[len(self.newMiddleGal)-1])
            changePos = self.galaxies[num].getPos()
            self.galaxies[self.currMiddleModel], self.galaxies[num] = self.galaxies[num], self.galaxies[self.currMiddleModel]
            self.galaxies[self.currMiddleModel].setPos(0,0,0)
            self.galaxies[num].setPos(changePos)
            #shitty algorithm for repositioning!!!
        self.galFrame.hide()
        taskMgr.doMethodLater(self.timer,self.move, "move") #should this pause w help menu
        taskMgr.doMethodLater(self.timer,self.changeColorTask, "changeColor")
        taskMgr.doMethodLater(self.timer, self.incYear, 'changeYear')
        taskMgr.doMethodLater(self.timer, self.rotatePlanet, 'rotatePlanet')

    def showTerrain(self):
        self.landRoot.show()
        self.right,self.left,self.up, self.down = 0,0,0,0
        self.oldX,self.oldY,self.oldZ = 0,0,0
        taskMgr.doMethodLater(self.timer,self.moveInPlane, "movePlane")

    def hideTerrain(self):
        self.landRoot.hide()
        self.initTerrain()
        taskMgr.remove('movePlane')

    def initTerrain(self):
        self.playerTerrainPos=[0,0,0]
        self.landCounter = 0
        zPos = 0
        for xPos in range(-self.blenderPlaneDim,self.blenderPlaneDim+1,3):
            for yPos in range (0,self.blenderPlaneDim*3+1,3):
                self.land[self.landCounter].setPos(xPos, yPos, zPos)
                self.landCounter+=1

    #taken from hw4
    def almostEqual(self,d1, d2, epsilon=10**-3): #check if not used
        # note: use math.isclose() outside 15-112 with Python version 3.5 or later
        return (abs(d2 - d1) < epsilon)




    ########## Background/Foreground ####################
    

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

    	self.setBackgroundColor((0, 0.4, 0, 1))
    


    ################ Draw 2D ###############
    def drawMenu(self):
        pText='GALAXY GLIDER'
        self.textObject= OnscreenText(text=pText, pos=(0,.9), scale=.07, fg=(1,.5,.5,1), align=TextNode.ACenter, mayChange=1)
    
    def drawEscapeText(self):
        self.escapeText = OnscreenText(text="ESC: Quit", parent=base.a2dTopLeft,
                                       fg=(1,1,1, 1), pos=(0.06, -0.1),
                                       align=TextNode.ALeft, scale=.05)
    def drawSlider(self):
        self.yearSlider = DirectSlider(pos = (-0.1,0,.75), scale = 0.8, value = 0.2, command = self.changeYear)

    def drawHelpButton(self):
        self.helpButton = DirectButton(pos=(-0.2, 0, 0.15), text="HELP",parent=base.a2dBottomRight,
                                   scale=.1, pad=(.1, .1),
                                   command=self.drawHelpMenu)
    def drawGalaxyButton(self):
        self.galaxyButton = DirectButton(pos=(-0.45, 0, 0.35), text="GALAXY SELECT",parent=base.a2dBottomRight,
                                   scale=.1, pad=(.1, .1),
                                   command=self.drawGalaxyMenu)
    def drawResetButton(self):
        self.resetButton = DirectButton(pos=(-.4, 0, -.27), text="RESET",parent=base.a2dTopRight,
                                   scale=.1, pad=(.1, .1),
                                   command=self.resetTime)
    def drawHelpMenu(self): #can 
        #disable click stuff too!
        taskMgr.remove('changeYear')
        taskMgr.remove('move')
        taskMgr.remove('changeColor')
        taskMgr.remove('rotatePlanet')
        self.helpXMargin, self.helpYMargin =75, 125
        print('ye')
        frameSize=(-.4,2.4,-2,0)
        self.helpFrame = DirectFrame(frameSize=frameSize, frameColor=(0,0.3,0.4,1),
                                    pos=(-1,-1,1))
        #do i want to reparent the frame to anything?
        helpTitle = "Help Menu"
        helpTitleObject = OnscreenText(parent=self.helpFrame, text = helpTitle, pos = (1,-.35,0),  #set parent??
                scale = 0.1,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        helpText = "To pan left-to-right and up-and-down, use the arrow keys."
        helpText2 = "To rotate, use 'r' for clockwise and 'l' for counterclockwise."
        help1Obj = OnscreenText(parent=self.helpFrame, text = helpText, pos = (1,-.6,0),  #set parent??
                scale = 0.07,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        help2Obj = OnscreenText(parent=self.helpFrame, text = helpText2, pos = (1,-.8,0),  #set parent??
                scale = 0.07,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        self.closeButton = DirectButton(parent=self.helpFrame,pos=(1,0,-1.8), text="CLOSE",
                                   scale=.1, pad=(.1, .1),
                                   command=self.closeHelpMenu)    

    def drawGalaxyMenu(self): #LOAD FRAME IN INIT + help frame!!!!!!!!!!!!!
        #disable click stuff too!!!
        taskMgr.remove('changeYear')
        taskMgr.remove('move')
        taskMgr.remove('changeColor')
        taskMgr.remove('rotatePlanet')
        self.helpXMargin, self.helpYMargin =75, 125
        print('ye')
        frameSize=(-.4,2.4,-2,0)
        self.galFrame = DirectFrame(frameSize=frameSize, frameColor=(0,0.3,0.4,1),
                                    pos=(-1,-1,1))
        #do i want to reparent the frame to anything?
        helpTitle = "Galaxy Selector"
        helpTitleObject = OnscreenText(parent=self.galFrame, text = helpTitle, pos = (1,-.35,0),  #set parent??
                scale = 0.1,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        helpText = "Select a galaxy"
        help2Obj = OnscreenText(parent=self.galFrame, text = helpText, pos = (1,-.8,0),  #set parent??
                scale = 0.07,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        galaxyList = ['Galaxy %d' %(i) for i in range(self.counter)] # am i missing one
        galaxyList = ['Current'] + galaxyList
        self.newMiddleGal = "Current"
        self.galaxySelector = DirectOptionMenu(parent=self.galFrame,text="options", scale=0.1,pos=(.8,0,-1.5),items=galaxyList,
                initialitem=0,highlightColor=(0.65,0.65,0.65,1),command=self.itemSel,textMayChange=1)
        self.goButton = DirectButton(parent=self.galFrame,pos=(1,0,-1.8), text="GO",
                                   scale=.1, pad=(.1, .1),
                                    command=self.closeGalaxyMenu)
    def itemSel(self,arg):#NOT WORKING!!!
        print('item selected', arg)
        self.newMiddleGal = arg

    def loadTextures(self):
        try:
            self.starTexture = loader.loadTexture('textures/starSurface.jpg')
            self.starTexture.setWrapU(Texture.WM_repeat)
            self.starTexture.setWrapV(Texture.WM_repeat)

            self.planetTexture = loader.loadTexture('textures/mars.jpg')
            self.planetTexture.setWrapU(Texture.WM_repeat)
            self.planetTexture.setWrapV(Texture.WM_repeat)
        except:
            print('failed to load textures')
    ################# Draw Galaxies #####################
    def loadGalaxies(self, step):
        if step==1:
            self.loadMiddleModel(self.counter)
            self.counter+=1
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
                            print(self.counter)
                            return False 
        return True

    def loadGalaxy(self,name,position):
        self.galaxies[self.counter]=loader.loadModel('galaxies/%s' %(name))
        self.galaxies[self.counter].reparentTo(self.render)
        xyzPos = [i*10 for i in position] # fix position - check size w cubes
        print(xyzPos)
        self.galaxies[self.counter].setPos(*xyzPos)
        self.galaxies[self.counter].setColor(*self.startColor)

    def loadMiddleModel(self,num):
    	self.galaxies[self.counter] = loader.loadModel('galaxies/gal%d' %(num))
    	self.galaxies[self.counter].reparentTo(self.render) 
    	self.galaxies[self.counter].setPos (0,0,0)
    	self.galaxies[self.counter].setColor(*self.startColor)
        self.currMiddleModel = num
    	#set texture 
        self.galaxies[self.counter].setTexture(self.starTexture)
    	
    ################## Draw Planets ###################
    def loadPlanets(self): # place planet in curr galaxy - which would actually just be the thing in center
        try: 
            self.planet = loader.loadModel('modelsMisc/planet3Small')

            self.planetRoot = render.attachNewNode('planetRoot')

            self.planetRoot.setPos(0, 0, 0)
            self.planetRoot.setHpr(0 , 0 , 0)
            self.planetRoot.reparentTo(base.camera)

            self.planet.reparentTo(self.planetRoot)
            #self.planet.reparentTo(base.camera) #necessary?
            self.planet.setPos(0,self.planetYOffset,self.planetZOffset)
            self.planet.setTag('planet', '1')
            
            #load texture?
            self.planet.setTexture(self.planetTexture)

            print('loaded planet')
        except:
            print('failed to load planet')
   
    
    def drawTerrain(self):
        self.blenderPlaneDim = 5
        self.landRoot = render.attachNewNode('land')
        self.playerTerrainPos= [0,0,0] #use collision det for z dir
        self.land = {}
        self.landCounter = 0

        self.landRoot.setPos(0, 1.8, -.4 )
        self.landRoot.setHpr(0 , 15 , 0)
        self.landRoot.reparentTo(base.camera)

        self.loadTerrain()

        self.landRoot.hide()
        
    def loadTerrain(self):
        zPos = 0
        for xPos in range(-(2*self.blenderPlaneDim),2*self.blenderPlaneDim+1,self.blenderPlaneDim):
            for yPos in range (-self.blenderPlaneDim,self.blenderPlaneDim*3+1,self.blenderPlaneDim):
                
                self.land[self.landCounter] = loader.loadModel('modelsMisc/land')
                self.land[self.landCounter].reparentTo(self.landRoot)
                self.land[self.landCounter].setTexture(self.starTexture)
                self.land[self.landCounter].setPos(xPos, yPos, zPos)
                self.landCounter+=1
       
    ############## Unused Code ##################
    
app=MyApp()
app.run()

