'''
Created on Dec 13, 2012

Created By: Michael Palmer

SchellingSegregationModel

A Python implementation of a Schelling Segregation Model for exploring 
self-segregation of groups on the basis of race, religion, language, etc. 

Based on the segregation model presented in:
MicroMotives and MacroBehavior
Thomas C. Schelling
W.W. Norton, New York, 2006

Design Decisions:

1. As per the model described in MicroMotives and MacroBehavior an agent's
   preferences do not apply when the agent is surrounded by empty lots.
   
2. Unlike MicroMotives and MacroBehavior an agent is allowed to trade places 
   with another unhappy agent as well as move to an empty lot.
   
3. The run function will exit early if a step is reached where no agent 
   is unhappy.
   
Usage Steps:
1. Build a neighborhood
2. Run the experiment for a selected number of cycles

Example (using factory functions to build the neighborhood):

The example builds a neighborhood of randomly assign X's and O's who
have minimum preferences for what their neighborhood looks like.
The model is asked to run for 30 ticks. At the start of the first
tick the unhappiness was at 28% with 51% similar neighborhoods. 
At the start of turn 22 the unhappiness was 0 with 86% similar 
neighborhoods.

>>> n = likesSameNeighborhood(50)
>>> r = run(n,30)
>>> r[0]
(0, (0.2839451570101725, 0.5140061162079511))
>>> r[len(r) -1]
(22, (0.0, 0.8582235236700829))


'''

from random import sample
from random import uniform
from random import seed
from random import triangular
from math   import floor
import unittest
import csv
import timeit


EMPTYLOT = 'Empty'

X_COORDINATE = 0
Y_COORDINATE = 1

"""
SchellingAgent

Ancestor Class for all the Schelling Agents in the module.
"""
class SchellingAgent(object):
    def __init__(self,neighborhood,mytype,percentpreference = 0.0,coordinates=None,view_radius = 1):
        
        self.neighborhood   = neighborhood
        self.mytype         = mytype
        self.preference     = percentpreference
        self.neighbor_radius= view_radius
        self.setCoordinates(coordinates)
        

    def setCoordinates(self,coordinates):        
        if coordinates != None:
            self.x = coordinates[X_COORDINATE]
            self.y = coordinates[Y_COORDINATE]
            self.neighborhood.putAgent(self)
        else:
            self.x              = 0
            self.y              = 0     
            
    def isMyType(self,neighbor):
        
        if neighbor.mytype == self.mytype: return True
        return False
               
    def getNeighbors(self):
        adjoining_lots = self.neighborhood.getNeighborhood(self.x,self.y,self.neighbor_radius)
        real_neighbors = [lot for row in adjoining_lots for lot in row  if lot.mytype!=EMPTYLOT and lot!=self]
        return real_neighbors
    
    def getSameNeighbors(self,neighbors = None):
        if neighbors ==None: neighbors = self.getNeighbors()
        same_neighbors = [neighbor  for neighbor in neighbors if self.isMyType(neighbor)==True]
        return same_neighbors

    def countNeighbors(self):
        neighbors     = self.getNeighbors()
        sameNeighbors = self.getSameNeighbors(neighbors)
        return (len(sameNeighbors),len(neighbors))
    
    def percentSame(self,neighbors = None):
        if neighbors == None: neighbors = self.getNeighbors()
        # getNeighbors returns nothing when the agent is surrounded by empty lots
        if len(neighbors)==0: return 0.0
        numbersame = len(self.getSameNeighbors(neighbors))
        percent = numbersame / (len(neighbors) * 1.0)
        return percent        
    
    def isUnhappy(self):
        return False
    
    def __repr__(self):
        return repr(self.mytype)

class EmptyLot(SchellingAgent):
    def __init__(self,neighborhood,coordinates):
        super(EmptyLot,self).__init__(neighborhood,EMPTYLOT)
        self.x = coordinates[X_COORDINATE]
        self.y = coordinates[Y_COORDINATE]
    def info(self):
        return 'Empty lot at %s,%s.'%(self.x,self.y)
        
class LikesSameAgent(SchellingAgent):    
    def isUnhappy(self):
        neighbors = self.getNeighbors()
        if neighbors==[]: return False
        likeme = self.percentSame(neighbors)
        if likeme < self.preference:
            return True
        return False
    def info(self):
        return 'Likes Same Agent Type %s Preference %s at %s,%s.'%(self.mytype,self.preference,self.x,self.y)

