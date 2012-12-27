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

Important Classes:

SchellingAgent           : The ancestor agent class for all Schelling agents. 
ContinuousSchellingAgent : The ancestor agent class for Schelling agents with continuous variables.
                           Inherits from Schelling Agent.
Neighborhood             : The class containing the methods and attributes for the agent neighborhood.
EmptyLot                 : A null object agent that represents an empty lot in the neighborhood.

Example:

The demo() function shows a complete run of a discrete Schelling Model where all agents have a similar agent preference.
The model moves from a time tick of 0 with .26 unhappiness and .52 neighborhood similarity to a time tick of 10 with
0 unhappiness and a neighborhood similarity of 0.84.

>>> demo()
[(0, (0.2861111111111111, 0.5220417633410673)), (1, (0.175, 0.6283731688511951)), (2, (0.08055555555555556, 0.7364341085271318)), (3, (0.05, 0.7770897832817337)),
(4, (0.03611111111111111, 0.8078703703703703)), (5, (0.013888888888888888, 0.8294573643410853)), (6, (0.011111111111111112, 0.8303777949113339)),
(7, (0.005555555555555556, 0.8386100386100386)), (8, (0.002777777777777778, 0.8410852713178295)), (9, (0.002777777777777778, 0.8383604021655066)),
(10, (0.0, 0.8428792569659442))]

