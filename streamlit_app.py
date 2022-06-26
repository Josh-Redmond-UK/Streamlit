import streamlit as st
import networkx as nx
import pandas as pd
from utitlies import *
import re

abs_regex = re.compile('.*abstract.*', re.IGNORECASE)
summary_regex = re.compile('.*summary.*', re.IGNORECASE)
desc_regex = re.compile('.*description.*', re.IGNORECASE)

patterns = [abs_regex, summary_regex, desc_regex]

attributes = ['name', 'id', 'class']


dois = ['10.5589/cjrsyearend34',
        '10.2991/rsete.2013.114',
        '10.1177/2053951720949566',
        '10.1093/acprof:oso/9780190239480.001.0001',
        '10.1016/S0959-8022(00)00004-7',
        '10.1145/3384772.3385155',
        '10.3390/rs13030439']


dois_frame = pd.DataFrame(dois).T


st.dataframe(dois_frame)