import xml.etree.ElementTree as ET
from urllib.error import HTTPError
from habanero import Crossref
import time
import json
from habanero import cn
import requests
from bs4 import BeautifulSoup
import re
from io import StringIO
import pandas as pd
import streamlit as st
cr = Crossref()
import networkx as nx

def start_negotiation(doi):
  try: 
    result = cn.content_negotiation(ids = doi, format = "citeproc-json")
  except Exception as e:
    err = e
    print(e)
    code = e.args[0][0:3]
    if code == "404":
      raise err
    if code == "406":
      raise err
    else:
      print("Lookup for DOI:", doi, "Failed with code:", code, "retrying")
      time.sleep(2)
      result = start_negotiation(doi)

  return(result)

def get_titles_and_abstracts(dois, regexs, attributes):

  headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
  }

  names_and_abstracts = {}


  # Iterate through the list of DOIs given and fetch the abstract and title for each
  for doi in dois:
    # Use crossref's content negotiation to retrieve metadata
    try: 
      metadata = start_negotiation(doi)
      json_metadata = json.loads(metadata)
    except: json_metadata = None

    # If the metadata is contained in that metadata, that's fine
    try:
      name = json_metadata['title']
    except:
      name = None
    
    # Same with the abstract
    try:
      abstract = json_metadata['abstract']
    except:
      # In the event that there is no abstract, find the URL for the paper, go to the page
      # and try to find anything in the HTML called "abstract", if that exists, copy it
      try:
        url = json_metadata['URL']
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')

        results = []

        for pattern in regexs:
          for attribute in attributes:
            found = soup.findAll(attrs = {attribute : pattern})
            results.append(found)


        if len(results) == 0:
          abstract = None
        else:
          abstract = results#.prettify()
      except:
        abstract = None

        
    # Return as dictionary with DOI as key, and a tuple of name and abstract as values
    names_and_abstracts[doi] = (name, abstract)
  
  return names_and_abstracts


def get_outgoing_citations(doi, return_dict=True):
  try: 
    testtdm = start_negotiation(doi)
    json_metadata = json.loads(testtdm)
  except: json_metadata = None

   
  
  try:
    l = len(json_metadata['reference'])
    if l > 0:
      refs_included = True
  except:
    refs_included = False

  if refs_included == True:
    citations = [] 
    for idx in range(len(json_metadata['reference'])):
      
      try: 
        cit = json_metadata['reference'][idx]['DOI']
        citations.append(cit)
      except: pass #cit = json_metadata['reference'][idx]['key']


    if len(citations) == 0:
      citations = None

  else: citations = None





  edges_dict = {doi: citations}
  if return_dict:
    return edges_dict
  else:
    return doi, citations


def nodes_to_graph(node_dict):
  G = nx.Graph()
  for ego_network in node_dict:
    ego = list(ego_network.keys())[0]
    neighbours = list(ego_network.values())[0]

    try:
      for neighbour in neighbours:
        G.add_edge(ego, neighbour)
    except: continue

  return G

def create_network(dois, steps):
  nodes = []
  already_queried = []
  for doi in dois:
    #st.write(f"querying {doi}")
    nodes.append(get_outgoing_citations(doi))
    already_queried.append(doi)


  bibliograph = nodes_to_graph(nodes)
  #st.write(f"Starting network size {len(list(bibliograph.nodes))}")
  for s in range(steps):

    for node in list(bibliograph.nodes):
      if node in already_queried:
        continue
      else:
        neighbours = list(get_outgoing_citations(node).values())[0]
        #print(neighbours)
        if type(neighbours) == type(None):
          continue
        for neigh in neighbours:
          #print(neigh)
          if neigh not in list(bibliograph.nodes):
            bibliograph.add_node(neigh)
          bibliograph.add_edge(node, neigh)
    #st.write(f"Step {s} completed.")
    print("Network size", len(list(bibliograph.nodes)), "nodes")
  return bibliograph


def parse_st_upload(upload):

    # Can be used wherever a "file-like" object is accepted:
    dataframe = pd.read_csv(upload)
    return dataframe

def set_node_community(G, communities):
    '''Add community to node attributes'''
    for c, v_c in enumerate(communities):
        for v in v_c:
            # Add 1 to save 0 for external edges
            G.nodes[v]['community'] = c + 1


def get_network_communities(G):
  communities = nx.algorithms.community.modularity_max.greedy_modularity_communities(G)
  set_node_community(G, communities)
  return G

def set_node_sizes(G):
  degrees = G.degree
  nodes = list(G.nodes)

  for n in nodes:
    G.nodes[n]['size'] = degrees[n]

  return G




def add_node_metadata(G):
  abs_regex = re.compile('.*abstract.*', re.IGNORECASE)
  summary_regex = re.compile('.*summary.*', re.IGNORECASE)
  desc_regex = re.compile('.*description.*', re.IGNORECASE)

  patterns = [abs_regex, summary_regex, desc_regex]
  attributes = ['name', 'id', 'class']
  title_abs = get_titles_and_abstracts(list(G.nodes), patterns, attributes)

  for n in G.nodes:
    G.nodes[n]['label'] = title_abs[n][0]
    G.nodes[n]['title'] = generate_panel_html(title_abs[n][0], "TestAuthor", title_abs[n][1], n)
    
  return G

def generate_panel_html(title=None, authors=None, abstract=None, doi=None):



  html_string = f'<p><strong>Title: {title}<br /></strong><strong>Authors: {authors}<br /></strong><strong>DOI: <a href="http://www.google.com">{doi}</a></strong></p>'
  return html_string

def set_node_community(G, communities):
  '''Add community to node attributes'''
  for c, v_c in enumerate(communities):
      for v in v_c:
          # Add 1 to save 0 for external edges
          G.nodes[v]['group'] = c + 1

  return G