class LikesOthersAgent(SchellingAgent):     
    def isUnhappy(self):
        neighbors = self.getNeighbors()
        if neighbors==[]: return False       
        others_percent = 1.0 - self.percentSame(neighbors)
        if others_percent < self.preference:
            return True
        return False   
    def info(self):
        return 'Likes Other Agent Type %s Preference %s at %s,%s.'%(self.mytype,self.preference,self.x,self.y) 
    
class ContinuousSchellingAgent(SchellingAgent):
    def __init__(self,neighborhood,mytype,minrange,maxrange,percentpreference = 0.0,coordinates=None,view_radius = 1):
        super(ContinuousSchellingAgent,self).__init__(neighborhood,mytype,percentpreference,coordinates,view_radius)
        self.minrange = minrange
        self.maxrange = maxrange
    def isMyType(self,neighbor): 
        if neighbor.mytype >= self.minrange and neighbor.mytype <= self.maxrange: return True
        return False
    
class ContinuousLikesSameAgent(ContinuousSchellingAgent):
    def isUnhappy(self):
        neighbors = self.getNeighbors()
        if neighbors==[]: return False
        likeme = self.percentSame(neighbors)
        if likeme < self.preference:
            return True
        return False    
    
class ContinuousLikesOtherAgent(ContinuousSchellingAgent):
    def isUnhappy(self):
        neighbors = self.getNeighbors()
        if neighbors==[]: return False       
        others_percent = 1.0 - self.percentSame(neighbors)
        if others_percent < self.preference:
            return True
        return False     
        
class Neighborhood(object):
    def __init__(self,dimension):
        self.dimension = dimension 
        self.lots      = [[EmptyLot(self,(x,y)) for y in range(self.dimension)] for x in range(self.dimension)]
        self.agents    = []
        self.unhappyagents = []
        self.runOnce   = False
    def wrap(self,x):
        if x<0: return(self.dimension+x)
        if x>self.dimension-1: return(x-self.dimension)
        return x
    def getNeighborhood(self,x,y,radius):
        neighbors=[]
        x_range = [self.wrap(i) for i in range(x - radius, x + radius +1)]
        y_range = [self.wrap(i) for i in range(y - radius, y + radius +1)]
        
        for x in x_range:
            row = []
            for y in y_range:
                row.append(self.lots[x][y])
            neighbors.append(row)

        return neighbors
    def putAgent(self,agent):
        self.agents.append(agent)
        self.lots[agent.x][agent.y] = agent
    def getUnhappyAgents(self):
        self.unhappyagents = [agent for agent in self.agents if agent.isUnhappy() == True]
        return self.unhappyagents
    def percentUnhappy(self):
        if self.runOnce:
           totalUnhappy = len(self.unhappyagents)
        else:
           totalUnhappy = len(self.getUnhappyAgents())
        return totalUnhappy / (len(self.agents) *1.0)
    def percentSimilar(self):
        neighborData = [ x.countNeighbors() for x in self.agents]
        similar_neighbors = sum([x[0] for x in neighborData]) 
        total_neighbors   = sum([x[1] for x in neighborData])
        return similar_neighbors / (total_neighbors *1.0)        
    def getStats(self):
        percent_unhappy   = self.percentUnhappy()
        percent_similar   = self.percentSimilar()
        return (percent_unhappy,percent_similar)
    def move(self):
        unhappy_agents = self.getUnhappyAgents()
        empty_lots     = [lot for row in self.lots for lot in row if lot.mytype == EMPTYLOT]
        places_to_move = []
        places_to_move.extend(unhappy_agents)
        places_to_move.extend(empty_lots)
        while (len(places_to_move)>=2):
            movers = sample(places_to_move,2)
            places_to_move.remove(movers[0])
            places_to_move.remove(movers[1])
            self.swap(movers[0],movers[1])
    def swap(self,agent1,agent2):
        x1,y1 = agent1.x,agent1.y
        agent1.x = agent2.x
        agent1.y = agent2.y
        agent2.x = x1
        agent2.y = y1
        self.lots[agent1.x][agent1.y] = agent1
        self.lots[agent2.x][agent2.y] = agent2
    def writeToCSV(self,filename = 'testSchelling.csv'):
        outputFile = open(filename,'wb')
        csvWriter = csv.writer(outputFile)
        csvWriter.writerows(self.lots)
        outputFile.close()
    def run(self,ticks=30):
        history = []
        for tick in range(ticks):
            stats = self.getStats()
            history.append((tick,stats))
            self.move()
            if stats[0] ==0.0: break
        return history
    

