#!/usr/bin/env python

from direct.showbase.ShowBase import ShowBase 
from direct.task.Task import Task
import random
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
from direct.filter.CommonFilters import CommonFilters
#import GeoMipTerrain 

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

        self.startWavelength = 380
        self.endWavelength = 750
        
        #textures
        self.loadTextures()
        
        #planet setup 
        self.planetColor = [0,0,3,2,1]
        #load planet
        self.planetYOffset, self.planetZOffset = 1.8, -.8
        self.loadPlanets()

        #load plane
        self.drawTerrain()

        #load background, objects
        self.uniTime=0
        self.loadBackground()
        
        
        #load galaxies
        self.positionSet = set()
        self.galaxyRoot = render.attachNewNode('galaxyRoot')
        self.planetRoot.setPos(0, 0, 0)
        self.planetRoot.setHpr(0 , 0 , 0)
        self.galaxyRoot.reparentTo(base.camera)
        self.galaxies = {}
        self.galaxyDistances = {}
        step,self.counter = 1,0 
        self.loadGalaxies(step)
        
        
        
        #make 2d elements
        self.drawMenu()
        self.drawSlider()
        self.drawEscapeText()
        self.drawHelpButton()
        self.drawResetButton()
        self.drawGalaxyButton()
        
        #define movement and interaction
        self.createKeyControls()
        self.keyMap = {'left':0, 'right':0, 'up':0, 'down':0, 'counter':0, 'clock':0, 'glow':0, 'unglow':0}

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



        #glow filter - panda3D samples: glow-filter
        self.filters = CommonFilters(base.win, base.cam)
        self.glowSize = 1
        filterok = self.filters.setBloom(
            blend=(0, 0, 0, 1), desat=-0.5, intensity=3.0, size=self.glowSize)
        

        #position camera 
        self.camera.setPos(0,0,0)
        self.x,self.y,self.z=0,0,0
        base.disableMouse() 

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

        taskMgr.doMethodLater(self.timer, self.expandGalaxies, 'expandGalaxies')

        ###################
        self.inSim = False
        self.drawHomeScreen()
        

    def setKey(self, key, value):
    	self.keyMap[key]=value 

    def createKeyControls(self):
    	self.accept('l',self.setKey, ['counter',1])
    	self.accept('r',self.setKey, ['clock',1])
    	self.accept('arrow_up',self.setKey, ['up',1])
    	self.accept('arrow_down',self.setKey, ['down',1])
    	self.accept('arrow_left',self.setKey, ['left',1])
    	self.accept('arrow_right',self.setKey,['right',1])
        self.accept('g', self.setKey, ['glow', 1])
        self.accept('f', self.setKey, ['unglow', 1])
        self.accept('h', self.changeGlow2, [1])
        self.accept('j', self.changeGlow2, [-1])
    	
    	# stop moving on key release
    	self.accept('arrow_up-up',self.setKey, ['up',0])
    	self.accept('arrow_down-up',self.setKey, ['down',0])
    	self.accept('arrow_left-up',self.setKey, ['left',0])
    	self.accept('arrow_right-up',self.setKey, ['right',0])
    	self.accept('l-up',self.setKey, ['counter',0])
    	self.accept('r-up',self.setKey, ['clock',0])
        self.accept('g-up', self.setKey, ['glow', 0])
        self.accept('f-up', self.setKey, ['unglow', 0])

        self.accept('escape', sys.exit)

    ############ MOUSE FUNCTIONS ############
    def planetClick(self):
        if self.planetHover == True and self.inSim == True: 
            print('planet clicked')
            taskMgr.remove('changeYear')
            taskMgr.remove('move')
            taskMgr.remove('changeColor')
            taskMgr.remove('rotatePlanet')
            self.planet.hide()
            self.planetHidden = True
            filterok = self.filters.setBloom(
                blend=(0, 0, 0, 1), desat=-0.5, intensity=3.0, size=0)
            
            self.showTerrain()
        else: 
            print('other click')
            if self.planetHidden == True:
                self.planet.show()
                self.planetHidden = False
                filterok = self.filters.setBloom(
                blend=(0, 0, 0, 1), desat=-0.5, intensity=3.0, size=int(self.glowSize))

                taskMgr.doMethodLater(self.timer,self.move, "move") #should this pause w help menu
                taskMgr.doMethodLater(self.timer,self.changeColorTask, "changeColor")
                taskMgr.doMethodLater(self.timer, self.incYear, 'changeYear')
                taskMgr.doMethodLater(self.timer, self.rotatePlanet, 'rotatePlanet')

                self.hideTerrain()
    


    ############TASKS################
    def changeColorTask0000(self,task):
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
    
    def changeColorTask(self,task):
        startScale = 1
        exponent = 3 * (self.currYear/self.maxYear)
        for gal in range(1,self.counter):
            squares = list(map(lambda x: (x//10)**2, self.galaxyDistances[gal][0]))
            distance = (sum(squares))**0.5  #use func to find ACTUAL distance of obj from center
            if distance != 0: 
                modifier = distance/8
                #print(modifier,distance)
            else: modifier = 0
            scale = startScale + modifier
            multiplier = (scale**exponent)
            #print(multiplier)
            wavelength = self.startWavelength * multiplier
            rgb = self.wav2RGB(wavelength)
            #if gal ==2:
                #print(rgb, wavelength, multiplier, distance)
            self.galaxies[gal].setColor(*rgb)

        return Task.cont

    #http://codingmess.blogspot.com/2009/05/conversion-of-wavelength-in-nanometers.html
    def wav2RGB(self,wavelength):
        w = int(wavelength)

        # colour
        if w >= 380 and w < 440:
            R = -(w - 440.) / (440. - 350.)
            G = 0.0
            B = 1.0
        elif w >= 440 and w < 490:
            R = 0.0
            G = (w - 440.) / (490. - 440.)
            B = 1.0
        elif w >= 490 and w < 510:
            R = 0.0
            G = 1.0
            B = -(w - 510.) / (510. - 490.)
        elif w >= 510 and w < 580:
            R = (w - 510.) / (580. - 510.)
            G = 1.0
            B = 0.0
        elif w >= 580 and w < 645:
            R = 1.0
            G = -(w - 645.) / (645. - 580.)
            B = 0.0
        elif w >= 645 and w <= 780:
            R = 1.0
            G = 0.0
            B = 0.0
        else:
            R = 1.0
            G = 0.0
            B = 0.0

        # intensity correction
        if w >= 380 and w < 420:
            SSS = 0.3 + 0.7*(w - 350) / (420 - 350)
        elif w >= 420 and w <= 700:
            SSS = 1.0
        elif w > 700 and w <= 780:
            SSS = 0.3 + 0.7*(780 - w) / (780 - 700)
        else:
            SSS = 0.0
        SSS *= 255

        return [int(SSS*R), int(SSS*G), int(SSS*B)]



    def changeGlow2 (self,inc):
        if self.planetHidden == False: #check??
            if inc>0:
                if self.glowSize<3:
                    self.glowSize +=1
            elif inc<0:
                if self.glowSize>0:
                    self.glowSize-=1
            filterok = self.filters.setBloom(
                blend=(0, 0, 0, 1), desat=-0.5, intensity=3.0, size=int(self.glowSize))


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
        self.galaxyRoot.setHpr(self.x,self.y,self.z)

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


    def expandGalaxies(self,task): #!!!!!! make exponential?
        inc = 0.3 * self.currYear
        for gal in range(1, self.counter):
            x,y,z = self.galaxyDistances[gal][0]
            distance = ((x**2)+(y**2)+(z**2))**0.5
            if distance != 0:
                unitX, unitY, unitZ = x/distance, y/distance, z/distance 
                newDist = distance + inc 
                newX, newY, newZ = newDist*unitX, newDist*unitY, newDist*unitZ
                self.galaxies[gal].setPos(newX,newY,newZ)
        return task.cont

    def rotatePlanet(self,task):
        self.planetP+=self.planetPInc
        self.planet.setHpr(0, self.planetP, 0)
        return task.cont
    '''
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
    '''

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

    def closeHomeScreen(self):
        self.helpFrame.hide()
        self.resetTime()
        self.inSim = True
        taskMgr.doMethodLater(self.timer,self.move, "move") #should this pause w help menu
        taskMgr.doMethodLater(self.timer,self.changeColorTask, "changeColor")
        taskMgr.doMethodLater(self.timer, self.incYear, 'changeYear')
        taskMgr.doMethodLater(self.timer, self.rotatePlanet, 'rotatePlanet')

    def closeHelpMenu(self):
        self.helpFrame.hide() 
        self.inSim = True
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
        self.inSim = True
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

    def getRandPos(self, xPos,yPos,zPos, interval):
        x,y,z = self.selectFloat(xPos - interval, xPos + interval),self.selectFloat(yPos - interval, yPos + interval),zPos         
        return (x,y,z)
    
    def selectFloat(self, min,max):
        while True:
            minInt = math.floor(min)
            maxInt = math.floor(max)
            base = random.randint(minInt,maxInt)
            add = random.random()
            num = base + add
            if num>=min and num<=max:
                return num

    ######### Land Data Stuff ###########################
    def containsMultiple(self,newVal,oldVal):
        high = math.floor(max(newVal, oldVal))
        low = math.floor(min(newVal, oldVal))
        if high!=low:
            return high%self.blenderPlaneDim==0
        return False

    def modTerrain(self):
        x,y,z = self.playerTerrainPos
        if self.containsMultiple(x,self.oldX): #use almost equal
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
        if self.containsMultiple(y,self.oldY): #almost equal 
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

    ########## Background/Foreground ####################
    

    def loadBackground(self):
    	#lighting documentation 
    	#https://www.panda3d.org/manual/index.php/Lighting#Ambient_Lights
    	
    	#point light
    	plight1= PointLight('plight')
    	plight1.setColor((2,2,2,1)) #change brightness
    	plight1NodePath=render.attachNewNode(plight1)
    	plight1NodePath.setPos(0,0,0)  
    	render.setLight(plight1NodePath)
        #plight1.setAttenuation((.2, 0, 1))

        plight2= PointLight('plight')
        plight2.setColor((1,1,1,1))
        plight2NodePath=render.attachNewNode(plight2)
        plight2NodePath.setPos(0,0,20)
        self.landRoot.setLight(plight2NodePath) #change to land

        '''
        #spotlight #adapted from shadows sample (Panda3D)
        self.light = self.landRoot.attachNewNode(Spotlight("Spot"))
        self.light.node().setScene(self.landRoot)
        self.light.node().setShadowCaster(True)
        #self.light.node().showFrustum()
        self.light.node().getLens().setFov(60)
        self.light.node().getLens().setNearFar(2, 100)
        self.landRoot.setLight(self.light)
        self.landRoot.setShaderAuto()'''

        #light.setP(-45)
        #light.setZ(20)        
        #light.node().getLens().setFilmSize(100, 100)

    	#ambient light
    	ambientL=AmbientLight('ambientL')
    	ambientL.setColor(VBase4(0.4,0.4,0.4,1))
    	alnp = render.attachNewNode(ambientL)
    	render.setLight(alnp)

    	self.setBackgroundColor((0, 0, 0, 1))
    
    ################ Draw 2D ###############
    def drawHomeScreen(self):
        #disable click stuff too!
        taskMgr.remove('changeYear')
        taskMgr.remove('move')
        taskMgr.remove('changeColor')
        taskMgr.remove('rotatePlanet')
        self.homeXMargin, self.homeYMargin =75, 125
        frameSize=(-.4,2.4,-2,0)
        self.helpFrame = DirectFrame(frameSize=frameSize, frameColor=(0,0.3,0.4,1),
                                    pos=(-1,-1,1))
        homeTitle = "Galaxy Glider"
        homeTitleObject = OnscreenText(parent=self.helpFrame, text = homeTitle, pos = (1,-.35,0),  #set parent??
                scale = 0.8,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        tutorialText = "TUTORIAL"
        startText = "START"
        self.tutorialButton = DirectButton(parent=self.helpFrame,pos=(1,0,-1.8), text=tutorialText,
                                   scale=.1, pad=(.1, .1),
                                   command=self.drawTutorialOne)
        self.startButton = DirectButton(parent=self.helpFrame,pos=(1,0,-1.6), text=startText,
                                   scale=.1, pad=(.1, .1),
                                   command=self.closeHomeScreen)
    def initTutorialMessages(self):
        self.tutorialMessages = dict()
        self.tutorialMessages[1] = ("Goal",'''This project is a simplified visualization of the universe. 
        It takes users through the life of the universe by incrementing
        the age of the universe from 0 years to its current age, 13.8 
        billion years.  
                        ''')
        self.tutorialMessages[2] = ('Redshift', '''The colors we perceive depend on the wavelength an object
        emits, as well as the speed the objects are moving away
        from us. As the universe aged, the galaxies grew farther 
        apart, and at an increasingly faster speed. This movement
        leads to redshifting, which means that we see faraway 
        galaxies as redder than they are.''')

        self.tutorialMessages[3] = ('User Interaction', '''Use the time slider at the top to view the universe at
            different ages. Use the arrow keys, 'r' and 'l' to rotate 
            your view. Click on the planet to explore it, and move around
            with arrow keys.''')

        self.tutorialMessages[4] = ('Other', '''Click on the help button to read instructions. Click
            on the galaxy button to change which galaxy you are in.
             Use the reset button to set the age of the universe to
              0 years.''')

    def drawTutorialOne(self):
        self.helpFrame.hide()
        self.homeXMargin, self.homeYMargin =75, 125
        frameSize=(-.4,2.4,-2,0)
        self.tutorialPage = 1
        self.initTutorialMessages()
        
        self.helpFrame = DirectFrame(frameSize=frameSize, frameColor=(0.1,0.4,0.7,1),
                                    pos=(-1,-1,1))

        self.tutorialTitleObject = OnscreenText(parent=self.helpFrame, text = self.tutorialMessages[1][0], pos = (1,-.45,0),  #set parent??
                scale = 0.3,fg=(1,0.5,0.5,1),align=TextNode.ACenter, wordwrap = 55, mayChange = True)
       
        self.tutorialTextObject = OnscreenText(parent=self.helpFrame, text = self.tutorialMessages[1][1], pos = (1,-.9,0),  #set parent??
                scale = 0.07,fg=(1,0.5,0.5,1),align=TextNode.ACenter, mayChange = True, wordwrap = 55)
        
        self.nextButton = DirectButton(parent=self.helpFrame,pos=(1,0,-1.6), text='NEXT',
                                   scale=.1, pad=(.1, .1),
                                   command=self.nextTutorialScreen)
        self.startButton = DirectButton(parent=self.helpFrame,pos=(1,0,-1.8), text='START',
                                   scale=.1, pad=(.1, .1),
                                   command=self.closeHomeScreen)
    def nextTutorialScreen(self):
        numValues = len(self.tutorialMessages)
        if (self.tutorialPage + 1) == numValues:
            self.nextButton.destroy()
        
        self.tutorialPage +=1
        self.tutorialTitleObject['text'] = self.tutorialMessages[self.tutorialPage][0]
        self.tutorialTextObject['text'] = self.tutorialMessages[self.tutorialPage][1]

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
    def drawHelpMenu(self):   
        self.inSim = False
        taskMgr.remove('changeYear')
        taskMgr.remove('move')
        taskMgr.remove('changeColor')
        taskMgr.remove('rotatePlanet')
        self.helpXMargin, self.helpYMargin =75, 125
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
        self.inSim = False
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

            self.treeTexture = loader.loadTexture('textures/treeText.jpg')
            self.treeTexture.setWrapU(Texture.WM_repeat)
            self.treeTexture.setWrapV(Texture.WM_repeat)
        except:
            print('failed to load textures')

    ################# Draw Galaxies #####################
    def loadGalaxies(self, step):
        if step==1:
            self.loadMiddleModel(self.counter)
            self.positionSet.add((0,0,0))
            self.counter+=1
        check = self.getGalaxyLayer(step)
        print('check',check)
        if check==True:
            self.loadGalaxies(step+1)
        #else do nothing and end func
    
    def getGalaxyLayer(self, step):
        try:
            for pos in range(3):
                for stepTry in [-step,step]: #does this work?
                    name = 'gal' + str(self.counter)
                    position = [0*pos] + [stepTry]
                    position += [0*(3-len(position))] 
                    self.loadGalaxy(name,position)
                    self.positionSet.add(tuple(position))
                    print('position')
                    self.counter+=1
            result = self.permutePositions(step)
            return result
        except:
            print('failed')
            return False
    
    def permutePositions(self,step):
        print('peep')
        for first in [-step,0,step]:
            for second in [-step,0,step]:
                for third in [-step,0,step]:
                    position = (first,second,third)
                    name = 'gal' + str(self.counter)
                    if position not in self.positionSet:
                        try:
                            self.loadGalaxy(name,position)
                            self.counter+=1
                            self.positionSet.add(position)
                        except:
                            print(self.counter)
                            print(self.positionSet)
                            return False 
        return True

    def loadGalaxy(self,name,position):
        self.galaxies[self.counter]=loader.loadModel('galaxies/%s' %(name))
        self.galaxies[self.counter].reparentTo(self.galaxyRoot)
        xyzPos = [i*10 for i in position] # fix position - check size w cubes
        print(xyzPos)
        self.galaxies[self.counter].setPos(*xyzPos)
        self.galaxies[self.counter].setColor(*self.startColor)
        self.galaxyDistances[self.counter] = [xyzPos, self.startWavelength]

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
            self.planet.setColor(90.3, 259.3, 0.2, 1)

            print('loaded planet')
        except:
            print('failed to load planet')
   
    ########### DRAW TERRAIN ####################
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
        for xPos in range(-(3*self.blenderPlaneDim),3*self.blenderPlaneDim+1,self.blenderPlaneDim):
            for yPos in range (-self.blenderPlaneDim,self.blenderPlaneDim*3+1,self.blenderPlaneDim):

                self.land[self.landCounter] = render.attachNewNode(str(self.landCounter))
                self.land[self.landCounter].setPos(xPos,yPos,zPos)
                self.land[self.landCounter].setHpr(0 , 0 , 0)
                self.land[self.landCounter].reparentTo(base.camera)
                self.land[self.landCounter].reparentTo(self.landRoot)

                land = loader.loadModel('modelsMisc/land')
                land.reparentTo(self.land[self.landCounter])
                
                num = random.randint(1,6)
                land.setTexture(self.starTexture)
                land.setPos(0,0,0)
                
                interval = self.blenderPlaneDim/2
                #choose to draw forest 
                num = random.randint(0,2)
                if num==0:
                    #choose random position in land 
                    center = self.getRandPos(0,0,0,interval) #may want to change range

                    #get number of trees
                    numTrees = random.randint(4,15)
                    self.makeTrees(numTrees,center,0,0,0)
                elif num==1: #make a plateau mountain
                    center = self.getRandPos(0,0,0,interval-1)
                    numLayers = random.randint(3,7)
                    self.makePlateau(numLayers, center)

                self.landCounter += 1
        terrain = GeoMipTerrain("mySimpleTerrain")
        terrain.setHeightfield("heightMap.jpg")
        #terrain.setBruteforce(True)
        terrain.getRoot().reparentTo(self.landRoot)
        terrain.generate()

    def makePlateau(self,numLayers,center):
        x,y,z = center 
        plateauHeight = 0.2
        startScale = self.selectFloat(0.05,0.2)
        #numLayers=1 #
        rotation = random.randint(0,360)
        for plateau in range(numLayers):
            scale = 2 - math.log(plateau+1) #doesnt work past 9 !!!
            self.loadPlateau(x,y,z,scale,startScale,rotation)
            z+=plateauHeight*startScale*scale
    
    def loadPlateau(self,x,y,z,scale,startScale,rotation):
        plateau = loader.loadModel('modelsMisc/splineSurface')
        plateau.reparentTo(self.land[self.landCounter])
        plateau.setPos(x,y,z)
        plateau.setColor(0.4,0.5,0.2,1)
        plateau.setHpr(rotation,0,0)
        realScale = startScale * scale
        plateau.setScale(realScale)

    def makeTrees(self,numTrees, center, xPos,yPos,zPos):
        #first generate positions around the center, within bounds, don't intersect with tree radiuses
        bound = self.blenderPlaneDim/2
        positions = set()
        treeRadius = 1.5 
        treeScale = 0.03
        x,y,z = center
        for tree in range(numTrees):
            notFound = True
            while notFound:
                tryPos = self.getRandPos(x,y,z, treeRadius)
                if tryPos[0]>(xPos-bound) and tryPos[0]<(xPos+bound) and tryPos[1]>(yPos-bound) and tryPos[1]<(yPos+bound):
                    notFound = False 
                    positions.add(tryPos)
                    x,y,z = tryPos
        for position in positions:
            xf,yf,zf = position
            self.loadTree(xf,yf,zf, treeScale)

    def loadTree(self,x,y,z,scale):
        #!!!!!! tree1 -> other possible trees - string formatting
        num = random.randint(1,4)
        tree = loader.loadModel('modelsMisc/tree%d' % (num))
        tree.reparentTo(self.land[self.landCounter])
        tree.setTexture(self.treeTexture)
        tree.setPos(x,y,z)
        tree.setScale(scale)
        rotation = random.randint(0,360)
        tree.setHpr(rotation,0,0)
        #tree.setShaderInput("texDisable", 1, 1, 1, 1)

    

    ############## Unused Code ##################
    
app=MyApp()
app.run()

