"""
Should contain interface elements for inside the robot as well as when it is plugged into a computer.
====
LIBRARY IMPORTS
"""
# Standard Libraries
import asyncio
import random
import pyaudio
from OpenGL.GL import *
from OpenGL.GLUT import *

# Klampt Libraries
import klampt
import klampt.vis as kvis

# Third Party Libraries
import transformers
import pygame as pygame  # Multimedia integration with OpenGL
from pygame.locals import *
import customtkinter as ctk  # Different UI options
import pyttsx3  # Text to speech
import vosk  # Voice recognition library

# My Custom Libraries
from . import system_strings as sysvx
from ..apps.apps import Map, Camera, Clock, DateWidget, TextWidget

"""
FUNCTION DEFINITIONS #1 
"""
# Most of them should go here, any down after the class definitions are there only to avoid screwing things up right now
def colorCalc(current_pressure, max_pressure):
    # Calculates a color based on a current and max value
    if current_pressure / max_pressure < 1:
        return current_pressure / max_pressure
    else:
        return 1

def visMuscles(dataframe_row):
    # Takes a dataframe row as a namedtuple and adds muscle to visualization
    name = dataframe_row[1]  # Should be the name index
    muscle = dataframe_row[-1]  # Index of the muscle object
    greenness = colorCalc(muscle.pressure, muscle.max_pressure)  # Should always be less than 1s
    klampt.vis.add(name, muscle.geometry)  # Adds the shape of the muscle - must happen
    klampt.vis.setColor(name, 0, greenness, 0, 1)  # Sets the color of the muscle (currently green
    klampt.vis.hideLabel(name)  # Hides the name of the muscle


"""
CLASS DEFINITIONS
"""
# Parent Class

class Personality:
    def __init__(self):
        from transformers import TFGPT2LMHeadModel, TFGPT2Tokenizer
        self.friendliness = 0.5
        self.formality = 0.5
        self.humor = 0.5
        self.excitement = 1
        model_name = "gpt2"  # You can use other variations like "gpt2-medium", "gpt2-large", or "gpt2-xl"
        self.tokenizer = TFGPT2Tokenizer.from_pretrained(model_name)
        self.model = TFGPT2LMHeadModel.from_pretrained(model_name)

    def process_input(self, input_text):

        input_ids = self.tokenizer.encode(input_text, return_tensors="pt")
        output = self.model.generate(input_ids, max_length=100, num_beams=5, no_repeat_ngram_size=2, top_k=50, top_p=0.95,
                            temperature=0.7)
        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return generated_text

    # Example text generation
    def encode_input(self, input_text):
        input_ids = self.tokenizer.encode(input_text, return_tensors="pt")
        return input_ids

    # Generate text
    def generate_output(self, input_ids):
        output = self.model.generate(input_ids, max_length=100, num_beams=5, no_repeat_ngram_size=2, top_k=50, top_p=0.95,
                            temperature=0.7)
        return output

    # Decode and print the generated text
    def decodeprint_output(self, output):
        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return generated_text
    def ask(self):
        return ""

    def order(self):
        return ""

    def update_personality(self, feedback):
        # Adjust personality parameters based on user feedback
        # Update the values in personality_params
        self.personality_params = feedback
        return "Personality updated."

class VoiceAssistantUI: # For voice control
    # Should be most of the audio interaction with a UI
    def __init__(self, voice_index: int, rate: int):
        # TTS Engine Initialization
        self.voice_engine = pyttsx3.init()
        self.voices = self.voice_engine.getProperty("voices")
        self.voice_engine.setProperty('rate', rate)
        self.voice_engine.setProperty('voice', self.voices[voice_index].id)

        self.recog_model = None
        self.voice_recog = None
        self.user_cam = None

        self.mic = None
        self.stream = None
        self.voice_launch()
        #self.voice_test()

    def shutdown_assistant(self):
        # Shuts down and releases resources
        self.voice_engine.stop()

    def announce(self, stringvar):
        print(stringvar)
        self.voice_engine.say(stringvar)
        self.voice_engine.runAndWait()
        return stringvar

    def voice_launch(self):
        # Voice Recognition Initialization
        self.recog_model = vosk.Model(model_name="vosk-model-small-en-us-0.15")
        self.voice_recog = vosk.KaldiRecognizer(self.recog_model, 16000)
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=81)
        self.stream.start_stream()
        # Tests/ Strings
        self.voice_engine.runAndWait()

    def voice_loop(self):
        data = self.stream.read(1024)
        if self.voice_recog.AcceptWaveform(data):
            text = self.voice_recog.Result()
            print(f"{text[14:-3]}")
            return(text)

    def voice_test(self):
        # Plays all the strings and voices in the catalog to test for audio quality.
        test_strings = sysvx.confused + sysvx.affirmatives + sysvx.negatives
        i = 0
        for voice in self.voices:
            print(voice, voice.id)
            self.voice_engine.setProperty('voice', voice.id)
            self.voice_engine.say(test_strings[random.randint(0, len(test_strings))]) # What they say goes here
            self.voice_engine.runAndWait()
            self.voice_engine.stop()
            i = (i + 1) % len(self.voices)

