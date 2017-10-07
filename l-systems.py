import math
#vars = 0,1
#axiom = 0
# constant [,]
#rules - 1 > 1,1
######## 0 > 1[0]0

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
            if elem == '1':
                newAxiom += '11'
            elif elem == '0': `
                newAxiom += '1[0]0'
            else: 
                newAxiom += elem 
        return getDirString(newAxiom, level+1)

def getPoints(instructions, length):
    start = (0,0)
    currDir = 90
    pointList= []
    prev = None
    temp1, prev = None, None
    popList = []
    for i in instructions:
        print(i)
        if prev == 1 and i!='1':
            #string of 1's has ended, draw 
            point = getEnd(start, temp1, currDir, length)
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
            print(currDir)
            point = getEnd(start, 1, currDir, length) #start is right?
            pointList.append((start, point))
            prev = None
            #print(pointList)
        if i == '[':
            # add to poplist, change dir 
            popList.append((start, currDir))
            currDir-=45
            prev = None
        elif i == ']':
            start, currDir = popList.pop()
            currDir +=45
            prev = None
    return pointList




def getEnd(start, temp1, currDir, length):
    hypot = temp1*length 
    rad = (currDir*math.pi)/180
    x= math.cos(rad)* hypot
    y = math.sin(rad)* hypot 
    return (start[0]+x,start[1]+y)


points = (returnPointList())

for i in points:
    print(i)