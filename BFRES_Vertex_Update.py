import sys
import struct
import array
import binascii

class poly(object):
        def __init__(self):
                self.name = ""
                self.verts = []
                self.normals = []
                self.colors =[]
                self.uv0 = []
                self.uv1 = []
                self.uv2 = []
                self.uv3 = []
                self.faces = []
                self.boneName = []
                self.boneI = []
                self.boneW = []

polys = []

cvsIn = open(sys.argv[2], "r")

curPoly = 0

ii = 0
for line in cvsIn:
    if line.startswith("Obj Name"):
            if(ii > 0):
                polys.append(data)
            data = poly()
            data.name = line.split(":")[1].replace("\n", "")
            ii += 1
            SubType = 0
    elif line.startswith("tex_Array:"):
        pass
    elif line.startswith("Bone_Suport"):
        pass
    elif line.startswith("Color_Suport"):
        colorEnable = True
    elif line.startswith("UV_Num:"):
        numUVs = int(line.split(":")[1].replace("\n", ""))
    elif line.startswith("vert_Array"):
        Type = 1
    elif line.startswith("face_Array"):
        Type = 2
    elif line.startswith("bone_Array"):
        Type = 3
    else:
        line = line.replace("\n", "").replace("\r", "").split(",")
        if(Type == 1):
            if(SubType == 0):
                data.verts.append(line)
                SubType += 1
            elif(SubType == 1):
                data.normals.append(line)
                SubType += 1
            elif(SubType == 2):
                data.colors.append(line)
                SubType += 1
            elif(SubType == 3):
                data.uv0.append(line)
                if(numUVs == 1):SubType = 0
                else:SubType += 1
            elif(SubType == 4):
                data.uv1.append(line)
                if(numUVs == 2):SubType = 0
                else:SubType += 1
            elif(SubType == 5):
                data.uv2.append(line)
                if(numUVs == 3):SubType = 0
                else:SubType += 1
            elif(SubType == 6):
                data.uv3.append(line)
                SubType = 0
        elif(Type == 2):
            data.faces.append(line)
        elif(Type == 3):
            line.pop()
            bbs = 0
            StrNames = []
            BonArry = []
            for obj in line:
                    
                    if(bbs == 0):
                            StrNames.append(obj)
                            bbs += 1
                    else:
                            BonArry.append(float(obj))
                            bbs = 0
            data.boneName.append(StrNames)
            data.boneW.append(BonArry)
            
polys.append(data)


def compress(float32):
    F16_EXPONENT_BITS = 0x1F
    F16_EXPONENT_SHIFT = 10
    F16_EXPONENT_BIAS = 15
    F16_MANTISSA_BITS = 0x3ff
    F16_MANTISSA_SHIFT =  (23 - F16_EXPONENT_SHIFT)
    F16_MAX_EXPONENT =  (F16_EXPONENT_BITS << F16_EXPONENT_SHIFT)

    a = struct.pack('>f',float32)
    b = binascii.hexlify(a)

    f32 = int(b,16)
    f16 = 0
    sign = (f32 >> 16) & 0x8000
    exponent = ((f32 >> 23) & 0xff) - 127
    mantissa = f32 & 0x007fffff

    if exponent == 128:
        f16 = sign | F16_MAX_EXPONENT
        if mantissa:
            f16 |= (mantissa & F16_MANTISSA_BITS)
    elif exponent > 15:
        f16 = sign | F16_MAX_EXPONENT
    elif exponent > -15:
        exponent += F16_EXPONENT_BIAS
        mantissa >>= F16_MANTISSA_SHIFT
        f16 = sign | exponent << F16_EXPONENT_SHIFT | mantissa
    else:
        f16 = sign
    return f16


def decompress(h):
    s = int((h >> 15) & 0x00000001)    # sign
    e = int((h >> 10) & 0x0000001f)    # exponent
    f = int(h & 0x000003ff)            # fraction

    if e == 0:
       if f == 0:
          return int(s << 31)
       else:
          while not (f & 0x00000400):
             f <<= 1
             e -= 1
          e += 1
          f &= ~0x00000400
    elif e == 31:
       if f == 0:
          return int((s << 31) | 0x7f800000)
       else:
          return int((s << 31) | 0x7f800000 | (f << 13))

    e = e + (127 -15)
    f = f << 13

    return int((s << 31) | (e << 23) | f)

