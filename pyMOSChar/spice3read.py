import struct
import re
import numpy as np
import collections
import pdb

def split(plotDat):
    """ Converts each of the arrays in plotDat into 2-D arrays
    where the first index corresponds to the parameter being swept.
    """
    pdb.set_trace()
    sweep = plotDat[list(plotDat.keys())[0]]
    splitPos = np.argwhere(sweep == sweep[0])
    nSplits = len(splitPos)
    
    plotDatSplit = collections.OrderedDict()
    keys = plotDat.keys()
    
    splitPtr = 0;
    splitPos = np.append(splitPos, len(sweep))
    # pdb.set_trace()
    for key in keys:
        plotDatSplit[key] = np.zeros((nSplits, len(plotDat[key])// nSplits))
        for splitPtr in range(nSplits):
            plotDatSplit[key][splitPtr] = plotDat[key][splitPos[splitPtr]:splitPos[splitPtr + 1]]
    
    return plotDatSplit

def read(filename):
    """
        https://lab4sys.com/en/reading-spice-outputs-with-python/?cn-reloaded=1
    """
    f = open(filename,"r")
    lignes = f.readlines()
    k = 0
    while not re.match("-+",lignes[k]):
        print(lignes[k])
        k += 1
    k += 1
    entete =lignes[k].strip()
    champs = re.split("\s+",entete)
    print(champs)
    k += 2
    ligne = lignes[k].strip()
    valeurs = re.split("\s+",ligne)
    complexes = []
    data = {}
    j = 0
    for i in range(len(champs)):
        valeurs[i] = valeurs[i].strip()
        if valeurs[j][len(valeurs[j])-1] == ",":
            complexes.append(True)
            j += 2
            data[champs[i]] = numpy.zeros(0,numpy.complex128)
        else:
            complexes.append(False)
            j += 1
            data[champs[i]] = numpy.zeros(0,numpy.float64)
    index = 0
    while k < len(lignes):
        ligne = lignes[k].strip()
        if re.match("^[\d+]",ligne):
            valeurs = re.split("\s+",ligne)
            j = 0
            for i in range(len(champs)):
                if complexes[i]:
                    valeurs[j]= valeurs[j][:len(valeurs[2])-1]
                    valeurs[j]= valeurs[j].replace(",",".")
                    valeurs[j+1]= valeurs[j+1].replace(",",".")
                    data[champs[i]] = numpy.append(data[champs[i]],complex(float(valeurs[j]),float(valeurs[j+1])))
                    j += 2
                else:
                    valeurs[j]= valeurs[j].replace(",",".")
                    data[champs[i]] = numpy.append(data[champs[i]],float(valeurs[j]))
                    j += 1
        k += 1
    f.close()
    return data
            
def read2(fileName, simulator="ngspice"):
    """ Reads a SPICE3RAW file and stores the data. Returns an ordered
    dictionary containing 2D arrays of simulated data. 2D arrays are used in
    case the simulation is parametric.

    Arguments:
    filename : A valid SPICE3 rawfile
    """
    rawFile = open(fileName, 'rb')
    dataBytes = rawFile.read()
    dataStr = str(dataBytes)
    
    simStarts = [m.start() for m in re.finditer('Title', dataStr)]
    
    plotDat = collections.OrderedDict()
    
    for startPtr in simStarts:
        flagStart = dataBytes.find(b'Flags: ', startPtr) + len('Flags: ')
        flags = dataBytes[flagStart:flagStart+4].decode()
        
        if flags == 'real':
        
            # Extract the number of variables
            startPos = dataBytes.find(b'No. Variables: ', startPtr) + len('No. Variables: ')
            endPos = dataBytes.find(b'No. Points:', startPtr)
            numVars = int(dataBytes[startPos:endPos].decode())
            
            #Extract the number of points
            startPos = endPos + len('No. Points: ')
            endPos = dataBytes.find(b'Variables:', startPos)
            numPoints = int(dataBytes[startPos:endPos].decode())
            
            #Extract variable names
            tmpPos = dataBytes.find(b'Variables:')
            startPos = dataBytes.find(b'Variables:', tmpPos + len('Variables')) + len('Variables:')
            endPos = dataBytes.find(b'Binary:\n')
            varData = (dataBytes[startPos:endPos]).decode("utf-8").replace('\t', ' ').strip()
            varLines = varData.split('\n')
            # print(varData)
            # print(varLines)
            varList = [line.strip().split()[1] for line in varLines]
            # pdb.set_trace()
            if (simulator == "ngspice"):
                # Create arrays to store the points
                for j in range(numVars):
                    plotDat[varList[j]] = np.zeros(numPoints)
                # Populate the arrays
                bytePtr = endPos + len('Binary:\n')
                for j in range(numPoints):
                    for k in plotDat.keys():
                        plotDat[k][j] = struct.unpack('d', dataBytes[bytePtr:bytePtr+8])[0]
                        bytePtr += 8
                        
            elif (simulator == "spectre"):
                headerEnds = [m.start() for m in re.finditer('Binary:\n', dataStr)]
                for j in range(numVars):
                    plotDat[varList[j]] = np.zeros(numPoints*len(headerEnds))
                sweepIter = 0
                for endPos in headerEnds:
                    bytePtr = endPos + len('Binary:\n')
                    for j in range(numPoints):
                        for k in plotDat.keys():
                            plotDat[k][j + sweepIter*numPoints] = struct.unpack('d', dataBytes[bytePtr:bytePtr+8][::-1])[0]
                            bytePtr += 8
                    sweepIter += 1
            
    # Assuming that the data file always contains parametric data for now
    #if (isParametric):
    #    return split(plotDat)
    #else:
    #    return plotDat
    rawFile.close()
    #return plotDat
    return split(plotDat)

def getVars(plotDat):
    """ Returns the list of variable names and their units, i.e. the indices
    for the ordered dictionaries that read generates.
    """
    return plotDat.keys()

def plot(plotDat, xVar, yVar, color='b'):
    """ Plots the specified variables stored in plotDat. If the simulation is
    parametric, each of the parametric simulations are plotted.

    Arguments:
    plotDat - The data generated by the read function
    xVar - The variable on the horizontal axis
    yVar - The variable on the vertical axis
    color - The color of the line plot (defaul blue).
    """
    import matplotlib.pyplot as plt
    for i in range(np.shape(plotDat[xVar])[0]):
        lines = plt.plot(plotDat[xVar][i], plotDat[yVar][i], c=color)
        color = lines[0].get_color()
    plt.show()

