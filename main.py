# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////
import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
from dpeaDPi.DPiComputer import *
from dpeaDPi.DPiStepper import *
from dpeaDPi.DPiComputer import DPiComputer

# ////////////////////////////////////////////////////////////////
# //                     HARDWARE SETUP                         //
# ////////////////////////////////////////////////////////////////
"""Stepper Motor goes into MOTOR 0 )
    Limit Switch associated with Stepper Motor goes into HOME 0
    One Sensor goes into IN 0
    Another Sensor goes into IN 1
    Servo Motor associated with the Gate goes into SERVO 1
    Motor Controller for DC Motor associated with the Stairs goes into SERVO 0"""
stepper_motor = 0

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 2
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()


# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////

# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40
    dpiStepper = DPiStepper()
    dpiStepper.setBoardNumber(0)
    if dpiStepper.initialize() != True:
        print("Communication with the DPiStepper board failed.")

    dpiStepper.enableMotors(True)
    microstepping = 8
    dpiStepper.setMicrostepping(microstepping)
    speed_steps_per_second = 200 * microstepping
    accel_steps_per_second_per_second = speed_steps_per_second
    dpiStepper.setSpeedInStepsPerSecond(stepper_motor, speed_steps_per_second)
    dpiStepper.setAccelerationInStepsPerSecondPerSecond(stepper_motor, accel_steps_per_second_per_second)
    dpiComputer = DPiComputer()
    dpiComputer.initialize()
    staircase = True
    staircase_speed = 90
    gate = False


    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()
        Clock.schedule_interval(self.debounce, .5)

    def toggleGate(self):
        self.openGate()

    def toggleStaircase(self):
        self.moveStaircase()

    def toggleRamp(self):
        #print("Move ramp up and down here")
        self.moveRamp()

    def auto(self):
        self.openGate()
        sleep(0.5)
        self.openGate()
        there = False
        while(there == False):
            there = self.isBallAtTopOfRamp()
        self.dpiComputer.writeServo(0, self.staircase_speed)
        sleep(7)
        self.dpiComputer.writeServo(0, 90)

    def setRampSpeed(self, speed):
        self.speed_steps_per_second = 200 * self.microstepping * speed
        self.accel_steps_per_second_per_second = self.speed_steps_per_second
        self.dpiStepper.setSpeedInStepsPerSecond(stepper_motor, self.speed_steps_per_second)
        self.dpiStepper.setAccelerationInStepsPerSecondPerSecond(stepper_motor, self.accel_steps_per_second_per_second)
        self.ids.rampSpeed.text = 'Ramp Speed: ' + str(speed)

    def setStaircaseSpeed(self, speed):
        math = 18 * (speed/10) + 90
        self.staircase = math
        print(self.staircase_speed)
        self.ids.staircaseSpeed.text = 'Staircase Speed: ' + str(speed)


    def initialize(self):
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        print("Exit")
        MyApp().stop()

    def debounce(self, dt):
        if (self.dpiComputer.readDigitalIn(self.dpiComputer.IN_CONNECTOR__IN_0) == 0):
            sleep(.05)
            if (self.dpiComputer.readDigitalIn(self.dpiComputer.IN_CONNECTOR__IN_0) == 0):
                self.moveRamp()
        else:
            return
        # ok, it's really pressed

    def moveRamp(self):
        steps = 45500
        wait_to_finish_moving_flg = True
        self.dpiStepper.setSpeedInStepsPerSecond(0, self.speed_steps_per_second)
        self.dpiStepper.setAccelerationInStepsPerSecondPerSecond(0, self.accel_steps_per_second_per_second)
        self.dpiStepper.moveToRelativePositionInSteps(0, -steps, wait_to_finish_moving_flg)
        self.dpiStepper.moveToHomeInSteps(0, 1, 10000, steps)
        self.dpiStepper.setSpeedInStepsPerSecond(0, self.speed_steps_per_second)
        self.dpiStepper.setAccelerationInStepsPerSecondPerSecond(0, self.accel_steps_per_second_per_second)
        self.dpiStepper.moveToRelativePositionInSteps(0, 400, wait_to_finish_moving_flg)

    def moveStaircase(self):
        if self.staircase:
            self.dpiComputer.writeServo(0, self.staircase_speed)
            self.staircase = False
        else:
            self.dpiComputer.writeServo(0, self.staircase)
            self.staircase = True

    def openGate(self):
        if self.gate == False:
            self.dpiComputer.writeServo(1, 180)
            self.gate = True
        else:
            self.dpiComputer.writeServo(1, 0)
            self.gate = False

    def isBallAtTopOfRamp(self):
        return self.dpiComputer.readDigitalIn(1)


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()