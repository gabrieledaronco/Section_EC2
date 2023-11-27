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
    side_tab1, side_tab2, side_tab3 ,side_tab4= st.tabs(["Materials","Geometry", "ULS Actions", "SLS Actions"])
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

        columns_actions = ["Load Case","N [kN]", "M [kNm]", "V [kN]" ]
        rows_actions = [["LC1",-100,1500,300]]
        uls_act_df = pd.DataFrame(data=rows_actions, columns=columns_actions)
        edited_uls_act_df= st.data_editor(uls_act_df, num_rows="dynamic")
              

    with side_tab4:
        st.caption("Compression is positive")
        st.caption("Positive moment produces tension on lower side")
        columns_sls = ["Load Case","N [kN]", "M [kNm]" ]
        rows_sls = [["LC1",-100,500]]
        sls_act_df = pd.DataFrame(data=rows_sls, columns=columns_sls)
        edited_sls_df= st.data_editor(sls_act_df.set_index("Load Case"))


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
n_actions = list(edited_uls_act_df["N [kN]"])
m_actions = list(edited_uls_act_df["M [kNm]"])
lc_actions = list(edited_uls_act_df["Load Case"])


#Caclutate Mr for each N 
capacity_list=[]
for i  in range(len(lc_actions)):
    if m_actions[i]>0:
        mr = conc_section.ultimate_bending_capacity(theta=0, n= n_actions[i]*1e3)
    else:
        mr = conc_section.ultimate_bending_capacity(theta=np.pi, n= n_actions[i]*1e3)
    capacity_list.append([lc_actions[i], 
                          n_actions[i], 
                          m_actions[i],
                          (mr.m_xy/1e6).round(1), 
                          abs(m_actions[i]/(mr.m_xy/1e6)).round(3)])


#Calculate Cracked Section
if edited_sls_df.iloc[0][1] >0:
    cracked_res = conc_section.calculate_cracked_properties(theta=0)
else:
    cracked_res = conc_section.calculate_cracked_properties(theta=np.pi)
cracked_stress_res = conc_section.calculate_cracked_stress(
    cracked_results=cracked_res,
    n= edited_sls_df.iloc[0][0]*1e3, 
    m=edited_sls_df.iloc[0][1]*1e6
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
  
    fig = Figure()
    ax = fig.gca()
    ax = MomentInteractionResults.plot_multiple_diagrams(
    moment_interaction_results=[m_n_0, m_n_180],
    labels=["Positive", "Negative"],
    fmt="-",
    )
    legend_list = ["Positive", "Negative"] + lc_actions
    for i in range(len(m_actions)):
        ax.scatter(x=m_actions[i], y=n_actions[i])
    for element in legend_list:
        ax.legend(legend_list)


    fig=ax.get_figure()
    temp_fig= BytesIO()
    fig.savefig(temp_fig, format="png")
    st.image(temp_fig)

    columns_capacity = ["Load Case","Ned [kN]", "Med [kNm]", "Mrd [kN]", "Utilization Level"]
    capacity_df = pd.DataFrame(data=capacity_list, columns=columns_capacity)
    # capacity_df = capacity_df.set_index("Load Case")
    printed_capacity_df= st.dataframe(capacity_df,use_container_width=True)


with tab3:
    fig = Figure()
    ax = fig.gca()
    ax = cracked_stress_res.plot_stress()
    fig=ax.get_figure()
    temp_fig= BytesIO()
    fig.savefig(temp_fig, format="png")
    st.image(temp_fig)

    cracked_df = sm.get_stress_df(cracked_stress_res)
    edited_cracked_df = st.dataframe(cracked_df,use_container_width=True)

    st.write(f"Depth of neutral axis is equal to {cracked_res.d_nc:.2f} mm")






with tab4:

    option = st.selectbox(
    'Moment-curvature calculation?',
    ('NO', 'YES'))
    if option == "YES":
        n_action= st.number_input("ULS Axial force [kN]",value=200.0)
        #print Moment curvature
        m_c_0 = conc_section.moment_curvature_analysis(theta=0, n=n_action*1e3)
        m_c_180 = conc_section.moment_curvature_analysis(theta=np.pi, n=n_action[0]*1e3)

        fig = Figure()
        ax = fig.gca()
        ax = MomentCurvatureResults.plot_multiple_results(
        moment_curvature_results=[m_c_0, m_c_180],
        labels=["Positive", "Negative"],
        fmt="-",
        )
        fig=ax.get_figure()
        temp_fig= BytesIO()
        fig.savefig(temp_fig, format="png")
        st.image(temp_fig)