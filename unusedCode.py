    def drawSlider(self):
        format = GeomVertexFormat.getV3()
        vdata = GeomVertexData('vertices', format, Geom.UHStatic)
        vdata.setNumRows(4)

        vertexWriter = GeomVertexWriter(vdata, 'vertex') #change?
        vertexWriter.addData3f(0,0,0)
        vertexWriter.addData3f(1,0,0)
        vertexWriter.addData3f(1,0,1)
        vertexWriter.addData3f(0,0,1)

        tris=GeomTriangles(Geom.UHStatic)
        tris.addVertex(0)
        tris.addVertex(1)
        tris.addVertex(3) #?why skip

        tris.closePrimitive()

        tris.addConsecutiveVertices(1,3) #range
        tris.closePrimitive()

        squareGeom = Geom(vdata)
        squareGeom.addPrimitive(tris)

        squareGN=GeomNode('square')
        squareGN.addGeom(squareGeom)
        sq=render.attachNewNode(squareGN)
        sq.setPos(1,40,0)