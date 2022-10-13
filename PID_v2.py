# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 21:55:28 2022
===============
Document Comments:
    10.11.22
    2218h 
    I think the index should be separate from the time values. Physics should 
    be based on time independent of the index so that I can have a consistent 
    indexing scheme regardless of the time resolution of the data.

===============
LIBRARY IMPORTS
"""
import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg
from scipy.integrate import odeint
import turtle


"""
CONFIG
"""
pd.options.display.width = 0
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

"""
GUI Initialization
"""


"""
GLOBALS
"""


"""
FUNCTION DEFINITIONS
"""

def gui():
    window = tk.Tk()
    window.title("PID Controller v1.a")
    frame = ttk.Frame(window, padding = 10)
    
    POS_START = tk.DoubleVar() # meters
    VEL_START =  tk.DoubleVar() # m/s
    ACCEL_START =  tk.DoubleVar() # m/s^2
    T_START =  tk.IntVar() # seconds
    T_END =  tk.IntVar() # seconds

    MASS =  tk.DoubleVar() # kilograms

    # PID parameters
    SET_POINT = tk.DoubleVar() # float(input("Set point of speed to maintain? "))
    P_K = tk.DoubleVar() # float(input("Proportional term? "))
    I_K = tk.DoubleVar() # float(input("Integral term? "))
    D_K = tk.DoubleVar() # float(input("Derivative term? "))
    SCALE_FACTOR = tk.DoubleVar() #float(input("Scaling factor for external disturbance? "))
    CONTROL_CONSTANT = tk.DoubleVar() # this is your k omega
    CONTROL_SIGN = True # this should be a checkbox
    throttle_f = 0.0 # initial force applied by throttle = 0

    """
    Initialization Parameters
    """
    # Kinematic parameters

    position_start_slider = ttk.Scale(
        frame,
        from_ = 10,
        to = 100,
        orient = "horizontal",
        variable = POS_START)

    velocity_start_slider = ttk.Scale(
        frame,
        from_ = 37,
        to = 100,
        orient = "horizontal",
        variable = VEL_START) 

    accel_start_slider = tk.Scale(
        frame,
        from_ = 16,
        to = 100,
        orient = "horizontal",
        variable = ACCEL_START) 

    t_start_slider = tk.Scale(
        frame,
        from_ = 1,
        to = 100,
        orient = "horizontal",
        variable = T_START) 

    t_end_slider = tk.Scale(
        frame,
        from_ = 53,
        to = 100,
        orient = "horizontal",
        variable = T_END) 

    mass_slider = tk.Scale(
        frame,
        from_ = 2,
        to = 100,
        orient = "horizontal",
        variable = MASS)

    scale_factor_slider = tk.Scale(
        frame,
        from_ = 2,
        to = 100,
        orient = "horizontal",
        variable = SCALE_FACTOR)  


    # PID parameters

    set_point_slider = tk.Scale(
        frame,
        from_ = 10,
        to = 100,
        orient = "horizontal",
        variable = SET_POINT)

    p_k_slider = tk.Scale(
        frame,
        from_ = 37,
        to = 100,
        orient = "horizontal",
        variable = P_K) 

    i_k_slider = tk.Scale(
        frame,
        from_ = 16,
        to = 100,
        orient = "horizontal",
        variable = I_K) 

    d_k_slider = tk.Scale(
        frame,
        from_ = 1,
        to = 100,
        orient = "horizontal",
        variable = D_K) 

    # Control constant
    control_constant_slider = tk.Scale(
        frame,
        from_ = 53,
        to = 100,
        orient = "horizontal",
        variable = CONTROL_CONSTANT) 

    # This should be a checkbox that just flips
    control_sign = tk.Scale(
        frame,
        from_ = 2,
        to = 100,
        orient = "horizontal",
        variable = MASS) 
    
#    window.mainloop()
    pass

def noise_f(k):
    whitenoise = np.random.normal(1,2)
    scaled_noise = k * whitenoise
    return scaled_noise

def total_samples(sample_rate=20, total_time=20):
    total_samples = sample_rate * total_time
    return total_samples

def time(num_samples, sample_rate, df):
    time_value_list = list((x * (1/sample_rate) for x in range(num_samples)))
    time_value_series = pd.Series(data=time_value_list)
    df["time"] = time_value_series
    return df

def mass(num_samples, df):
    mass = 1
    mass_list = []
    for i in range(num_samples):
        mass_list.append(mass)
    print(mass_list)
    mass_series = pd.Series(data = mass_list)
    print(mass_series)
    df["mass"] = mass_series

    return df

def disturbance_force(num_samples, df):
    disturbance = 1
    disturbance_list = []
    for i in range(num_samples):
        disturbance_list.append(disturbance)
    print(disturbance_list)
    disturbance_series = pd.Series(data = disturbance_list)
    df["disturbance_force"] = disturbance_series
    return df

def throttle_force():
    force = 0
    return force

def total_force(external_f, throttle_f):
    return external_f + throttle_f
    
def acceleration(force=0, mass=1):
    accel = force/mass
    return accel

def velocity(df):
    pass

def position(df):
    pass

def error(process_variable, set_point):
    return set_point - process_variable

def pid(error=0):
    proportional = error
    integral = np.trapz(error)
    derivative = np.gradient(error)
    pass

def row_maker(total_samples, smp_rate):
    headers = ["time","mass", "disturbance_force", "throttle_force", "total_force", "acceleration", "velocity", "position", "error", "pid"]
    df = pd.DataFrame(columns=headers, index=range(total_samples))
    return df

def init():
    #command_line = bool(input("Run in command line mode? "))
    sample_rate = int(input("Sample rate in Hz (int): "))
    total_time = int(input("Total time in seconds (int): "))
    sample_number = total_samples(sample_rate, total_time)
    return(sample_number, sample_rate)

def main():
    total_samples, sample_freq = init()
    time_series = row_maker(total_samples, sample_freq)
    df = time(total_samples, sample_freq, time_series)
    df = mass(total_samples, df)
    df = disturbance_force(total_samples, df)
    print(df)
    print(df.columns)
    return 

main()