'''

from random import sample
from random import uniform
from random import seed
from random import triangular
from random import normalvariate
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
"""
ContinuousSchellingAgent

An ancestor class for Schelling agents working on continuous variables like age and income.
This class is meant to be subclassed for use.

"""
class ContinuousSchellingAgent(SchellingAgent):
    """
    method: __init__

    Arguments:
    See <SchellinAgent> for most of theese
    minrange     a new argument for the ContinuousSchellingAgent that defines the bottom of a similar agent range.
    maxrange     a new argument for the ContinuousSchellingAgent that defines the top of a similar agent range.
    """
    def __init__(self,neighborhood,mytype,minrange,maxrange,percentPreference = 0.0,coordinates=None,viewRadius = 1):
        super(ContinuousSchellingAgent,self).__init__(neighborhood,mytype,percentPreference,coordinates,viewRadius)
        self.minrange = minrange
        self.maxrange = maxrange
    """
    method: isMyType

    Defines a similarity argument for continuous variables based on a range.

    Arguments:
    neighbor      a neighbor agent to be compared with the current agent

    Returns:
    Boolean    True -- Agent is like me     False -- Agent is not like me
    """
    def isMyType(self,neighbor): 
        if neighbor.mytype >= self.minrange and neighbor.mytype <= self.maxrange: return True
        return False
"""
ContinuousLikesSameAgent

Defines a continuous Schelling agent that prefers agents like itself.

"""
class ContinuousLikesSameAgent(ContinuousSchellingAgent):
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
        return 'Continuous Likes Same Agent  Type %s Attribute %s Minrange %s, Maxrange %s at %s,%s.'%(self.mytype,self.preference,self.minrange,self.maxrange,self.x,self.y)    

"""
ContinuousLikesOtherAgent

Defines a continuous Schelling agent that prefers agents not like itself.

"""    
class ContinuousLikesOtherAgent(ContinuousSchellingAgent):
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
        return 'Continuous Likes Other Agents  Type %s Attribute %s Minrange %s, Maxrange %s at %s,%s.'%(self.mytype,self.preference,self.minrange,self.maxrange,self.x,self.y)        

"""
Neighborhood

Defines the methods and data for the agent neighborhood. This is always a torus - the grid wraps East to West and North to South.
"""
class Neighborhood(object):
    """
    method: __init__

    Define a torus neighborhood of dimension length and width
    Arguments:
    dimension           the size of one 'side' of the neighborhood
    Object Attributes:
    self.dimension      the length and width of the neighborhood
    self.lots           the grid that stores the neighborhood
    self.agents         the list of agents in the neighborhood
    self.unhappyagents  cache for the list of unhappy agents
    self.runOnce        indicator if moves have been performed at least once
    """
    def __init__(self,dimension):
        self.dimension = dimension 
        self.lots      = [[EmptyLot(self,(x,y)) for y in range(self.dimension)] for x in range(self.dimension)]
        self.agents    = []
        self.unhappyagents = []
        self.runOnce   = False
    """
    method: wrap

    Adjust the incoming coordinate to account for being on a torus

    Argument:
    x      a coordginate to wrap around the torus
    Return:
    int   adjusted coordinate value    
    """
    def wrap(self,x):
        if x<0: return(self.dimension+x)
        if x>self.dimension-1: return(x-self.dimension)
        return x
    """
    method: getNeighborhood

    Get the visible neighborhood at a point in the grid

    Arguments:
    x       x coordinate on the neighborhood grid
    y       y coordinate on the neighborhood grid
    radius  number of lots arround the coordiante to pull for the neighborhood

    Returns:
    List    a list of lots that make up a neighborhood
    """
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
    """
    method: putAgent

    Add an agent to the neighborhood grid

    Argument:
    agent      agent to add to the grid
    """
    def putAgent(self,agent):
        self.agents.append(agent)
        self.lots[agent.x][agent.y] = agent
    """
    method: getUnhappyAgents

    Return a list of agents in the neighborhood that say they are unhappy

    Return:
    List   a list of unhappy agents
    """
    def getUnhappyAgents(self):
        self.unhappyagents = [agent for agent in self.agents if agent.isUnhappy() == True]
        return self.unhappyagents
    """
    method: percentUnhappy

    Returns a measurement of total neighborhood unhappiness. Uses a cached list of unhappy agents if available.

    Return:
    float   a representation of neighborhood unhappiness 0.0 - 1.0
    """
    def percentUnhappy(self):
        if self.runOnce:
           totalUnhappy = len(self.unhappyagents)
        else:
           totalUnhappy = len(self.getUnhappyAgents())
        return totalUnhappy / (len(self.agents) *1.0)
    """
    method: percentSimilar

    A representation of the similarity of the neighborhoods of the agents

    Return:
    float  a representation of agent neighborhood similarity 0.0-1.0
    """
    def percentSimilar(self):
        neighborData = [ agent.countNeighbors() for agent in self.agents]
        similar_neighbors = sum([x[0] for x in neighborData]) 
        total_neighbors   = sum([x[1] for x in neighborData])
        return similar_neighbors / (total_neighbors *1.0)
    """
    method: getStats

    A convenience method to get the stats for the neighborhood

    Return:
    tuple  0 = percent of unahppy agents   1 = agent neighborhood similarity
    """
    def getStats(self):
        #rounded to 4 places for easy readability
        #2 places is too few to see some results
        percent_unhappy   = round(self.percentUnhappy(),4)
        percent_similar   = round(self.percentSimilar(),4)
        return (percent_unhappy,percent_similar)
    """
    method: move

    Get the unhappy agents and empty lots and start moving agents around.   
    """
    def move(self):
        #build the list of moveable parts
        unhappy_agents = self.getUnhappyAgents()
        empty_lots     = [lot for row in self.lots for lot in row if lot.mytype == EMPTYLOT]
        places_to_move = []
        places_to_move.extend(unhappy_agents)
        places_to_move.extend(empty_lots)
        #start swapping two by two at random
        while (len(places_to_move)>=2):
            movers = sample(places_to_move,2)
            places_to_move.remove(movers[0])
            places_to_move.remove(movers[1])
            self.swap(movers[0],movers[1])
    """
    method: swap

    Swap the positions of two agents in the grid.

    Arguments:
    agent1      an agent to move
    agent2      another agent to move
    """
    def swap(self,agent1,agent2):
        x1,y1 = agent1.x,agent1.y
        agent1.x = agent2.x
        agent1.y = agent2.y
        agent2.x = x1
        agent2.y = y1
        self.lots[agent1.x][agent1.y] = agent1
        self.lots[agent2.x][agent2.y] = agent2
    """
    method: writeToCSV

    A helper method to save/visualize the state of the grid

    Argument:
    filename     name for the output csv file   
    """
    def writeToCSV(self,filename = 'testSchelling.csv'):
        outputFile = open(filename,'wb')
        csvWriter = csv.writer(outputFile)
        csvWriter.writerows(self.lots)
        outputFile.close()



"""
 Function: run

 A heartbeat function to run the Schelling models.
 Accumulates stat history and will stop early if
 unhappiness is eliminated.

Arguments:
neighborhood    the instantiated Schelling neighborhood
ticks           how many clock cycles to run the model  
"""
def run(neighborhood,ticks=30):
    history = []
    for tick in range(ticks):
        stats = neighborhood.getStats()
        history.append((tick,stats))
        neighborhood.move()
        if stats[0] ==0.0: break
    return history
    
"""
   Function: likesSameAgeNeighborhood

   A helper function to build a continous Schelling model based on same age segregation.

   Arguments:
   size               dimension of the Schelling neighborhood
   preference         percentage of neighbors that need to be like   
   populatedpercent   what percentage of the lots will contain agents as opposed to empty lots
   averageage         median age for the neighborhood
   minage             minimum age for the neighborhood
   maxage             maximum age for the neighborhood

   Return:
   Neighborhood       An instantiated Schelling Neighborhood
"""
def likesSameAgeNeighborhood(size,preference=0.3,populatedpercent=.95,averageage=45,minage=20,maxage=90):
    neighborhood = Neighborhood(size)
    for x in range(size):
        for y in range(size):
            #decide if the lot will be populated
            pick = uniform(0,1)
            if pick < populatedpercent:
                #produce a random age between minage and maxage
                age = floor(triangular(minage,maxage,averageage))
                age = int(age)
                agent= ContinuousLikesSameAgent(neighborhood,age,age-5,age+5,preference,(x,y))
    return neighborhood


"""
   Function: likesOtherAgeNeighborhood

   A helper function to build a continous Schelling model based on age diversity segregation.

   Arguments:
   size               dimension of the Schelling neighborhood
   preference         percentage of neighbors that need to be different   
   populatedpercent   what percentage of the lots will contain agents as opposed to empty lots
   averageage         median age for the neighborhood
   minage             minimum age for the neighborhood
   maxage             maximum age for the neighborhood

   Return:
   Neighborhood       An instantiated Schelling Neighborhood
"""
def likesOtherAgeNeighborhood(size,preference=0.4,populatedpercent=.95,averageage=55,minage=20,maxage=95):
    neighborhood = Neighborhood(size)
    for x in range(size):
        for y in range(size):
            #decide if the lot will be populated
            pick = uniform(0,1)
            if pick < populatedpercent:
                #produce a random age between minage and maxage
                age = normalvariate(averageage,10)
                if age < minage: age = minage
                if age > maxage: age = maxage
                age = int(age)
                agent= ContinuousLikesOtherAgent(neighborhood,age,age-7,age+7,preference,(x,y))
    return neighborhood

"""
  Function: likesSameNeighborhood

  A helper function to build a discrete Schelling Model based on attraction of similar agents

  Arguments:
  size                  dimension of the Schelling neighborhood
  preference            the preference for similar agents 
  typeA                 the type of typeA agents
  typeB                 the type of typeB agents
  typeASplit            the percentage of typeA agents
  typeBSplit            the percentage of typeB agents

  Return:
  Neighborhood     An instantiated Schelling Neighborhood
"""
def likesSameNeighborhood(size,preference=0.3,typeA='X',typeB='O',typeASplit=0.5,typeBSplit=0.4):
    if typeASplit + typeBSplit > 1.0: return 'Split values must add to 1.0.'     
    neighborhood = Neighborhood(size)
    for x in range(size):
        for y in range(size):
            pick = uniform(0,1)
            #decide if the lot will be typeA
            if pick <= typeASplit:
                LikesSameAgent(neighborhood,typeA,preference,(x,y))
            #decide if the lot will be typeB (anything leftover will be an EmptyLot)
            elif pick <= typeASplit + typeBSplit:
                LikesSameAgent(neighborhood,typeB,preference,(x,y))
    return neighborhood

"""
  Function: likesOthersNeighborhood(

  A helper function to build a discrete Schelling Model based on attraction of differant agents

  Arguments:
  size                  dimension of the Schelling neighborhood
  preference            the preference for similar agents 
  typeA                 the type of typeA agents
  typeB                 the type of typeB agents
  typeASplit            the percentage of typeA agents
  typeBSplit            the percentage of typeB agents

  Return:
  Neighborhood     An instantiated Schelling Neighborhood
"""
def likesOthersNeighborhood(size,preference=0.4,typeA='X',typeB='O',typeASplit=0.5,typeBSplit=0.4):
    if typeASplit + typeBSplit > 1.0: return 'Split values must add to 1.0.'     
    neighborhood = Neighborhood(size)
    for x in range(size):
        for y in range(size):
            pick = uniform(0,1)
            #decide if the lot will be typeA
            if pick <= typeASplit:
                LikesOthersAgent(neighborhood,typeA,preference,(x,y))
            #decide if the lot will be typeB (anything leftover will be an EmptyLot)    
            elif pick <= typeASplit + typeBSplit:
                LikesOthersAgent(neighborhood,typeB,preference,(x,y))
    return neighborhood


"""
 Function: demo

 Shows a sample of how to run and use the Schelling code.
"""
def demo(neighborhoodfunction=likesSameNeighborhood):
    n = neighborhoodfunction(20)
    n.writeToCSV('before.csv')
    r = run(n)
    n.writeToCSV('after.csv')
    print r
    return r

"""
testagents

Unit tests to keep the developer honest
"""
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
        suite.addTest(testagents('test_demo'))        

        
        return suite
      
    def runTest(self):
        runner = unittest.TextTestRunner(verbosity=2)
        suite = self.getsuite()
        result = runner.run(suite)    
        return result

    def test_demo(self):

        results = demo(likesSameNeighborhood)
        self.assertTrue(len(results)>0)
        results = demo(likesOthersNeighborhood)
        self.assertTrue(len(results)>0)
        results = demo(likesOtherAgeNeighborhood)
        self.assertTrue(len(results)>0)
        results = demo(likesSameAgeNeighborhood)
        self.assertTrue(len(results)>0)
    
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
        self.assertEqual(after,(0.0,0.3333))
  
        
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
        i = s.info()
        self.assertTrue(i.startswith('Continuous'))
        
    def test_buildContinuousLikeOthers(self):
        n=Neighborhood(10)
        s=ContinuousLikesOtherAgent(n,45,40,50,0.3)
        self.assertEqual(s.mytype,45)
        self.assertEqual(s.minrange,40)
        self.assertEqual(s.maxrange,50)        
        self.assertEqual(s.preference,0.3)
        self.assertEqual(s.isUnhappy(),False)
        i = s.info()
        self.assertTrue(i.startswith('Continuous'))
        
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
       
          
