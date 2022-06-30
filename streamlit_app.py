import streamlit as st
import networkx as nx
import pandas as pd
import streamlit.components.v1 as components
from utilities import *
from pyvis.network import Network
import re

abs_regex = re.compile('.*abstract.*', re.IGNORECASE)
summary_regex = re.compile('.*summary.*', re.IGNORECASE)
desc_regex = re.compile('.*description.*', re.IGNORECASE)

patterns = [abs_regex, summary_regex, desc_regex]

attributes = ['name', 'id', 'class']
global dois_frame 

BG = nx.Graph()

dois = []

global draw_network
draw_network = False


st.title("Citation Network Builder", anchor=None)

doi_control_container = st.sidebar.container()
with doi_control_container:

    uploaded_file =st.file_uploader("Upload DOIs")
    if uploaded_file is not None:
        dois_frame = parse_st_upload(uploaded_file)
        dois_frame.columns=['DOI']  
        dataframe_display = st.dataframe(dois_frame)

        build_network = st.button("Create Citation Network")
        backwards_expansion_steps = st.slider("Citation Expansion Steps", 0, 4, 0, 1)
        if build_network:
            with st.spinner(text="Building Network"):
                BG = create_network(list(dois_frame['DOI']), 0)
                
                st.success("Network Built!")
                        
                Graph_Display = Network(notebook=True, height="720px", width="100%")
                #Graph_Display.barnes_hut()
                st.write("Getting Metadata")
                BG = set_node_sizes(BG)
                BG = add_node_metadata(BG)
                st.write("Detecting Commmunities")
                communities = nx.algorithms.community.modularity_max.greedy_modularity_communities(BG)
                BG = set_node_community(BG, communities)
                Graph_Display.from_nx(BG)
                Graph_Display.show("ex.html")
                draw_network = True

if draw_network:            
    HtmlFile = open("ex.html", 'r', encoding='utf-8')
    source_code = HtmlFile.read() 
    components.html(source_code, height = 720)
    accordion = st.expander("Network Details", expanded=False)    
    with accordion:
        st.download_button("Download Graph", "\n".join(nx.generate_gml(BG)), file_name="graph.gml")