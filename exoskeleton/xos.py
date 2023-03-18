import time
import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *



import numpy as np
import tkinter as tk
import pandas as pd
import random

import klampt
import klampt.vis # For visualization
import klampt.sim.batch # For batch simulation
import klampt.sim.settle # Applies forces and lets them reach equilibrium in simulation
import klampt.sim.simulation # For simulation
import klampt.io.resource # For easy resource access
import klampt.model.subrobot # Defines the subrobot
from klampt.vis import colorize
from klampt.model import collide
import klampt.math.vectorops as kmv # This is for cross products
from klampt.model.trajectory import RobotTrajectory # Trajectory
from klampt.control.utils import TimedLooper
from klampt.plan import robotplanning, robotcspace # Configuration space
import klampt.model.create.moving_base_robot as kmcmbr
import klampt.model.create.primitives as kmcp # This is where the box is

"""
PANDAS CONFIG
"""
pd.options.display.width = 0
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

"""
MATRIX DATA
"""
NULL_MATRIX = [1, 0, 0, 0, 1, 0, 0, 0, 1]
NULL_ORIGIN = [0, 0, 0]
NULL_TRANSFORM = (NULL_MATRIX, NULL_ORIGIN)


"""
LIMB ATTACHMENT POINTS
"""

IDENTITY_MATRIX = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
X_MATRIX = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]

"""
PARAMETER DICTIONARIES
"""
TEST_MUSCLE = {"name": None,
               "link_a": None,
               "link_b": None,
               "transform_a" : 0,
               "transform_b": 0,
               "label_a": "proximal",
               "label_b": "distal",
               "force": 0,
               "pressure": 0,
               "weave_length": 1,
               "turns": 5,
               "displacement": 0,
               "geometry": None}

"""
GEOMETRIES
"""
BONE_GEOMETRY = kmcp.box(.05, .4, .05, mass=10)
FLOOR_GEOMETRY = kmcp.box(5, 5, .01, center=[0, 0, 0])

"""
CLASS DEFINITIONS
"""
class Muscle(klampt.GeometricPrimitive, klampt.sim.DefaultActuatorEmulator):
    """
    Refers to exactly one McKibben muscle, with all associated attributes.
    This may end up being an interface for both an Actuator and a simulated ActuatorEmulator, running simultaneously.
    """
    def __init__(self, wm, sim, ctrl, a, b):
        """
        Takes the world model and two link IDs, a robot controller, and a first and second relative link transform.
        """
        klampt.GeometricPrimitive.__init__(self)
        klampt.sim.DefaultActuatorEmulator.__init__(self, sim, ctrl)

        self.wm = wm
        self.sim = sim
        self.ctrl = ctrl
        self.setSegment(a,b)
        klampt.vis.add("muscle_3", self)


class MuscleGroup:
    def __init__(self):
        pass