def readByte(file):
    return struct.unpack("B", file.read(1))[0]
 
def readu16be(file):
    return struct.unpack(">H", file.read(2))[0]
 
def readu16le(file):
    return struct.unpack("<H", file.read(2))[0]

def readu32be(file):
    return struct.unpack(">I", file.read(4))[0]
 
def readu32le(file):
    return struct.unpack("<I", file.read(4))[0]
 
def readfloatbe(file):
    return struct.unpack(">f", file.read(4))[0]
 
def readfloatle(file):
    return struct.unpack("<f", file.read(4))[0]

def readhalffloatbe(file):
    v = readu16be(file)
    x = decompress(v)
    str = struct.pack('I',x)
    f = struct.unpack('f',str)[0]
    return float(f)

def updateDamit(file):
    file.seek(0,1)

def writefloatbe(file,val):
    file.write(struct.pack(">f", val))
    updateDamit(file)
def writehalffloatbe(file,val):
    half = compress(val)
    file.write(struct.pack(">H", half))
    updateDamit(file)

def ReadOffset(file):
    offset = file.tell()
    return (offset + readu32be(file))

def getString(file):
    result = ""
    tmpChar = file.read(1)
    while ord(tmpChar) != 0:
        result += str(tmpChar).replace("b", "").replace("'", "")
        tmpChar =file.read(1)
    return result

class fmdlh:
    def __init__(self,file):
        self.fmdl = file.read(4)
        self.fnameOff = ReadOffset(file)
        self.eofString = ReadOffset(file)
        self.fsklOff = ReadOffset(file)
        self.fvtxArrOff = ReadOffset(file)
        self.fshpIndx = ReadOffset(file)
        self.fmatIndx = ReadOffset(file)
        self.paramOff = ReadOffset(file)
        self.fvtxCount = readu16be(file)
        self.fshpCount = readu16be(file)
        self.fmatCount = readu16be(file)
        self.paramCount = readu16be(file)
class fvtxh:
    def __init__(self,file):
        self.fmdl = file.read(4)
        self.attCount = readByte(file)
        self.buffCount = readByte(file)
        self.sectIndx = readu16be(file)
        self.vertCount = readu32be(file)
        self.u1 = readu16be(file)
        self.u2 = readu16be(file)
        self.attArrOff = ReadOffset(file)
        self.attIndxOff = ReadOffset(file)
        self.buffArrOff = ReadOffset(file)
        self.padding = readu32be(file)
class fmath:
    def __init__(self,file):
        self.fmat = file.read(4)
        self.matOff = ReadOffset(file)
        self.u1 = readu32be(file)
        self.sectIndx = readu16be(file)
        self.rendParamCount = readu16be(file)
        self.texSelCount = readByte(file)
        self.texAttSelCount = readByte(file)
        self.matParamCount = readu16be(file)
        self.matParamSize = readu32be(file)
        self.u2 = readu32be(file)
        self.rendParamIndx = ReadOffset(file)
        self.unkMatOff = ReadOffset(file)
        self.shadeOff = ReadOffset(file)
        self.texSelOff = ReadOffset(file)
        self.texAttSelOff = ReadOffset(file)
        self.texAttIndxOff = ReadOffset(file)
        self.matParamArrOff = ReadOffset(file)
        self.matParamIndxOff = ReadOffset(file)
        self.matParamOff = ReadOffset(file)
        self.shadParamIndxOff = ReadOffset(file)

class fsklh:
    def __init__(self,file):
        self.fskl = file.read(4)
        self.u1 = readu16be(file)
        self.fsklType = readu16be(file)
        self.boneArrCount = readu16be(file)
        self.invIndxArrCount = readu16be(file)
        self.exIndxCount = readu16be(file)
        self.u3 = readu16be(file)
        self.boneIndxOff = ReadOffset(file)
        self.boneArrOff = ReadOffset(file)
        self.invIndxArrOff = ReadOffset(file)
        self.invMatrArrOff = ReadOffset(file)
        self.padding = readu32be(file)

