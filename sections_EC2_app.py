import streamlit as st
import plotly.graph_objects as go
from matplotlib.figure import Figure
import sections_EC2_module as sm
from io import BytesIO
import numpy as np
import pandas as pd
## Import analysis section
from concreteproperties.concrete_section import ConcreteSection
from concreteproperties.results import MomentInteractionResults, MomentCurvatureResults
from concreteproperties.pre import add_bar_circular_array
from sectionproperties.pre.library.primitive_sections import rectangular_section, circular_section

st.header("Reinforced Concrete Sections")
st.subheader(f"Uniaxial bending")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Geometry","M-N Results", "Cracking", "Curvature", "Shear Resistance"])

with st.sidebar:
    side_tab1, side_tab2, side_tab3 = st.tabs(["Materials","Geometry", "Actions"])
    with side_tab1:
        st.subheader("Concrete")
        concrete_grade = st.selectbox("Concrete Grade",("C25/30",
                                     "C30/37",
                                     "C35/45",
                                     "C40/45",
                                     "C40/50",
                                     "C50/60",
                                     "C55/67",
                                     "C60/75",
                                     "C80/95",
                                     "C90/105"
                                     ))
       
        c_fc = float(concrete_grade[1:3])
        concrete_serie = sm.concrete_EC2(c_fc)
        c_fct = concrete_serie.fctm
        c_E = concrete_serie.Ecm
        st.caption(f"Caracteristic compressive resistance = {c_fc} MPa")
        st.caption(f"Elastic modulus = {int(c_E)} MPa")

        st.divider()
        st.subheader("Steel Rebar")
        steel_grade = st.selectbox("Steel Grade",("B450C",
                                     "B500C",
                                     ))
        s_fy = float(steel_grade[1:4])
        st.caption(f"Yielding Strength= {s_fy} MPa")
    
    with side_tab2:
        section_type = st.selectbox("Section Type",("Rectangular",
                                     "Circular",
                                     ))
        st.subheader("Section Geometry")
        if section_type == "Rectangular":
            s_h = st.number_input("height [mm]", value=1000)
            s_b = st.number_input("width [mm]", value=1000)
        elif section_type == "Circular":
            s_d = st.number_input("diameter [mm]", value=1000)


        st.subheader("Reinforcement Bars")
        if section_type == "Rectangular":
            bars_df = pd.DataFrame(
                [{"Bars diameter [mm]":25, "Number of bars":4, "Cover [mm]":50},
                 {"Bars diameter [mm]":25, "Number of bars":0, "Cover [mm]":50},
                 {"Bars diameter [mm]":25, "Number of bars":4, "Cover [mm]":50},
                 {"Bars diameter [mm]":25, "Number of bars":0, "Cover [mm]":50},
                 {"Bars diameter [mm]":25, "Number of bars":2, "Cover [mm]":50},
                 {"Bars diameter [mm]":25, "Number of bars":0, "Cover [mm]":50},
                 ], index=["Top layer 1",
                           "Top layer 2",
                            "Bottom layer 1",
                            "Bottom layer 2",
                            "Side layer 1",
                            "Side layer 2"]
            )
            edited_df = st.data_editor(bars_df)
            diameters = edited_df.loc[:,"Bars diameter [mm]"]
            areas = (np.pi*diameters**2)/4
            modified_df = pd.concat([edited_df,areas],axis=1)
            modified_df.columns=["Bars diameter [mm]",
                                 "Number of bars",
                                 "Cover [mm]",
                                 "Area"]
            
        
        elif section_type == "Circular":
            b_diameter= st.number_input("Bars diameter [mm]",value = 25)
            b_nr_bars= st.number_input("Number of bars", value = 10 )
            cover = st.number_input("Cover [mm]", value=50)

    with side_tab3:
        st.caption("Compression is positive")
        st.caption("Positive moment produces tension on lower side")
        st.subheader("ULS")
        n_action= st.number_input("ULS Axial force [kN]",value=200.0)
        m_action= st.number_input("ULS Bending Moment [kNm]",value=500.0)
        st.subheader("SLS")
        sls_n_action= st.number_input("SLS Axial force [kN]",value=100.0)
        sls_m_action= st.number_input("SLS Bending Moment [kNm]",value=300.0)


#Define materials
concrete = sm.create_concrete(fc=concrete_serie.fck,
                              fcm=concrete_serie.fcm,
                              fc_t=concrete_serie.fctm,
                              E=concrete_serie.Ecm,
                              eps_cu1=concrete_serie.eps_cu1,
                              eps_c1=concrete_serie.eps_c1,
                              eps_cu2=concrete_serie.eps_cu2,
                              eps_c2=concrete_serie.eps_c2,
                              n=concrete_serie.n)
