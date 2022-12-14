"""
DEVELOPER COMMENTS

This should probably also be a core element and not have external dependencies.
"""

"""
LIBRARY IMPORTS
"""
import sys
sys.path.append(r"/Pyonics/submodules")
import numpy as np
import pandas as pd
"""
CLASS DEFINITIONS
"""
class PIDController():
    def error(self, set_point, df, i):
        """
        Determines the error.
        :param process_variable:
        :param set_point:
        :param df: main dataframe
        :param i: time step
        :return: modified dataframe
        """
        error = set_point - df.at[i, "velocity"]
        df.at[i, "error"] = error
        return df

    def pid(self, df, i, p_k, i_k, d_k, scaling_factor):
        """
        Performs the PID logic.
        :param df: main dataframe
        :param i: time step
        :return: modified dataframe
        """
        df_abridged = df[0:i]
        proportional = p_k * df.at[i, "error"]
        integral = i_k * np.trapz(df_abridged["error"])
        if i < 2:
            derivative = 0
        else:
            gradient = np.gradient(df_abridged["error"])
            derivative = d_k * float(gradient[-2:-1])
        pid = scaling_factor * (proportional + integral + derivative)
        df.at[i, "proportional"] = proportional
        df.at[i, "integral"] = integral
        df.at[i, "derivative"] = derivative
        df.at[i, "control"] = pid
        return df

    def __init__(self):
        pass
"""
FUNCTION DEFINITIONS
"""


def error(set_point, df, i):
    """
    Determines the error.
    :param process_variable:
    :param set_point:
    :param df: main dataframe
    :param i: time step
    :return: modified dataframe
    """
    error = set_point - df.at[i, "velocity"]
    df.at[i, "error"] = error
    return df


def pid(df, i, p_k, i_k, d_k, scaling_factor):
    """
    Performs the PID logic.
    :param df: main dataframe
    :param i: time step
    :return: modified dataframe
    """
    df_abridged = df[0:i]
    proportional = p_k * df.at[i, "error"]
    integral = i_k * np.trapz(df_abridged["error"])
    if i < 2:
        derivative = 0
    else:
        gradient = np.gradient(df_abridged["error"])
        derivative = d_k * float(gradient[-2:-1])
    pid = scaling_factor * (proportional + integral + derivative)
    df.at[i, "proportional"] = proportional
    df.at[i, "integral"] = integral
    df.at[i, "derivative"] = derivative
    df.at[i, "control"] = pid
    return df