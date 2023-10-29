#General import
from math import pi
import numpy as np

# Import stress/strain profiles
from concreteproperties.stress_strain_profile import (
    ConcreteLinearNoTension, 
    RectangularStressBlock, 
    SteelElasticPlastic
)

## Import materials
from concreteproperties.material import Concrete, SteelBar

## Import geometry functions for creating rectangular sections
from sectionproperties.pre.library.concrete_sections import concrete_rectangular_section
from sectionproperties.pre.geometry import Geometry, CompoundGeometry
from sectionproperties.pre.library import primitive_sections
from sectionproperties.pre.library.primitive_sections import rectangular_section
from concreteproperties.pre import add_bar, add_bar_rectangular_array

## Import analysis section
from concreteproperties.concrete_section import ConcreteSection

## Define material functions

def create_concrete(
        fc: float,
        fc_t:float, 
        E: float,
        gamma_r: float = 1.50, 
        ult_strain: float=0.0035,
        ):
    """
    Returns a concreteproperties concrete material with values
    imported., accordin to EC2
    """
    concrete_service = ConcreteLinearNoTension(
    elastic_modulus = E,
    ultimate_strain = ult_strain,
    compressive_strength =  fc,
    )

    ## Ultimate stress-strain profile
    concrete_ultimate = RectangularStressBlock(
        compressive_strength=fc,
        alpha= 1/gamma_r, 
        gamma= 0.8, 
        ultimate_strain=0.0035,
    )

    ## Defining the Concrete material
    concrete = Concrete(
        name=f"{fc} MPa Concrete",
        density = 2.4e-5, # Assumed, only used for self-weight
        stress_strain_profile=concrete_service,
        ultimate_stress_strain_profile=concrete_ultimate,
        flexural_tensile_strength=fc_t, 
        colour="lightgrey",
    )
    return concrete


def create_steelbar(fy: float, gamma_r: float=1.15):
    """
    Returns a concreteproperties steel material with values
    imported accordin to EC2
    """
    steel_elastic_plastic = SteelElasticPlastic(
            yield_strength=fy/gamma_r,
            elastic_modulus=200e3,
            fracture_strain=0.05,
    )

    ## Defining the SteelBar material
    steel = SteelBar(
        name=f"{fy} MPa Steel",
        density=7.7e-6,
        stress_strain_profile=steel_elastic_plastic,
        colour="black",
    )
    return steel

## Define Concrete rectangular section
def def_geom(height:float, width:float, mat:Concrete)-> Geometry:
    conc_geom = rectangular_section(b=width,d=height, material= mat).align_center()

    return conc_geom

##Add bars to section

def rect_bar_list(top_diameter:float, 
             bottom_diameter:float, 
             left_diameter:float,
             right_diameter:float,
             top_nr_bars:int,
             bottom_nr_bars:int,
             left_nr_bars:int,
             right_nr_bars:int,
             height:float,
             width:float,
             cover:float
             )->list[list[float]]:
    """
    retunrs a list[list] with the coordinates and the anrea of the reinf bars to be used
    assumptions: section has to be rectangular
    """
    area_top = (pi*top_diameter**2)/4
    area_bottom = (pi*bottom_diameter**2)/4
    area_left = (pi*left_diameter**2)/4
    area_right = (pi*right_diameter**2)/4
    s_top = (width-2*cover)/(top_nr_bars-1)
    s_bottom = (width-2*cover)/(bottom_nr_bars-1)
    s_left = (height-2*cover)/(left_nr_bars-1)
    s_right = (height-2*cover)/(right_nr_bars-1)
    top_list = []
    bottom_list=[]
    left_list=[]
    right_list=[]
    
    for i in range(top_nr_bars):
        if i ==0:
            x=-width/2+cover
            sub_list = [area_top, x, height/2-cover]
        else:
            x=x+s_top
            sub_list = [area_top, x, height/2-cover]
        top_list.append(sub_list)
    
    for i in range(bottom_nr_bars):
        if i ==0:
            x=-width/2+cover
            sub_list = [area_bottom, x, -height/2+cover]
        else:
            x=x+s_bottom
            sub_list = [area_bottom, x, -height/2+cover]
        bottom_list.append(sub_list)

    for i in range(left_nr_bars):
        if area_left == 0:
            continue
        elif i ==0:
            y=-height/2+cover
            sub_list = [area_left, -width/2+cover, y]
        else:
            y=y+s_left
            sub_list = [area_left, -width/2+cover, y]
        left_list.append(sub_list)
    
    for i in range(right_nr_bars):
        if area_right ==0:
            continue
        elif i ==0:
            y=-height/2+cover
            sub_list = [area_right, width/2-cover, y]
        else:
            y=y+s_right
            sub_list = [area_right, width/2-cover, y]
        right_list.append(sub_list)
    
    bar_list = top_list+bottom_list
    if area_left ==0 or area_right ==0:
        return bar_list
    else:
        for i in range(left_nr_bars):
            if i ==0 or i == left_nr_bars-1:
                continue
            else:
                bar_list.append(left_list[i])
        for i in range(right_nr_bars):
            if i ==0 or i == right_nr_bars-1:
                continue
            else:
                bar_list.append(right_list[i])        
        return bar_list

def add_bars(bars_list:list[list[float]], conc_geom:Geometry, mat:SteelBar)->CompoundGeometry:
    for rebar in bars_list:
        area, x, y = rebar
        conc_geom = add_bar(geometry=conc_geom, 
                                 area=area,
                                 material=mat, 
                                 x=x,
                                 y=y
                                 )
   
    return conc_geom