steel_rebar=sm.create_steelbar(fy=s_fy,gamma_r=1.15)

#Define concrete geometry
if section_type == "Rectangular":
    conc_geom = sm.def_r_geom(height=s_h,width=s_b, mat=concrete)
    bars_serie = modified_df.apply(sm.rect_bar_list,
                                   axis=1,
                                   args=(s_h,s_b)
                                )
    
    conc_geom = sm.add_bars(bars_df=bars_serie,
                                     conc_geom=conc_geom,
                                     mat=steel_rebar)


elif section_type == "Circular":
    conc_geom = sm.def_c_geom(diameter=s_d, mat=concrete)
    conc_geom = add_bar_circular_array(
                    geometry=conc_geom,
                    area=0.25*np.pi*b_diameter**2,
                    material=steel_rebar, 
                    n_bar=b_nr_bars,
                    r_array=s_d/2-cover)

#Define concrete section
conc_section = ConcreteSection(conc_geom)


#Actions
actions_dict = {"L1":(n_action,m_action),}
actions=list(actions_dict.values())
actions_ordered=list(zip(*actions))

#Caclutate Mr for each N (CREARE TABELLA PER METTERE I VALORI)
capacity_moments={}
for name,actions in actions_dict.items():
    if actions[1]>0:
        mr = conc_section.ultimate_bending_capacity(theta=0, n= actions[0]*1e3)
    else:
        mr = conc_section.ultimate_bending_capacity(theta=np.pi, n= actions[0]*1e3)
    capacity_moments.update({name:mr.m_xy/1e6})

#Calculate Cracked Section
if sls_m_action >0:
    cracked_res = conc_section.calculate_cracked_properties(theta=0)
else:
    cracked_res = conc_section.calculate_cracked_properties(theta=np.pi)
cracked_stress_res = conc_section.calculate_cracked_stress(
    cracked_results=cracked_res,n= sls_n_action*1e3, m=sls_m_action*1e6
)

#print N-M curve with actions
m_n_0=conc_section.moment_interaction_diagram(theta=0)
m_n_180=conc_section.moment_interaction_diagram(theta=np.pi)

#Tabs display:

with tab1:
    fig = Figure()
    ax = fig.gca()
    ax = conc_section.plot_section()
    fig=ax.get_figure()

    temp_fig= BytesIO()
    fig.savefig(temp_fig, format="png")
    st.image(temp_fig)

    
with tab2:
  
    fig_2 = Figure()
    ax_2 = fig_2.gca()
    ax_2 = MomentInteractionResults.plot_multiple_diagrams(
    moment_interaction_results=[m_n_0, m_n_180],
    labels=["Positive", "Negative"],
    fmt="-",
    )
    ax_2.scatter(x=actions_ordered[1], y=actions_ordered[0], color = 'black')
    ax_2.legend(["Positive", "Negative","Actions"])
    fig_2=ax_2.get_figure()
    temp_fig_2= BytesIO()
    fig_2.savefig(temp_fig_2, format="png")
    st.image(temp_fig_2)

    for lc,mr in capacity_moments.items():
        st.write(f"The Bending Capacity is equal to {mr.round(1)} kNm")
        st.write(f"The utilization level is equal to {abs((actions_dict[lc][1]/mr).round(3))} ")


with tab3:
    fig_3 = Figure()
    ax_3 = fig_3.gca()
    ax_3 = cracked_stress_res.plot_stress()
    fig_3=ax_3.get_figure()
    temp_fig_3= BytesIO()
    fig_3.savefig(temp_fig_3, format="png")
    st.image(temp_fig_3)
    st.write(f"Depth of neutral axis is equal to {cracked_res.d_nc:.2f} mm")

with tab4:

    option = st.selectbox(
    'Moment-curvature calculation?',
    ('NO', 'YES'))
    if option == "YES":
        #print Moment curvature
        m_c_0 = conc_section.moment_curvature_analysis(theta=0, n=actions[0]*1e3)
        m_c_180 = conc_section.moment_curvature_analysis(theta=np.pi, n=actions[0]*1e3)

        fig_4 = Figure()
        ax_4 = fig_4.gca()
        ax_4 = MomentCurvatureResults.plot_multiple_results(
        moment_curvature_results=[m_c_0, m_c_180],
        labels=["Positive", "Negative"],
        fmt="-",
        )
        fig_4=ax_4.get_figure()
        temp_fig_4= BytesIO()
        fig_4.savefig(temp_fig_4, format="png")
        st.image(temp_fig_4)