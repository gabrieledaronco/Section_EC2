import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import sections_EC2_module as sm

col1, col2 =st.columns(2)
with col1:
    st.header("Reinforced Concrete Sections")
    st.subheader("Rectangular sections")

with col2:
    st. write("Hola")

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
s_h = st.sidebar.number_input("height [mm]", value=900)
s_b = st.sidebar.number_input("width [mm]", value=600)

conc_geom = sm.def_geom(height=s_h,width=s_b, mat=concrete)

bars = [
[500.000000,-250,384.824982],
[500.000000,250,384.824982],
[500.000000,-250,-384.824982],
[500.000000,250,-384.824982],
[500.000000,-250,230.894989],
[500.000000,-250,76.964996],
[500.000000,-250,-76.964996],
[500.000000,-250,-230.894989],
[500.000000,250,230.894989],
[500.000000,250,76.964996],
[500.000000,250,-76.964996],
[500.000000,250,-230.894989],
[500.000000,0,384.824982],
[500.000000,0,-384.824982],
]

reinf_geom = sm.add_bars(bars_list=bars,conc_geom=conc_geom,mat=steel_rebar)


