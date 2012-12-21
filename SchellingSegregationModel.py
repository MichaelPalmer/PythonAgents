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

Ancestor Class for all the Schelling Agents in the module. ScheliingAgent is meant to be
an ancestor class, it should not be instantiated directly.
"""
class SchellingAgent(object):
    """
    method: __init__

    Initialize the attributes of the Schelling Agent
          
    Arguments:
    neighborhood          An initialized neighborhood where the agent will 'live'
    mytype                A value representing an attribute of the agent - could be race,age,religion,language,etc.
    percentpreference     The percentage of neighbors that the agent would like to see around them with the 'right' traits
    coordinates           The x and y coordinates to place the agent on the grid
    viewRadius           The radius of the neighborhood the agent uses to determine their neighbors.
                          A radius of one implies 8 neighbors
    """
    def __init__(self,neighborhood,mytype,percentpreference = 0.0,coordinates=None,viewRadius = 1):
        
        self.neighborhood   = neighborhood
        self.mytype         = mytype
        self.preference     = percentpreference
        self.neighborRadius= viewRadius
        self.setCoordinates(coordinates)
    """
    method: setCoordinates

    logic to deal with setting coordinates of the agent - absense of coordinates implies
    that the coordinates will be set with external code

    Arguments:
    coordinates              coordinates to use to position the agent
    """
    def setCoordinates(self,coordinates):        
        if coordinates != None:
            self.x = coordinates[X_COORDINATE]
            self.y = coordinates[Y_COORDINATE]
            self.neighborhood.putAgent(self)
        else:
            self.x              = 0
            self.y              = 0     

    """
    method: isMyType

    The logic that determines if a neighbor is the 'same' as mee.
    The code here will work for many discrete variable cases (race,sex,religion, etc.)
    Any special case logic will need to override this code.

    Arguments:
    neighbor           the neighboring agent that is being evaluated
    Return:
    Boolean            True = neighbor is like me  False = neighbor is not like me
    """
    def isMyType(self,neighbor):        
        if neighbor.mytype == self.mytype: return True
        return False
    """
    method: getNeighbors

    Get my neighborhood from the neighborhood object and subtract empty lots
    and the current agent

    Return:
    List of Neighbors
    """
    def getNeighbors(self):
        adjoining_lots = self.neighborhood.getNeighborhood(self.x,self.y,self.neighborRadius)
        real_neighbors = [lot for row in adjoining_lots for lot in row  if lot.mytype!=EMPTYLOT and lot!=self]
        return real_neighbors

    """
    method: getSameNeighbors

    Look at my neighbors and return the ones that are 'like' me.

    Arguments:
    neighbors   - Optional list of neighbors, will be retrieved if missing
    Return:
    List of neighbors that are like me
    """
    def getSameNeighbors(self,neighbors = None):
        if neighbors ==None: neighbors = self.getNeighbors()
        same_neighbors = [neighbor  for neighbor in neighbors if self.isMyType(neighbor)==True]
        return same_neighbors
    """
    method: countNeighbors

    A convenience method to return the total number of neighbors and the neighbors that are the same

    Return:
    Tuple  Position 0 = Count of Same Neighbors
           Position 1 = Count of All Neighbors
    """
    def countNeighbors(self):
        neighbors     = self.getNeighbors()
        sameNeighbors = self.getSameNeighbors(neighbors)
        return (len(sameNeighbors),len(neighbors))
    """
    method: percentSame

    Calculate the percentage of the neighbors who are like me

    Return:
    float between 0 and 1.0 Percentage of like neighbors
    """  
    def percentSame(self,neighbors = None):
        if neighbors == None:
            neighbors = self.getNeighbors()
        #getNeighbors returns nothing when the agent is surrounded by empty lots
        if len(neighbors)==0:
            return 0.0
        numbersame = len(self.getSameNeighbors(neighbors))
        percent = numbersame / (len(neighbors) * 1.0)
        return percent        

    """
    method: isUnhappy

    Evaluate the neighbors and figure out if the agent is unhappy and wants to move.

    ***Should be overridden by an implementing class***

    Return:
    Boolean   True = Unhappy wants to move  False = is OK where they are
    """
    def isUnhappy(self):
        return False
    """
    method: __repr__

    Return a fair shorthand version of the agent.
    Uses repr() for cases where the primary attribute is a number or other non-string.

    Return:
    string representing the agent
    """
    def __repr__(self):
        return repr(self.mytype)

"""
EmptyLot

An empty lot is treated as a pseudo-agent.
The idea is to have the empty lot be use a null object pattern.

"""
class EmptyLot(SchellingAgent):
    """
    method: __init__

    Overrides coordinate setup, already exists as part of the landscape
    
    """
    def __init__(self,myneighborhood,coords):
        super(EmptyLot,self).__init__(neighborhood=myneighborhood,mytype=EMPTYLOT)
        self.x = coords[X_COORDINATE]
        self.y = coords[Y_COORDINATE]
    """
    method: info

    provides a nice source of debugging info about the agent

    Return:
    String   A string with important information about the current state of the agent.
    """
    def info(self):
        return 'Empty lot at %s,%s.'%(self.x,self.y)

"""
LikesSameAgent

A discrete Schelling Agent that likes to have a percentage of the neighbors be of the same type as the agent.

"""     
class LikesSameAgent(SchellingAgent):   
    """
    method: isUnhappy

    Look at the neighbors and return True if too few neighbors are of the same type

    Return:
    Boolean  True - agent is unhappy with the neighborhood  False - agent is content    
    """
    def isUnhappy(self):
        neighbors = self.getNeighbors()
        if neighbors==[]: return False
        likeme = self.percentSame(neighbors)
        if likeme < self.preference:
            return True
        return False
    """
    method: info

    provides a nice source of debugging info about the agent

    Return:
    String   A string with important information about the current state of the agent.
    """        
    def info(self):
        return 'Likes Same Agent Type %s Preference %s at %s,%s.'%(self.mytype,self.preference,self.x,self.y)

"""
LikesOthersAgent

A discrete Schelling Agent that likes to have a percentage of the neighbors be of a different type from the agent.

"""  
class LikesOthersAgent(SchellingAgent):
    """
    method: isUnhappy

    Look at the neighbors and return True if too many neighbors are of the same type

    Return:
    Boolean  True - agent is unhappy with the neighborhood  False - agent is content    
    """
    def isUnhappy(self):
        neighbors = self.getNeighbors()
        if neighbors==[]: return False       
        others_percent = 1.0 - self.percentSame(neighbors)
        if others_percent < self.preference:
            return True
        return False
    """
    method: info

    provides a nice source of debugging info about the agent

    Return:
    String   A string with important information about the current state of the agent.
    """    
    def info(self):
        return 'Likes Other Agent Type %s Preference %s at %s,%s.'%(self.mytype,self.preference,self.x,self.y) 
    
class ContinuousSchellingAgent(SchellingAgent):
    def __init__(self,neighborhood,mytype,minrange,maxrange,percentPreference = 0.0,coordinates=None,viewRadius = 1):
        super(ContinuousSchellingAgent,self).__init__(neighborhood,mytype,percentPreference,coordinates,viewRadius)
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
       
          