class AugmentOverlayKlUI(kvis.glcommon.GLMultiViewportProgram):
    # For a Heads-Up Display or Helmet Mounted Display. This version uses Klampt vis plugins from the ground up.
    def __init__(self):
        pygame.init()  # Starts pygame multimedia library

        # Add text to the visualization
        font = pygame.font.SysFont(None, 36)


        # Creates the HUD display world
        self.holodeck = klampt.WorldModel()

        kvis.glcommon.GLMultiViewportProgram.__init__(self)  # Maybe here is where we embed it?
        # Sets up widgets on the display

        kvis.show()  # Opens the visualization for the first time

        kvis.setWindowTitle("Klampt HUD  Test")
        kvis.setBackgroundColor(0, 0, 0, 1)  # Makes background black
        kvis.resizeWindow(1920,1080)

        #self.viewport = kvis.getViewport() # testing pygame backend
        self.viewport = pygame.display.get_surface()

        self.date = DateWidget()
        self.clock = Clock()
        self.missions = TextWidget()
        self.missions.update("No Missions")

        self.camera = Camera(0)
        self.subtitles = TextWidget()
        self.subtitles.update("this is where the subtitles of whoever you are listening to will go")

        # Create the visualization
        kvis.add("world", self.holodeck)
        kvis.addText("time", self.clock.time, position=(0,-100), size=50)
        kvis.addText("date", self.date.date, position=(0,0), size=50)

        # Length 2 is relative to xy, length 3 is in world coordinates
        kvis.addText("missions", self.missions.text, position=(-300,0), size=50)
        kvis.addText("subtitles", self.subtitles.text, position=(400, 500), size=40)
        kvis.setColor("time", 1,1,1,1)
        kvis.setColor("date", 1,1,1,1)
        kvis.setColor("missions", 1,1,1,1)
        kvis.setColor("subtitles", 1,1,1,1)

        self.artificial_horizon = kvis.GeometricPrimitive()
        self.artificial_horizon.setSphere((0,0,0), 100)


        # Move the window to the upper left
        display_size = (1920,1080)
        # Get the Pygame display surface
        screen = pygame.display.get_surface()


        pygame.FULLSCREEN = True
        pygame.display.set_mode(display_size, DOUBLEBUF | OPENGL | NOFRAME)
        pygame.display.is_fullscreen()  # I wanted this to be a command
        self.drawOptions()
        # Begin desktopGUI event loop
        asyncio.run(self.async_handler())

    async def idle(self):
        """
        Idle function for the desktopGUI that sends commands to the controller, gets forces from it, and sends to the sim.
        """
        kvis.lock()  # Locks the klampt visualization
        kvis.clearText()
        self.clock.update()
        self.date.update()
        kvis.addText("time", self.clock.time, position=(0,-100), size=50)
        kvis.addText("date", self.date.date, position=(0,0), size=50)
        # Length 2 is relative to xy, length 3 is in world coordinates
        kvis.addText("missions", self.missions.text, position=(-300,0), size=50)
        kvis.addText("subtitles", self.subtitles.text, position=(400, 500), size=40)
        kvis.setColor("time", 1,1,1,1)
        kvis.setColor("date", 1,1,1,1)
        kvis.setColor("missions", 1,1,1,1)
        kvis.setColor("subtitles", 1,1,1,1)
        kvis.unlock()  # Unlocks the klampt visualization
        kvis.update()
        self.display()
        return True

    async def async_handler(self):
        while kvis.shown():
            await self.idle()  # Updates what is displayed
            await asyncio.sleep(0)  # Waits a bit to relinquish control to the OSC handler

        """
        Visual Options
        """

    def drawOptions(self):
        """
        Changes some drawing options for link geometry
        In the setDraw function, the first argument is an integer denoting vertices, edges. etc. The second is a Boolean
        determining regardless of whether the option is drawn.

        setColor function takes an int and RGBA float values.
        """
        wm = self.holodeck
        for x in range(wm.numIDs()):
            wm.appearance(x).setDraw(2, True)  # Makes edges visible
            wm.appearance(x).setColor(2, 0, 1, 0, .5)  # Makes edges green?
            # wm.appearance(x).setColor(4, .1, .1, .1, .1)  # This makes the faces a translucent blue grey
            # wm.appearance(x).setColor(4, 0, 1, 0, .5)  # I think this changes the glow color
            # wm.appearance(x).setDraw(4, True)  # I believe this should make edges glow
        """
        Shutdown
        """
    async def shutdown(self):
        self.hud.close_all()
        kvis.kill()