def ageNeighborhood(size,populatedpercent=.95,preference=0.3,averageage=45,minage=20,maxage=90):
    neighborhood = Neighborhood(size)
    for x in range(size):
        for y in range(size):
            pick = uniform(0,1)
            if pick < populatedpercent:
                age = floor(triangular(minage,maxage,averageage))
                agent= ContinuousLikesSameAgent(neighborhood,age,age-5,age+5,preference,(x,y))
    return neighborhood
                                              
def likesSameNeighborhood(size,preference=0.4,typeA='X',typeB='O',typeASplit=0.5,typeBSplit=0.4):
    if typeASplit + typeBSplit > 1.0: return 'Split values must add to 1.0.'     
    neighborhood = Neighborhood(size)
    for x in range(size):
        for y in range(size):
            pick = uniform(0,1)
            if pick <= typeASplit:
                LikesSameAgent(neighborhood,typeA,preference,(x,y))
            elif pick <= typeASplit + typeBSplit:
                LikesSameAgent(neighborhood,typeB,preference,(x,y))
    return neighborhood

def likesOthersNeighborhood(size,preference=0.4,typeA='X',typeB='O',typeASplit=0.5,typeBSplit=0.4):
    if typeASplit + typeBSplit > 1.0: return 'Split values must add to 1.0.'     
    neighborhood = Neighborhood(size)
    for x in range(size):
        for y in range(size):
            pick = uniform(0,1)
            if pick <= typeASplit:
                LikesOthersAgent(neighborhood,typeA,preference,(x,y))
            elif pick <= typeASplit + typeBSplit:
                LikesOthersAgent(neighborhood,typeB,preference,(x,y))
    return neighborhood

def moveimprove():
    n = likesSameNeighborhood(100)
    a = n.agents[0]
    print timeit.timeit(stmt = n.move,number = 1)
        