class ExoController(klampt.control.OmniRobotInterface):
    """
    This is my specialized controller subclass for the exoskeleton. Eventually this probably wants to be its own module, and before that probably needs to be broken up
    """

    # Initialization
    def __init__(self, robotmodel,  world, config_data):
        klampt.control.OmniRobotInterface.__init__(self, robotmodel)


        self.world = world
        self.robot = robotmodel
        self.muscles = pd.DataFrame()

        # This is where we actually load in the subRobots

        # Now we load in all the muscles, accessible as a dataframe
        #self.muscles = self.muscleLoader(config_data["attachments"])



    def botAssembly(self, filepath_dict):
        """
        Given a dictionary of filepaths provided in config.txt, adds the subrobot limbs to the world and mounts them on the core.
        """

        print("Number of world IDs:", self.world.numIDs)


    def muscleLoader(self, filepath):
        """
        Given a filepath to a .csv file containing structured muscle parameters, generates a list of Muscle objects and
        assigns them to the robot model.
        """

        blank1 = None
        blank2 = None # I'm just using these to make a set so Python doesn't think it's a dict

        muscles = {blank1, blank2}

        with open(filepath) as fn:
            attachments = pd.read_csv(fn, sep=",", header=0, index_col="name")
        # Need to convert each row to a dictionary with one element and create a Muscle based on that
        for x in attachments.keys():
            attachdict = attachments[x].to_dict()
            muscles.add(Muscle(attachdict))
        # We use the dictionary elements to instantiate the muscles, we use the dataframe to store them and their parameters
        return muscles

    # Control and Kinematics
    def sensedPosition(self):
        return self.klamptModel().getDOFPosition()

    def controlRate(self):
        return 100

    def setTorque(self):
        """
        Takes a list of torque inputs and sends them to controllers. Maybe one controller should control multiple actuators.
        Kind of an architectural decision.
        ==================================
        UPDATE: Okay so I think I'm ready to implement this method. Torque is equal to the cross product of the 3-D force
        vector (provided us by the McKibben muscle parameters and perhaps a custom method) and the distance from the fulcrum at which the distance is applied
        (constant, determined with what should be a single distance query relative to the transform - this can be optimized)
        """
        force = (2, 2, 2)
        distance = (0, 1, 0)
        torque = klampt.math.vectorops.cross(force, distance)
        return torque

    def setVelocity(self):
        return

    def moveToPosition(self, list_of_q):
        self.klamptModel().setConfig(list_of_q)
        return

    def setPosition(self, list_of_q):
        self.klamptModel().setConfig(list_of_q)

    def queuedTrajectory(self):
        return self.trajectory


    def beginIdle(self):
        """
        Used for loops.
        """
        self.shutdown_flag = False

        while self.shutdown_flag == False:
            self.idle()

    # Editing functions
    def geomEdit(self,n, fn):
        """
        Opens a geometry editor for the input arguments.
        """
        klampt.io.resource.edit(n, fn, editor="visual", world=self.world)

    def configEdit(self):
        """
        Opens an editor for the configuration of the stated variables.
        """
        klampt.io.resource.edit("trajectory", self.trajectory, editor="visual", world=self.world, referenceObject=self.robot)

    def motionPlanner(self, world):
        """
        I think this takes a world and makes a plan (trajectory without time coordinates) to reach a particular config?
        """
        self.plan = robotplanning.plan_to_config(self.world, self.robot, target=[3.14,1.4, 0])

    # Function verification tests

    def diagnostics(self):
        """
        This is a diagnostic function with verbose output. May eventually be a call for more nested diagnostic subroutines.
        """
        for x in range(self.world.numRobots()):
            print(x, "Is a Robot")
            print("name: ", self.world.getName(x))

        for x in range(self.world.numIDs()):
            print(x, "is an ID")
            print(self.world.getName(x))
        print("Robot number of links: ", self.robot.numLinks())
        print("Number of IDs//: ", self.world.numIDs())

        def printLinks(self):
            for link in range(self.robot.numLinks()):
                print("Link name: ", link)

    def randomTrajectoryTest(self):
        # This populates a random trajectory for the robot to execute.
        self.trajectory = klampt.model.trajectory.RobotTrajectory(self.robot)
        print("trajectory", self.trajectory)
        x = self.robot.getConfig()
        for i in range(10):
            y = [0, 0, 0, 0, 0, .5, 0]
            newconfig = np.add(x,y)
            self.trajectory.milestones.append(newconfig)
            x = newconfig
        self.trajectory.times = list(range(len(self.trajectory.milestones)))



    def idle(self):
        self.setPosition(self.target)

class ExoSim(klampt.sim.simulation.SimpleSimulator):
    """
    This is a class for Simulations.
    """
    def __init__(self, wm, robot):
        klampt.sim.simulation.SimpleSimulator.__init__(self, wm)
        self.dt = 1

    def simLoop(self, robot):
        """
        Should simulate continuously for the specified number of cycles, maybe with looping or other end behavior
        """
        wm = self.world
        klampt.vis.run()
        for x in range(1,robot.numLinks()):
            body = self.body(robot.link(x))
            body.applyForceAtPoint((.1,.1,.1),(.1,.1,.1))
            self.simulate(.1)
            self.updateWorld()

class ExoGUI(klampt.vis.glprogram.GLRealtimeProgram):
    """
    GUI class, contains visualization options and is usually where the simulator will be called.
    """
    def __init__(self, filepath):
        klampt.vis.glprogram.GLRealtimeProgram.__init__(self, "ExoTest")
        #All the world elements MUST be loaded before the Simulator is created
        self.world = klampt.WorldModel()
        self.robot = None
        self.plan = None
        self.trajectory = None
        self.actuators = None
        self.sim = None
        self.worldSetup(filepath)
        #Simulator creation and activation comes at the very end
        self.sim.setGravity([0, 0, -9.8])

