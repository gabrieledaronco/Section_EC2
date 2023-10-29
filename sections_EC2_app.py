import streamlit as st
import plotly.graph_objects as go
from matplotlib.figure import Figure
import sections_EC2_module as sm
from io import BytesIO
import numpy as np
## Import analysis section
from concreteproperties.concrete_section import ConcreteSection
from math import pi


st.header("Reinforced Concrete Sections")
st.subheader("Rectangular sections")

col1, col2 =st.columns(2)
tab1, tab2, tab3 = st.tabs(["Geometry","M-N Results", "Cracking"])

st.sidebar.subheader("Concrete")
concrete = st.sidebar.text_input("Concrete grade", value="C25/30")
c_fc = st.sidebar.number_input("fc [MPa]", value=25)
c_fct = st.sidebar.number_input("fct [MPa]", value=2)
c_E = st.sidebar.number_input("fct [MPa]", value=24000)

st.sidebar.subheader("Steel Rebar")
concrete = st.sidebar.text_input("Steel grade",value = "500B")
s_fy = st.sidebar.number_input("fc [MPa]", value=500)

concrete = sm.create_concrete(fc=c_fc,fc_t=c_fct,E=c_E)
steel_rebar=sm.create_steelbar(fy=s_fy,gamma_r=1.15)

st.sidebar.subheader("Section Geometry")
type = st.sidebar.text_input("Section Type", value="Rectangular")
s_h = st.sidebar.number_input("height [mm]", value=900)
s_b = st.sidebar.number_input("width [mm]", value=600)

st.sidebar.subheader("Reinforcement Bars")
t_diameter= st.sidebar.number_input("Top diameter [mm]")
t_nr_bars= st.sidebar.number_input("Top number of bars", format="%i" )
b_diameter= st.sidebar.number_input("Bottom diameter [mm]")
b_nr_bars= st.sidebar.number_input("Bottom number of bars", format="%i")
l_diameter= st.sidebar.number_input("Left diameter [mm]")
l_nr_bars= st.sidebar.number_input("Left number of bars", format="%i" )
r_diameter= st.sidebar.number_input("Right diameter [mm]")
r_nr_bars= st.sidebar.number_input("Right number of bars", format="%i" )
cover = st.sidebar.number_input("Cover [mm]")

st.sidebar.subheader("Acions")
n_action= st.sidebar.number_input("ULS Axial_force [kN]")
m_action= st.sidebar.number_input("ULS Bending Moment [kNm]")
sls_n_action= st.sidebar.number_input("SLS Axial_force [kN]")
sls_m_action= st.sidebar.number_input("SLS Bending Moment [kNm]")



#Define concrete geometry
conc_geom = sm.def_geom(height=s_h,width=s_b, mat=concrete)

bars_list = sm.rect_bar_list(top_diameter=t_diameter,
                             top_nr_bars=int(t_nr_bars),
                             bottom_diameter=b_diameter,
                             bottom_nr_bars=int(b_nr_bars),
                             left_diameter=l_diameter,
                             left_nr_bars=int(l_nr_bars),
                             right_diameter=r_diameter,
                             right_nr_bars=int(r_nr_bars),
                             height=s_h,
                             width=s_b,
                             cover=cover
                             )

conc_geom = sm.add_bars(bars_list=bars_list,conc_geom=conc_geom,mat=steel_rebar)
#Define concrete section
conc_section = ConcreteSection(conc_geom)




#Actions
actions_dict = {"L1":(n_action,m_action),}
actions=list(actions_dict.values())
actions_ordered=list(zip(*actions))

#Caclutate Mr for each N (CREARE TABELLA PER METTERE I VALORI)
capacity_moments={}
for name,actions in actions_dict.items():
    mr = conc_section.ultimate_bending_capacity(theta=0, n= actions[0]*1e3)
    capacity_moments.update({name:mr.m_xy/1e6})

#Calculate Cracked Section
cracked_res = conc_section.calculate_cracked_properties(theta=0)
cracked_stress_res = conc_section.calculate_cracked_stress(
    cracked_results=cracked_res,n= sls_n_action, m=sls_m_action
)

#print N-M curve with actions
m_n=conc_section.moment_interaction_diagram(theta=0)
m_n_list=m_n.get_results_lists("m_xy")
# m_n_180=conc_section.moment_interaction_diagram(theta=pi)
# m_n_0_list=m_n_0.get_results_lists("m_xy")
# m_n_180_list=m_n_180.get_results_lists("m_xy")
# m_n_list_n = m_n_0_list[0]+ m_n_180_list[0]
# m_n_list_m = m_n_0_list[1]+ m_n_180_list[1]
# m_n_list= (m_n_list_n,m_n_list_m)
m_n_array =np.array(m_n_list)

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
    fig = go.Figure()
    fig.add_trace(go.Scatter(name= "Section Capacity",y=m_n_array[1]/1e6, x=m_n_array[0]/1e3))
    fig.add_trace(go.Scatter(name= "External action",x=actions_ordered[0], y=actions_ordered[1], mode="markers"))
    fig.layout.width = 800
    fig.layout.height = 800
    fig.layout.xaxis.title = "Axial Force (kN)"
    fig.layout.yaxis.title = "Bending Moment (kNm)"
    fig
    for lc,mr in capacity_moments.items():
        st.write(f"The Bending Capacity is equal to {mr.round(1)} kNm")

with tab3:
    fig_2 = Figure()
    ax_2 = fig_2.gca()
    ax_2 = cracked_stress_res.plot_stress()

    fig_2=ax_2.get_figure()

    temp_fig_2= BytesIO()
    fig_2.savefig(temp_fig_2, format="png")
    st.image(temp_fig_2)
  
    st.write(f"Depth of neutral axis is equal to {cracked_res.d_nc:.2f} mm")
