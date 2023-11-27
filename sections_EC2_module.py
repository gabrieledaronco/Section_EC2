#General import
from math import pi
import numpy as np
import pandas as pd

# Import stress/strain profiles
from concreteproperties.stress_strain_profile import (
    ConcreteLinearNoTension, 
    RectangularStressBlock, 
    SteelElasticPlastic,
    EurocodeNonLinear,
    EurocodeParabolicUltimate
)

## Import materials
from concreteproperties.material import Concrete, SteelBar

## Import geometry functions for creating rectangular sections
from sectionproperties.pre.library.concrete_sections import concrete_rectangular_section, concrete_circular_section
from sectionproperties.pre.geometry import Geometry, CompoundGeometry
from sectionproperties.pre.library import primitive_sections
from sectionproperties.pre.library.primitive_sections import rectangular_section, circular_section
from concreteproperties.pre import add_bar, add_bar_rectangular_array
from concreteproperties.results import StressResult

## Import analysis section
from concreteproperties.concrete_section import ConcreteSection

## Define material functions

def create_concrete(
        fc: float,
        fcm: float,
        fc_t:float, 
        E: float,
        eps_cu1: float,
        eps_c1: float,
        eps_cu2: float,
        eps_c2: float,
        n:float,
        gamma_r: float = 1.50, 
        ):
    """
    Returns a concreteproperties concrete material with values
    imported, according to EC2
    """
    ec2_non_linear = EurocodeNonLinear(
    elastic_modulus = E,
    ultimate_strain = eps_cu1,
    compressive_strength = fcm,
    compressive_strain= eps_c1,
    tensile_strength= fc_t,
    tension_softening_stiffness= 10e+3
    )

    linear_no_tension = ConcreteLinearNoTension(
    elastic_modulus = E,
    ultimate_strain = eps_cu1,
    compressive_strength =  fc,
    )

    ## Ultimate stress-strain profile
    stress_block = RectangularStressBlock(
        compressive_strength=fc,
        alpha= 1/gamma_r, 
        gamma= 0.8, 
        ultimate_strain=eps_cu2,
    )

    ec2_ultimate = EurocodeParabolicUltimate(
        compressive_strength=fc/gamma_r,
        compressive_strain= eps_c2,
        ultimate_strain=eps_cu2,
        n=n
    )

    ## Defining the Concrete material
    concrete = Concrete(
        name=f"{fc} MPa Concrete",
        density = 2.4e-5, # Assumed, only used for self-weight
        stress_strain_profile=linear_no_tension,
        ultimate_stress_strain_profile= stress_block,
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
def def_r_geom(height:float, width:float, mat:Concrete)-> Geometry:
    conc_geom = rectangular_section(b=width,d=height, material= mat).align_center()

    return conc_geom

def def_c_geom(diameter:float, mat:Concrete)-> Geometry:
    conc_geom = circular_section(d=diameter, n=36, material= mat).align_center()

    return conc_geom

##Add bars to section

def rect_bar_list(bars_df:pd.Series,
             height:float,
             width:float,
             )->list[list[float]]:
    """
    retunrs a list[list] with the coordinates and the anrea of the reinf bars to be used
    assumptions: section has to be rectangular
    """
    diam = bars_df["Bars diameter [mm]"]
    area = bars_df["Area"]
    nr_bars = int(bars_df["Number of bars"])
    cover = bars_df["Cover [mm]"]
    bar_list=[]
    
    if bars_df.name == "Top layer 1":
        s = (width -2*cover)/(nr_bars-1)
        x = -width/2+cover
        y = height/2-cover
    elif bars_df.name == "Top layer 2":
        s = (width -2*cover)/(nr_bars-1)
        x = -width/2+cover
        y = height/2-cover-diam*1.2
    elif bars_df.name == "Bottom layer 1":
        s = (width -2*cover)/(nr_bars-1)
        x = -width/2+cover
        y = -height/2+cover
    elif bars_df.name == "Bottom layer 2":
        s = (width -2*cover)/(nr_bars-1)
        x = -width/2+cover
        y = -height/2+cover+diam*1.2
    elif bars_df.name == "Side layer 1":
        nr_bars=nr_bars+2
        s = (height -2*cover)/(nr_bars-1)
        x = -width/2+cover
        y = -height/2+cover
    elif bars_df.name == "Side layer 2":
        nr_bars=nr_bars+2
        s = (height -2*cover)/(nr_bars-1)
        x = -width/2+cover+diam*1.2
        y = -height/2+cover

    for i in range(nr_bars):
        if area == 0:
            continue
        elif i ==0:
            if bars_df.name[0:4] == "Side":
                continue
            else:
                sub_list = [area, x, y]
        elif i== (nr_bars-1) and bars_df.name[0:4] == "Side":
            continue
        else:
            if bars_df.name[0:4] == "Side":
                y=y+s
            else:
                x=x+s
            sub_list = [area, x, y]
        bar_list.append(sub_list)
    
    return bar_list


def add_bars(bars_df:pd.Series, conc_geom:Geometry, mat:SteelBar)->CompoundGeometry:
    """
    add bars from a list[list]
    the side bars are located in rows 4 and 5
    """
    for i in range(len(bars_df)):
        if i==4 or i==5:
            for rebar in bars_df.iloc[i]:
                area, x, y = rebar
                conc_geom = add_bar(geometry=conc_geom, 
                                        area=area,
                                        material=mat, 
                                        x=x,
                                        y=y
                                        )
                conc_geom = add_bar(geometry=conc_geom, 
                                        area=area,
                                        material=mat, 
                                        x=-x,
                                        y=y
                                        )
        else:
            for rebar in bars_df.iloc[i]:
                area, x, y = rebar
                conc_geom = add_bar(geometry=conc_geom, 
                                        area=area,
                                        material=mat, 
                                        x=x,
                                        y=y
                                        )
    return conc_geom

def concrete_EC2(fck:float)->pd.Series:
    """
    return a series with the poperties of Concrete according to EC2
    the results are in MPa
    """
    fcm = fck+8
    fctm = (fck<=50)*(0.3*fck**(2/3))+(fck > 50)*(2.12*np.log(1+fcm/10))
    concrete_serie = pd.Series(data={
        "fck":fck,
        "fcm": fcm,
        "fctm": fctm,
        "fctk_05": 0.7*fctm,
        "fctk_95": 1.3*fctm,
        "Ecm": 22*(fcm/10)**0.3*1000,
        "eps_c1": min([0.7*fcm**0.31,2.8])/1000,
        "eps_cu1": 3.5/1000 if fck < 50 else (2.8 +27*((98-fcm)/100)**4)/1000,
        "eps_c2": 2.0/1000 if fck < 50 else (2+0.085*(fck-50)**0.53)/1000,
        "eps_cu2":3.5/1000 if fck < 50 else (2.6+35*((90-fck)/100)**4)/1000,
        "n": 2.0 if fck < 50 else 1.4+23.4*((90-fck)/100)**4
    }
    )
    return concrete_serie

def get_stress_df (CrackedStress:StressResult)->pd.DataFrame:
    """
    returns a dataframe with the coords of the bars and the stresses
    """
    columns = [
        "Bar No.",
        "x location [mm]",
        "y location [mm]",
        "Area [mm2]",
        "Stress [MPa]",
        "Force [kN]",
        "Lever Arm [mm]",
        "Moment [kNm]"
    ]

    forces = []
    moments_x = []
    data = []
    for idx, reinf_geom in enumerate(CrackedStress.lumped_reinforcement_geometries):
    # get the reinforcement results
        centroid = reinf_geom.calculate_centroid()
        area = reinf_geom.calculate_area()
        stress = CrackedStress.lumped_reinforcement_stresses[idx]
        strain = CrackedStress.lumped_reinforcement_strains[idx]
        force, d_x, d_y = CrackedStress.lumped_reinforcement_forces[idx]

    # calculate the moment each bar creates and store the results
        moment_x = force * d_y
        forces.append(force)
        moments_x.append(moment_x)

        data.append([idx+1,
                    centroid[0],
                    centroid[1],
                    round(area,1),
                    stress.round(1),
                    (force/1e3).round(1),
                    d_y.round(1),
                    (moment_x/1e6).round(1)
                    ]
                    )
    
    df= pd.DataFrame(data=data, columns=columns)
    df=df.set_index("Bar No.")

    return df




