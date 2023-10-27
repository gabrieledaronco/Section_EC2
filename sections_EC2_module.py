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
    elastic_modulus = E, # Use either Cl. 8.6.2.2 or Cl. 8.6.2.3
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

def add_bars(bars_list:list[list[float]], conc_geom:Geometry, mat:SteelBar):
    for area,x,y in bars_list:
        reinf_geometry = add_bar(conc_geom, area=area,material=mat, x=x,y=y)
    return reinf_geometry


