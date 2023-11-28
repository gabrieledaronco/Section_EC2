import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class Column_EC2:
    """
    A data type to describe the data required to compute the capacity of a  concrete 
    column.
    
    Assumptions: 
        - All values are in SI units
        - h is the clear height of the column
        - E is the elastic modulus
        - A is the cross sectional area
        - Ix is the Second moment of area about the x-axis (strong axis)
        - Iy is the Second moment of area about the y-axis (weak axis)
        - kx is the effective length factor about the x-axis
        - ky is the effective length factor about the y-axis
    """

    h: float
    E: float
    A: float
    c: float
    d:float
    sigma_s:float

    def crack_width(self, cracked_df:pd.DataFrame, kc:float, x_nn:float)-> float:
        """
    returns the crack width of a sections
    
    Assumptions: 
        - All values are in SI units
        - x_nn is the neutral axis depth
        - sigma_s is the maximum tensile stress in the bars


    """
        h_eff= min(2.5*(self.h-self.d),(self.h-self.x)/3, self.h/2)