class fshph:
    def __init__(self,file):
        self.fshp = file.read(4)
        self.polyNameOff = ReadOffset(file)
        self.u1 = readu32be(file)
        self.fvtxIndx = readu16be(file)
        self.fmatIndx = readu16be(file)
        self.fsklIndx = readu16be(file)
        self.sectIndx = readu16be(file)
        self.fsklIndxArrCount = readu16be(file)
        self.matrFlag = readByte(file)
        self.lodMdlCount = readByte(file)
        self.visGrpCount = readu32be(file)
        self.u3 = readfloatbe(file)
        self.fvtxOff = ReadOffset(file)
        self.lodMdlOff = ReadOffset(file)
        self.fsklIndxArrOff = ReadOffset(file)
        self.u4 = readu32be(file)
        self.visGrpNodeOff = ReadOffset(file)
        self.visGrpRangeOff = ReadOffset(file)
        self.visGrpIndxOff = ReadOffset(file)
        self.u5 = readu32be(file)

class attdata:
    def __init__(self,attName,buffIndx,buffOff,vertType):
        self.attName = attName
        self.buffIndx = buffIndx
        self.buffOff = buffOff
        self.vertType = vertType
class buffData:
    def __init__(self,buffSize,strideSize,dataOffset):
        self.buffSize = buffSize
        self.strideSize = strideSize
        self.dataOffset = dataOffset

def writeByte(file,val):
    file.write(struct.pack("B", val))
    updateDamit(file)
def write16be(file,val):
    file.write(struct.pack(">H", val))
    updateDamit(file)
def writes16be(file,val):
    file.write(struct.pack(">h", val))
    updateDamit(file)
def write32be(file,val):
    file.write(struct.pack(">I", val))
    updateDamit(file)
def write10be(file,x,y,z):
        x *= -1
        y *= -1
        z *= -1
        x -= 1
        y -= 1
        z -= 1
        x = ~x
        y = ~y
        z = ~z
        x = 0x3ff & x
        y = 0x3ff & y
        z = 0x3ff & z
        x = x<<0
        y = y<<10
        z = z<<20
        base = x + y + z
        write32be(file,base)
f = open(sys.argv[1], "rb+")

AllVerts = []

f.seek(5)
verNum = readByte(f)
print(verNum)
f.seek(26,1)
FileOffset = ReadOffset(f)
f.seek(FileOffset)
BlockSize = readu32be(f)
FMDLTotal = readu32be(f)
f.seek(0x10,1)