class AugmentOverlayTkUI:
    # For a Heads-Up Display or Helmet Mounted Display. This version uses Tkinter.
    def __init__(self, controller, assistant, has_missions=True, has_map=True,
                 has_camera=True, has_clock=True, has_date=True, has_compass=False):
        # boolean values are rapidly becoming more of them
        self.root_HUD = ctk.CTk()  # root_HUD is the tkinter root window

        if not assistant:
            # If no voice assistant assigned uses the controller's built-in assistant
            self.assistant = controller.assistant
        else:
            # Applies the assigned voice assistant
            self.assistant = assistant

        # HUDisplay options using tkinter

        self.root_HUD.overrideredirect(True)  # Makes it borderless
        self.root_HUD.geometry("1920x1080+0+0")  # Sets the size of the window
        self.root_HUD.attributes("-alpha", 0.5)  # Make the window transparent
        self.root_HUD.configure(background="black")  # Makes the background black

        # Sets up the map
        if has_map:
            self.map = Map(self.root_HUD, w=300, h=250)
            self.map.widget.grid(row=3,column=5)
        else:
            self.map = None

        # Sets up the clock
        if has_clock:
            self.clock = Clock(self.root_HUD)
            self.clock.grid(row=3,column=0, sticky="sw")
        else:
            self.clock = None

        # Sets up the date widget
        if has_date:
            self.date = DateWidget(self.root_HUD)
            self.date.grid(row=0,column=0, sticky="nw")
        else:
            self.date = None

        # Sets up compass
        if has_compass:
            self.compass = Compass(self.root_HUD)
            self.compass.grid(column=2,row=2, sticky="n")
        else:
            self.compass = None

        # Sets up the camera feed and display if present
        if has_camera:
            self.camera = Camera(0)
        else:
            self.camera = None

        # Sets up mission info display
        if has_missions:
            self.missions = TextWidget(self.root_HUD, "no missions")
            self.missions.grid(column=5,row=0, sticky="ne")
        else:
            self.missions = None

        self.stop = ctk.CTkButton(self.root_HUD, command=lambda:asyncio.run(self.close_all()), text="STOP", font=("System", 200),
                                  fg_color="transparent", text_color="red", width=800)
        self.stop.grid(column=1,row=0)

        # Style changes
        self.hud_color = "red"
        self.root_HUD.focus_force()
        self.root_HUD.mainloop()

    async def close_HUD(self):
        # Closes the root_HUD
        self.assistant.announce("Closing heads-up display.")
        self.root_HUD.destroy()
        self.assistant.shutdown_assistant()

    async def close_all(self):
        # Closes the root_HUD
        self.assistant.announce("Shutting down system.")
        self.root_HUD.destroy()
        self.assistant.shutdown_assistant()
        self.controller.shutdown()

    def refresh(self):
        # Update everything on the screen
        self.hud_color = "blue"
        pass

"""
FUNCTION DEFINITIONS
"""

"""
Main Function
"""

def main():
    return

if __name__ == "__main__":
    main()