class testagents(unittest.TestCase):
    def getsuite(self):
        suite = unittest.TestSuite()  
        suite.addTest(testagents('test_buildNeighborhood'))
        suite.addTest(testagents('test_buildLikeSame'))   
        suite.addTest(testagents('test_buildLikeOthers'))       
        suite.addTest(testagents('test_percentAllSame'))    
        suite.addTest(testagents('test_percentSomeSame'))
        suite.addTest(testagents('test_smallMove'))
        suite.addTest(testagents('test_smallMoveLikesOthers'))
        suite.addTest(testagents('test_buildContinuousLikeSame'))
        suite.addTest(testagents('test_buildContinuousLikeOthers'))
        suite.addTest(testagents('test_continuouslikesameisunhappy'))
        suite.addTest(testagents('test_continuouslikeotherisunhappy'))
        suite.addTest(testagents('test_continuoussmallmove'))

        
        return suite
      
    def runTest(self):
        runner = unittest.TextTestRunner(verbosity=2)
        suite = self.getsuite()
        result = runner.run(suite)    
        return result
    
    def test_buildNeighborhood(self):       
        n = Neighborhood(50)    
        self.assertEqual(n.dimension,50)
        self.assertEquals(len(n.lots),50)
        for x in range(50):
            self.assertEquals(len(n.lots[x]),50)
        self.assertEqual(n.agents,[]) 
        origin_neighbors = n.getNeighborhood(n.lots[0][0].x,n.lots[0][0].y,1)
        self.assertEqual(len(origin_neighbors[0]),3)
        self.assertEqual(len(origin_neighbors[1]),3)
        self.assertEqual(len(origin_neighbors[2]),3)
        self.assertEqual(origin_neighbors[0][0].x,49)
        self.assertEqual(origin_neighbors[0][0].y,49)
        
    def test_buildLikeSame(self):
        n=Neighborhood(10)
        s=LikesSameAgent(n,'X',0.3)
        self.assertEqual(s.mytype,'X')
        self.assertEqual(s.preference,0.3)
        self.assertEqual(s.isUnhappy(),False)
        
    def test_buildLikeOthers(self):
        n=Neighborhood(10)
        s=LikesOthersAgent(n,'X',0.3)
        self.assertEqual(s.mytype,'X')
        self.assertEqual(s.preference,0.3)
        self.assertEqual(s.isUnhappy(),False)   
        
    def test_percentAllSame(self):
        n=Neighborhood(10)
        s=LikesSameAgent(n,'X',0.1,(0,1)) 
        s1=LikesSameAgent(n,'X',0.1,(1,1))
        s2=LikesSameAgent(n,'X',0.1,(2,1)) 
        self.assertEqual(s.percentSame(),1.0)

    def test_percentSomeSame(self):
        n=Neighborhood(10)
        s=LikesSameAgent(n,'X',0.1,(0,1)) 
        s1=LikesSameAgent(n,'X',0.1,(1,1))
        s2=LikesSameAgent(n,'X',0.1,(2,1)) 
        s3=LikesSameAgent(n,'O',0.4,(0,2))
        self.assertEqual(s.percentSame(),0.5)     
  
    def test_isUnhappy(self):
        seed(1)
        n=Neighborhood(10)
        s=LikesSameAgent(n,'X',0.1,(0,1)) 
        s1=LikesSameAgent(n,'X',0.1,(1,1))
        s2=LikesSameAgent(n,'X',0.1,(2,1)) 
        s3=LikesSameAgent(n,'O',0.4,(0,2))  
        self.assertEquals(s3.isUnhappy(),True)
        
    def test_smallMove(self):
        seed(1)
        n=Neighborhood(10)
        s=LikesSameAgent(n,'X',0.1,(0,1)) 
        s1=LikesSameAgent(n,'X',0.1,(1,1))
        s2=LikesSameAgent(n,'X',0.1,(2,1)) 
        s3=LikesSameAgent(n,'O',0.4,(0,2))
        before =  n.getStats()
        self.assertEqual(before,(0.25,0.5))
        self.assertEqual(len(n.agents),4)
        n.move() 
        after  =  n.getStats()
        self.assertEqual(after,(0.0,1.0))
        self.assertEqual(len(n.agents),4)

    def test_smallMoveLikesOthers(self):
        seed(1)
        n=Neighborhood(10)
        s=LikesOthersAgent(n,'X',0.1,(0,1)) 
        s1=LikesSameAgent(n,'X',0.1,(1,1))
        s2=LikesSameAgent(n,'X',0.1,(2,1)) 
        s3=LikesOthersAgent(n,'O',0.1,(2,2))
        before =  n.getStats()
        self.assertEqual(before,(0.25,0.5))
        self.assertEqual(len(n.agents),4)
        n.move() 
        after  =  n.getStats()
        self.assertEqual(len(n.agents),4)
        self.assertEqual(after,(0.0,1/3.0))
  
        
    def test_buildContinuousLikeSame(self):
        n=Neighborhood(10)
        s=ContinuousLikesSameAgent(n,45,40,50,0.3,(0,1))
        self.assertEqual(s.mytype,45)
        self.assertEqual(s.minrange,40)
        self.assertEqual(s.maxrange,50)
        self.assertEqual(s.preference,0.3)
        self.assertEqual(s.isUnhappy(),False)
        self.assertEquals(s.x,0)
        self.assertEquals(s.y,1)
        
    def test_buildContinuousLikeOthers(self):
        n=Neighborhood(10)
        s=ContinuousLikesOtherAgent(n,45,40,50,0.3)
        self.assertEqual(s.mytype,45)
        self.assertEqual(s.minrange,40)
        self.assertEqual(s.maxrange,50)        
        self.assertEqual(s.preference,0.3)
        self.assertEqual(s.isUnhappy(),False)
        
    def test_continuouslikesameisunhappy(self):
        seed(1)
        n=Neighborhood(10)
        s=ContinuousLikesSameAgent(n,45,40,50,0.1,(0,1)) 
        s1=ContinuousLikesSameAgent(n,41,31,51,0.1,(1,1)) 
        s3=ContinuousLikesSameAgent(n,22,20,30,0.4,(0,2)) 
        self.assertEquals(s3.isUnhappy(),True)   
        
    def test_continuouslikeotherisunhappy(self):
        seed(1)
        n=Neighborhood(10)
        s=ContinuousLikesSameAgent(n,45,40,50,0.1,(0,1)) 
        s1=ContinuousLikesSameAgent(n,41,31,51,0.1,(1,1)) 
        s3=ContinuousLikesOtherAgent(n,39,30,46,0.4,(0,2)) 
        self.assertEquals(s3.isUnhappy(),True)
        
    def test_continuoussmallmove(self):
        seed(1)
        n=Neighborhood(10)
        s=ContinuousLikesSameAgent(n,45,40,50,0.1,(0,1)) 
        s1=ContinuousLikesSameAgent(n,41,31,51,0.1,(1,1))
        s2=ContinuousLikesSameAgent(n,47,37,49,0.1,(2,1)) 
        s3=ContinuousLikesSameAgent(n,22,20,30,0.4,(0,2))        
        before =  n.getStats()
        self.assertEqual(before,(0.25,0.5))
        self.assertEqual(len(n.agents),4)
        n.move() 
        after  =  n.getStats()
        self.assertEqual(after,(0.0,1.0))
        self.assertEqual(len(n.agents),4)        
       
          
