import math
import random
#vars = 0,1
#axiom = 0
# constant [,]
#rules - 1 > 1,1
######## 0 > 1[0]0

#store width of trunk as well 
#change axiom to use rotation matrices??
#https://generativelandscapes.wordpress.com/2014/09/23/adding-detail-to-a-region-forests-example-20-6/
#http://www.allenpike.com/images/461/lsystem.python
##^dont include

#spherical coordinates ref: http://mathworld.wolfram.com/SphericalCoordinates.html


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
    if level == 2:
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
    currPhi = 0
    currTheta = 180
    pointList= []
    prev = None
    temp1, prev = None, None
    popList = []
    depth = 0
    for i in instructions:
        if prev == 1 and i!='1':
            #string of 1's has ended, draw 
            point, currTheta = getEnd(start, temp1, currPhi, currTheta, length, len(popList))
            pointList.append((start,point,depth, currPhi, currTheta)) # tuple of tuples!
            #print(pointList)
            temp1, prev = None, None
            start = point #?????
        elif i == '1':
            if temp1 == None: 
                temp1 = 1
                prev = 1
            else: temp1+=1
        elif i == '0': 
            #print(currPhi)
            #theta thing is v wrong... dont care about ending
            point, randTheta= getEnd(start, 1, currPhi, currTheta, length, len(popList)) #start is right?
            pointList.append((start, point, depth,currPhi, randTheta))
            prev = None
            #print(pointList)
        if i == '[':
            # add to poplist, change dir 
            popList.append((start, currPhi, currTheta))
            depth+=1
            currPhi-=45
            prev = None
        elif i == ']':
            #currTheta-=180
            start, currPhi, currTheta = popList.pop()
            currPhi +=45
            prev = None
        elif i == '{':
            popList.append((start,currPhi, currTheta))
            depth += 1
            currPhi +=30
            prev = None 
        elif i == '}':
            start, currPhi, currTheta = popList.pop()
            depth-=1
            prev = None
    return pointList




def getEnd(start, temp1, currPhi, currTheta, length, depth):
    if depth > 0:
        branchRatio = (1/depth)*2
        thetaInterval = 50  # can increas??
        theta = random.randint(currTheta - thetaInterval, currTheta + thetaInterval)
    else: 
        branchRatio = 1
        theta = currTheta
    hypot = temp1*length*branchRatio
    
    
    radPhi = (currPhi*math.pi)/180
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

print(points)