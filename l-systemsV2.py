import math
import random
#vars = 0,1
#axiom = 0
# constant [,]
#rules - 1 > 1,1
######## 0 > 1[0]0

rules = {}
rules['1'] = '11'
rules['0'] = '1{0}1[0]0'
#rules['0'] = '1[0]0'

def returnPointList():
    axiom1 = '0' 
    startLevel = 0 
    length = 1
    #pointList = []

    instructions = getDirString(axiom1, startLevel)
    print(instructions)

    return getPoints(instructions, length)
    #print(pointList)


    #print(instructions)
def getDirString(axiom, level):
    if level == 3:
        return axiom
    else: 
        newAxiom = ''
        for elem in axiom:
            if elem in rules: 
                newAxiom+= rules[elem]
            else: 
                newAxiom += elem 
        return getDirString(newAxiom, level+1)

def getPoints(instructions, length):
    start = (0,0,0)
    currDir = 90
    currTheta = 180
    pointList= []
    prev = None
    temp1, prev = None, None
    popList = []
    for i in instructions:
        print(i)
        if prev == 1 and i!='1':
            #string of 1's has ended, draw 
            point, currTheta = getEnd(start, temp1, currDir, currTheta, length, len(popList))
            pointList.append((start,point)) # tuple of tuples!
            #print(pointList)
            temp1, prev = None, None
            start = point #?????
        elif i == '1':
            if temp1 == None: 
                temp1 = 1
                prev = 1
            else: temp1+=1
        elif i == '0': 
            #print(currDir)
            #theta thing is v wrong... dont care about ending
            point, randTheta= getEnd(start, 1, currDir, currTheta, length, len(popList)) #start is right?
            pointList.append((start, point))
            prev = None
            #print(pointList)
        if i == '[':
            # add to poplist, change dir 
            popList.append((start, currDir, currTheta))
            currDir-=45
            prev = None
        elif i == ']':
            #currTheta-=180
            start, currDir, currTheta = popList.pop()
            currDir +=45
            prev = None
        elif i == '{':
            popList.append((start,currDir, currTheta))
            currDir +=30
            prev = None 
        elif i == '}':
            start, currDir, currTheta = popList.pop()
            prev = None
    return pointList




def getEnd(start, temp1, currDir, currTheta, length, depth):
    if depth > 1:
        branchRatio = (1/depth)*2
        thetaInterval = 50  # can increas??
        theta = random.randint(currTheta - thetaInterval, currTheta + thetaInterval)
    else: 
        branchRatio = 1
        theta = currTheta
    hypot = temp1*length*branchRatio
    
    phi = currDir
    while phi < 0:
        phi +=360
    if phi>270:
        phi = 360 - phi
    else:
        phi = abs(phi-90)
    print('phi', currDir, phi)
    radPhi = (phi*math.pi)/180
    radTheta = (theta*math.pi)/180

    x = hypot * math.cos(radTheta)*math.sin(radPhi)
    y = hypot * math.sin(radTheta)*math.sin(radPhi)
    z = hypot * math.cos(radPhi)
    x = round(x + start[0],3)
    y = round(y + start[1],3)
    z = round(z + start[2],3)
    if almostEqual(x,0): x = 0
    if almostEqual(y,0): y = 0
    if almostEqual(z,0): y = 0
    return (x,y,z), theta

def almostEqual(d1,d2, epsilon = 10**-7):
    return abs(d1-d2)<epsilon

points = (returnPointList())

for i in points:
    print(i)