for mdl in range(FMDLTotal):
    f.seek(12,1)
    FMDLOffset = ReadOffset(f)
    NextFMDL = f.tell()
    f.seek(FMDLOffset)

    GroupArray = []
    FMDLArr = []
    FVTXArr = []
    FSKLArr = []
    FMATArr = []
    FMATNameArr = []
    FSHPArr = []
    VTXAttr = []
	
    BoneArray = []
    BoneFixArray = []
    invIndxArr = []
    invMatrArr = []
    Node_Array = []

    #F_Model Header
    fmdl_info = fmdlh(f)
    FMDLArr.append(fmdl_info)
    #F_Vertex Header
    f.seek(fmdl_info.fvtxArrOff)
    for vtx in range(fmdl_info.fvtxCount):FVTXArr.append(fvtxh(f))
    f.seek(fmdl_info.fmatIndx)
    f.seek(24,1)
    #F_Material Header
    for mat in range(fmdl_info.fmatCount):
        f.seek(8,1)
        FMATNameOffset = ReadOffset(f)
        Rtn = f.tell()
        f.seek(FMATNameOffset)

        FMATNameArr.append(getString(f))
        f.seek(Rtn)

        FMATOffset = ReadOffset(f)
        Rtn = f.tell()

        f.seek(FMATOffset)
        FMATArr.append(fmath(f))
        f.seek(Rtn)
    #F_Skeleton Header
    f.seek(fmdl_info.fsklOff)
    fskl_info = fsklh(f)
    FSKLArr.append(fskl_info)

    #Get Bone names
    BoneNameArray = []
    f.seek(fskl_info.boneArrOff)
    for bonz in range(fskl_info.boneArrCount):
            #print(hex(f.tell()))
            boneOffset = ReadOffset(f)
            rtn = f.tell() + 0x3c
            f.seek(boneOffset)
            BoneNameArray.append(getString(f))
            if(verNum <= 2):rtn += 48
            f.seek(rtn)


    OptimizedBoneInd = []
    #Node Setup
    f.seek(fskl_info.invIndxArrOff)
    for nodes in range(fskl_info.invIndxArrCount + fskl_info.exIndxCount):Node_Array.append(readu16be(f))
    for thing in Node_Array:
            OptimizedBoneInd.append(BoneNameArray[thing])
    #print(BoneNameArray)
    #print(OptimizedBoneInd)
    for pol in polys:
            pol.boneI = []
            
            for nams in pol.boneName:
                    boneInx = []
                    for nnn in nams:
                            for b,boneName in enumerate(OptimizedBoneInd):
                                    if nnn == boneName:
                                            boneInx.append(b)
                    pol.boneI.append(boneInx)
            #print(pol.boneI)
    #print(polys[0].boneName)
                                    

    #F_Shape Header
    f.seek(fmdl_info.fshpIndx + 24)
    for shp in range(fmdl_info.fshpCount):
        f.seek(12,1)
        #print(hex(f.tell()))
        FSHPOffset = ReadOffset(f)
        Rtn = f.tell()

        f.seek(FSHPOffset)
        
        FSHPArr.append(fshph(f))
        f.seek(Rtn)

    #Mesh Building

    for m in range(len(FSHPArr)):
            

        f.seek(FSHPArr[m].polyNameOff)
        #print(FSHPArr[m].polyNameOff)
        MeshName = getString(f)
        print(MeshName)

        f.seek(FVTXArr[FSHPArr[m].fvtxIndx].attArrOff)
        AttrArr = []
        for att in range(FVTXArr[FSHPArr[m].fvtxIndx].attCount):
            AttTypeOff = ReadOffset(f)
            Rtn1 = f.tell()
            f.seek(AttTypeOff)
            AttType = getString(f)
            f.seek(Rtn1)
            buffIndx = readByte(f)
            skip = readByte(f)
            buffOff = readu16be(f)
            vertType = readu32be(f)
            AttrArr.append(attdata(AttType,buffIndx,buffOff,vertType))
        BuffArr = []
        f.seek(FVTXArr[FSHPArr[m].fvtxIndx].buffArrOff)
        for buf in range(FVTXArr[FSHPArr[m].fvtxIndx].buffCount):
            f.seek(4,1)
            BufferSize = readu32be(f)
            f.seek(4,1)
            StrideSize = readu16be(f)
            f.seek(6,1)
            DataOffset = ReadOffset(f)
            BuffArr.append(buffData(BufferSize,StrideSize,DataOffset))

        f.seek(FSHPArr[m].lodMdlOff + 4)
        
        faceType = readu32be(f)
        f.seek(0xC,1)
        indxBuffOff = ReadOffset(f)
        f.seek(0x4,1)
        f.seek(indxBuffOff + 4)
        FaceCount = readu32be(f)
        f.seek(12,1)
        FaceBuffer = ReadOffset(f)
        enablePop = True
        pp = poly()
        p = 0
        if(len(polys)>0):
                while(enablePop):
                        if(MeshName == polys[p].name):
                               print("A Match! %s" % polys[p].name)
                               pp = polys.pop(p)
                               enablePop = False
                        p += 1
                        if(len(polys)<=p):
                              enablePop = False  
        print(len(BuffArr))

        for v in range(FVTXArr[FSHPArr[m].fvtxIndx].vertCount):
                for attr in range(len(AttrArr)):
                        f.seek(((BuffArr[AttrArr[attr].buffIndx].dataOffset) + (AttrArr[attr].buffOff) + (BuffArr[AttrArr[attr].buffIndx].strideSize * v)))
                        if(len(pp.verts) > v):
                                #print(pp.verts[v])
                                vert = pp.verts[v]
                                uv0 = pp.uv0[v]
                                if(len(pp.uv1)>v):
                                        uv1 = pp.uv1[v]
                                else:
                                        uv1 = [0,0]
                                if(len(pp.uv2)>v):
                                        uv2 = pp.uv2[v]
                                else:
                                        uv2 = [0,0]
                                norm = pp.normals[v]
                                color0 = pp.colors[v]
                                if(len(pp.boneI)>v):
                                        binx = pp.boneI[v]
                                        bwgt = pp.boneW[v]
                                else:
                                        binx = [0]
                                        bwgt = [1.0]
                        else:
                                vert = [0,0,0]
                                uv0 = [0,0]
                                uv1 = [0,0]
                                uv2 = [0,0]
                                norm = [1,1,1]
                                binx = [0]
                                bwgt = [1.0]
                                color0 = [127,127,127,127]
                        if(AttrArr[attr].attName == "_p0"):
                                #print(hex(f.tell()))
                                if(AttrArr[attr].vertType == 2063):
                                    #print(hex(f.tell()))
                                    for vt in vert:writehalffloatbe(f,float(vt)) 
                                elif(AttrArr[attr].vertType == 2065):
                                    #print(hex(f.tell()))
                                    for vt in vert:writefloatbe(f,float(vt))
                                else:print("Unk Vertex attr:%s" % hex(AttrArr[attr].vertType))
                        if(AttrArr[attr].attName == "_n0"):
                                if(AttrArr[attr].vertType == 523):
                                        write10be(f,int(float(norm[0])*511),int(float(norm[1])*511),int(float(norm[2])*511))
                        if(AttrArr[attr].attName == "_c0"):
                                if(AttrArr[attr].vertType == 10):
                                        for clr in color0:
                                               writeByte(f,int(float(clr)))
                                if(AttrArr[attr].vertType == 2063):
                                        for clr in color0:
                                               writeByte(f,float(clr)/255)
                        if(AttrArr[attr].attName == "_u0"):
                                if(AttrArr[attr].vertType == 2061):
                                        writefloatbe(f,float(uv0[0]))
                                        writefloatbe(f,float(uv0[1])*-1)
                                elif(AttrArr[attr].vertType == 2056):
                                        writehalffloatbe(f,float(uv0[0]))
                                        writehalffloatbe(f,(float(uv0[1])*-1))
                                elif(AttrArr[attr].vertType == 519):
                                        writes16be(f,int(float(uv0[0])*32767))
                                        vvv = (float(uv0[1])*-1)+1
                                        writes16be(f,int(vvv*32767))
                                elif(AttrArr[attr].vertType == 7):
                                        write16be(f,int(float(uv0[0])*65535))
                                        vvv = (float(uv0[1])*-1)+1
                                        write16be(f,int(vvv*65535))
                                elif(AttrArr[attr].vertType == 4 or AttrArr[attr].vertType == 516):
                                        writeByte(f,int(float(uv0[0])*255))
                                        vvv = (float(uv0[1])*-1)+1
                                        writeByte(f,int(vvv*255))
                                else:
                                        print("Unk %i for _u0" % AttrArr[attr].vertType)
                        if(AttrArr[attr].attName == "_u1"):
                                if(AttrArr[attr].vertType == 2061):
                                        writefloatbe(f,float(uv1[0]))
                                        writefloatbe(f,float(uv1[1])*-1)
                                elif(AttrArr[attr].vertType == 2056):
                                        writehalffloatbe(f,float(uv1[0]))
                                        writehalffloatbe(f,(float(uv1[1])*-1))
                                elif(AttrArr[attr].vertType == 519):
                                        writes16be(f,int(float(uv1[0])*32767))
                                        vvv = (float(uv1[1])*-1)+1
                                        writes16be(f,int(vvv*32767))
                                elif(AttrArr[attr].vertType == 7):
                                        write16be(f,int(float(uv1[0])*65535))
                                        vvv = (float(uv1[1])*-1)+1
                                        write16be(f,int(vvv*65535))
                                elif(AttrArr[attr].vertType == 4 or AttrArr[attr].vertType == 516):
                                        writeByte(f,int(float(uv1[0])*255))
                                        vvv = (float(uv1[1])*-1)+1
                                        writeByte(f,int(vvv*255))
                                else:
                                        print("Unk %i for _u1" % AttrArr[attr].vertType)
                        if(AttrArr[attr].attName == "_u2"):
                                if(AttrArr[attr].vertType == 2061):
                                        writefloatbe(f,float(uv2[0]))
                                        writefloatbe(f,float(uv2[1])*-1)
                                elif(AttrArr[attr].vertType == 2056):
                                        writehalffloatbe(f,float(uv2[0]))
                                        writehalffloatbe(f,(float(uv2[1])*-1))
                                elif(AttrArr[attr].vertType == 519):
                                        writes16be(f,int(float(uv2[0])*32767))
                                        vvv = (float(uv2[1])*-1)+1
                                        writes16be(f,int(vvv*32767))
                                elif(AttrArr[attr].vertType == 7):
                                        write16be(f,int(float(uv2[0])*65535))
                                        vvv = (float(uv2[1])*-1)+1
                                        write16be(f,int(vvv*65535))
                                elif(AttrArr[attr].vertType == 4 or AttrArr[attr].vertType == 516):
                                        writeByte(f,int(float(uv2[0])*255))
                                        vvv = (float(uv2[1])*-1)+1
                                        writeByte(f,int(vvv*255))
                                else:
                                        print("Unk %i for _u2" % AttrArr[attr].vertType)
                        if(AttrArr[attr].attName == "_i0"):
                                if(AttrArr[attr].vertType == 266):
                                        for iii in range(4):
                                                if(len(binx)<(iii+1)):
                                                        writeByte(f,0)
                                                else:
                                                        writeByte(f,binx[iii])
                                elif(AttrArr[attr].vertType == 260):
                                        for iii in range(2):
                                                if(len(binx)<(iii+1)):
                                                        writeByte(f,0)
                                                else:
                                                        writeByte(f,binx[iii])
                                elif(AttrArr[attr].vertType == 256):
                                        writeByte(f,binx[0])
                                else:print("Unk %i for _i0" % AttrArr[attr].vertType)
                                        
                        if(AttrArr[attr].attName == "_w0"):
                                if(AttrArr[attr].vertType == 10):
                                        maxWeght = 255
                                        for iii in range(4):
                                                #print("WGT%i\nRemaining Weight:%i" % (iii,maxWeght))
                                                if(len(bwgt)<(iii+1)):
                                                        writeByte(f,0)
                                                        maxWeght = 0
                                                else:
                                                        valWeght = int(bwgt[iii]*255)
                                                        if(len(bwgt) == iii+1):
                                                                valWeght = maxWeght
                                                        if(valWeght>=maxWeght):
                                                                #print("haythere")
                                                                valWeght = maxWeght
                                                                maxWeght = 0
                                                        else:
                                                                maxWeght -= valWeght
                                                        writeByte(f,valWeght)
                                if(AttrArr[attr].vertType == 4):
                                        maxWeght = 255
                                        for iii in range(2):
                                                if(len(bwgt)<(iii+1)):
                                                        writeByte(f,maxWeght)
                                                        maxWeght = 0
                                                else:
                                                        valWeght = (bwgt[iii]*255)
                                                        if(valWeght>maxWeght):
                                                                valWeght = maxWeght
                                                                maxWeght = 0
                                                        else:
                                                                maxWeght -= valWeght
                                                        writeByte(f,valWeght)
                                                
                                #print("UV Type:%d" % AttrArr[attr].vertType)

        

        f.seek(FaceBuffer)
        
                
        print("Myobj Face Count is %i" % len(pp.faces))
        if(len(pp.verts) > 0):
                if faceType == 4:
                        for ff in range(int(FaceCount/6)):
                                if(len(pp.faces) > ff):
                                        #print(pp.faces[ff])
                                        face = pp.faces[ff]    
                                else:
                                        face = [1,2,3]
                                for point in face:
                                        write16be(f,int(float(point))-1)
                if faceType == 9:
                        for ff in range(FaceCount/12):
                                if(len(pp.faces) > ff):face = pp.faces[ff]    
                                else:face = [1,2,3]
                                for point in face:
                                        write32be(f,int(float(point))-1)

    f.seek(NextFMDL)

f.close()