# Initialization
    def worldSetup(self, filepath_dict):
        """
        Sets up the world for the simulation, and initializes the simulation.
        """
        # Simulator is initialized
        # World is added to visualization
        klampt.vis.add("world", self.world)
        self.world.loadRobot(filepath_dict["core"])
        self.robot = self.world.robot(0)
        self.muscle = None
        self.point_a = None
        self.point_b = None
        # Robot is added to visualization
        klampt.vis.add("X001", self.robot)

        self.sim = ExoSim(self.world, self.robot)
        # creation of the controller
        self.XOS = klampt.control.robotinterfaceutils.RobotInterfaceCompleter(
            ExoController(self.robot, self.world, filepath_dict))

        # This is necessary

        self.drawEdges()
        self.muscle = None
        self.drawMuscle("bicep", 4, 6)


        klampt.vis.setWindowTitle("X001  Test")
        self.viewport = klampt.vis.getViewport()
        self.viewport.fit([0,0,-5], 25)
        self.sim.simLoop(self.robot)

    def idlefunc(self):
        pass

    """
    Simulation Methods
    """

    """
    Test Methods
    """
    def animationTest(self):
        """
        Animates the native trajectory.
        """
        klampt.vis.visualization.animate("X001", self.trajectory, speed=3, endBehavior="loop")
        klampt.vis.run()
        STOP_FLAG = False
        while STOP_FLAG == False:
            self.idlefunc()

        self.XOS.close()
        klampt.vis.kill()


    def torqueTest(self):

        print("OUTPUT FROM THE CONTROLLER:", self.XOS)
    """
    Visual Options
    """
    def drawMuscle(self, id, a, b):
        """
        Draws the muscle lines on the robot
        """
        assert type(id) == str, "Error: Muscle ID must be string value."

        self.muscle = klampt.GeometricPrimitive()
        self.point_a = self.world.robot(0).link(a).getTransform()[1]
        self.point_b = self.world.robot(0).link(b).getTransform()[1]
        print("Point A: ", self.point_a, "Point B: ", self.point_b)
        self.muscle.setSegment(self.point_a, self.point_b)
        klampt.vis.add(id, self.muscle)
        klampt.vis.setColor(id, 0,1,0,1)


    def drawEdges(self):
        """
        Changes some drawing options for link geometry
        """
        wm = self.world
        for x in range(wm.numIDs()):
            wm.appearance(x).setDraw(2, True) # Makes edges visible
            wm.appearance(x).setDraw(4, True) # I believe this should make edges glow
            wm.appearance(x).setColor(2, 1, 1, 1, 1) # Makes edges white, something about the surface normals is not right but it's fixable
            wm.appearance(x).setColor(3, .3, .3, .3, 1) # I think this makes the specularity color red


    """
    Shutdown
    """

    def shutdown(self):
        klampt.vis.kill()


"""
FUNCTION DEFINITIONS
"""
def configLoader():
    print("Loading config.txt...")
    with open("config.txt") as fn:
        print("Loading core components...", fn.readline().rstrip())
        core = fn.readline().rstrip()
        print("Loading right arm...", fn.readline().rstrip())
        rightarm = fn.readline().rstrip()
        print("Loading left arm...", fn.readline().rstrip())
        leftarm = fn.readline().rstrip()
        print("Loading right leg...", fn.readline().rstrip())
        rightleg = fn.readline().rstrip()
        print("Loading left leg...", fn.readline().rstrip())
        leftleg = fn.readline().rstrip()
        print("Loading muscle attachments...", fn.readline().rstrip())
        attachments = fn.readline().rstrip()


        config = {"core": core,
                      "rightarm": rightarm,
                      "leftarm": leftarm,
                      "rightleg": rightleg,
                      "leftleg": leftleg,
                      "attachments": attachments}

        return config


"""
MAIN LOOP
"""

if __name__ == "__main__":
    xo_parts = configLoader()
    print("xo_parts", xo_parts)
    exo_sim_test = ExoGUI(xo_parts)