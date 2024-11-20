import random
import math
import pandas as pd
import folium
import numpy as np
import geopandas 
import requests
import branca
from PIL import Image
import base64

import streamlit as st

from folium.plugins import HeatMap
from shapely.wkt import loads
from folium.plugins import MarkerCluster
from folium import plugins

from folium.plugins import BeautifyIcon
from folium.plugins import MousePosition
from folium.plugins import HeatMap
from streamlit.components.v1 import html
from folium import LinearColormap

import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
import geopandas as gpd
from branca.colormap import linear
from shapely.geometry import Point
from scipy.stats import boxcox
import pandas as pd 
import geopandas as gpd
import numpy as np
import pickle
from shapely import wkt

import folium
from folium.plugins import MarkerCluster
from folium.plugins import BeautifyIcon

import time
import warnings
warnings.filterwarnings("ignore")

county_list = [
    "Mills", "Harris", "Jefferson", "Aransas", "Nueces", "Galveston", "Travis", 
    "Fort Bend", "Dallas", "Brazoria", "Brazos", "Howard", "Bexar", "Caldwell", 
    "Orange", "Jasper", "Hardin", "Calhoun", "Wharton", "Crosby", "Montgomery", 
    "Bastrop", "Roberts", "Taylor", "Washington", "Comal", "Victoria", "McLennan", 
    "Liberty", "Midland", "Tarrant", "Henderson", "Wilson"
]

#if "selected_county" not in st.session_state:
#    st.session_state.selected_county = ["Brazos"]

def convert_list_to_gdf(list_of_tuples):
        df = gpd.GeoDataFrame([['POINT ' +str(i).replace(',', ' ')]  for i in list_of_tuples], columns=['geometry'])
        df['geometry'] = df.apply(lambda x: wkt.loads(x['geometry']), axis=1)
        df = df.set_geometry("geometry")
        df.crs = "EPSG:4326"
        return df

@st.cache_data
def get_feature_data():
    tower_data_file = 'hurricane/tower_data.csv'
    amenities_file_name = 'hurricane/amenities.csv'
    
    #tower_df = pd.read_csv(tower_data_file)
    tower_df = 1
    amenities_df = pd.read_csv(amenities_file_name, index_col=0)

    restaurant_df = amenities_df[amenities_df['amenity_type']=='Restaurant']
    restaurants = convert_list_to_gdf(restaurant_df['coordinates'])
    restaurants['county'] = restaurant_df['county'].to_list()

    hospital_df = amenities_df[amenities_df['amenity_type']=='Hospital']
    hospitals = convert_list_to_gdf(hospital_df['coordinates'].to_list())
    hospitals['county'] = hospital_df['county'].to_list()

    fire_stations_df = amenities_df[amenities_df['amenity_type']=='Fire_station']
    fire_stations = convert_list_to_gdf(fire_stations_df['coordinates'].to_list())
    fire_stations['county'] = fire_stations_df['county'].to_list()

    parkings_df = amenities_df[amenities_df['amenity_type']=='Parking']
    parkings = convert_list_to_gdf(parkings_df['coordinates'].to_list())
    parkings['county'] = parkings_df['county'].to_list()

    return restaurants, hospitals, fire_stations, parkings, tower_df #tower_coordinates

@st.cache_data
def get_gdf_data():
    # Set filepath
    # fp = "./data/filtered_gdf_v2.csv"
    fp = "hurricane/census_data.csv"
    # Read file using gpd.read_file()
    gdf_read = gpd.read_file(fp, 
                        GEOM_POSSIBLE_NAMES="geometry", 
                        KEEP_GEOM_COLUMNS="NO") 

    
    gdf_read['GEOID_12'] = gdf_read['GEOID_12'].apply(lambda x:int(x))
    gdf_read['TotPop'] = gdf_read['TotPop'].apply(lambda x:int(x))
    gdf_read['D1B'] = gdf_read['D1B'].apply(lambda x:float(x))
    gdf_read['NatWalkInd'] = gdf_read['NatWalkInd'].apply(lambda x:float(x))
    gdf_read['STATEFP_x'] = gdf_read['STATEFP_x'].astype('int64')
    gdf_read['COUNTYFP_x'] = gdf_read['COUNTYFP_x'].astype('int64')
    gdf_read['TRACTCE_x'] = gdf_read['TRACTCE_x'].astype('int64')
    gdf_read['BLKGRPCE_x'] = gdf_read['BLKGRPCE_x'].astype('int64')
   

    gdf = gpd.GeoDataFrame(gdf_read[['STATEFP_x', 'COUNTYFP_x', 'TRACTCE_x', 'BLKGRPCE_x',  'GEOID', 'geometry', 'TotPop', 'D1B', 'NatWalkInd','GEOID_12', 'county']])
    gdf.crs = "EPSG:4326"
    # Set 'power' to 0 for specified 'TRACTCE_x' values
    specified_tracts = [1400, 1303, 1601, 1000, 1701, 1900]
    gdf.loc[gdf['TRACTCE_x'].isin(specified_tracts), 'power'] = 1

    walk_ind_dict = gdf.set_index("GEOID")["NatWalkInd"]
    gross_pop_density_dict = gdf.set_index("GEOID")["D1B"]
    tot_pop_dict = gdf.set_index("GEOID")["TotPop"]



    return walk_ind_dict, gross_pop_density_dict, tot_pop_dict, gdf

@st.cache_data
def get_tower_coordinates(tower_df, county):
    # Collect Tower Data
    print(county)
    # import pdb 
    # pdb.set_trace()
    tower_coordinates = np.array(tower_df[tower_df['county'].isin(county)].apply(lambda x: (x['Longitude'], x['Latitude']), axis=1))
    tower_coordinates = convert_list_to_gdf(tower_coordinates)
    
    return tower_coordinates

# @st.cache_data
# def get_tower_locations(_tower_coordinates):
#     # Sample 100 locations and return them
#     return [(x.y, x.x) for x in _tower_coordinates['geometry'].sample(50)]

# Setting the page configuration for a better look
st.set_page_config(
    page_title="Disaster Impact Dashboard",
    page_icon="🌍",
    layout="wide",
)

st.markdown("""
        <style>
               .main .block-container {
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)

# Sidebar for disaster type selection
st.sidebar.title("📍 Real-Time Disaster Impact Dashboard")

# Function to set background image for sidebar
def sidebar_bg(side_bg):

   side_bg_ext = 'jpg'

   st.markdown(
      f"""
      <style>
      [data-testid="stSidebar"] > div:first-child {{
          background: url(data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()});
      }}
      </style>
      """,
      unsafe_allow_html=True,
      )
side_bg = 'images/bg9.jpg'
# sidebar_bg(side_bg)
  

def set_bg_hack_url(side_bg):
    side_bg_ext = 'jpg'  # Make sure this matches your image's format

    # Added CSS for background size, position, and overlay
    st.markdown(
        f"""
        <style>
        .stApp  {{
           background: url(data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()});
       }}
        .stApp::before {{
            content: '';
            display: block;
            position: absolute;
            top: 0; right: 0; bottom: 0; left: 0;
            background: rgba(255, 255, 255, 0.5);  # Adjust color and opacity for overlay
            z-index: -1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


set_bg_hack_url('images/bg11.jpg')
st.markdown("---")

sidebar = st.sidebar
st.sidebar.markdown("### Select a County")
    #selected_county = st.sidebar.selectbox("County", county_list, index=0)
dropbox = sidebar.container()
selected_county = dropbox.multiselect(
   "Select a county",
    county_list,
    default='Brazos',
#    index=None,
   placeholder="Brazos",
)

restaurants, hospitals, fire_stations, parkings, tower_df = get_feature_data()
restaurants  = restaurants[restaurants['county'].isin(selected_county)]
hospitals  = hospitals[hospitals['county'].isin(selected_county)]
fire_stations  = fire_stations[fire_stations['county'].isin(selected_county)]
parkings  = parkings[parkings['county'].isin(selected_county)]
#tower_coordinates = get_tower_coordinates(tower_df, selected_county)

    #tower_coordinates = get_tower_coordinates(tower_df)
walk_ind_dict, gross_pop_density_dict, tot_pop_dict, gdf = get_gdf_data()
gdf = gdf[gdf['county'].isin(selected_county)]

filtered_data = pd.read_csv("hurricane/disaster_data.csv")


# Create a Folium map centered around a sample location
map_center = [filtered_data["lat"].mean(), filtered_data["lon"].mean()+10]
m = folium.Map(location=map_center, zoom_start=5, prefer_canvas=True, tiles=None)

folium.raster_layers.TileLayer(tiles="openstreetmap", name='Open Street Map').add_to(m)
folium.raster_layers.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", 
                               attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community', 
                               name='Satellite View',
                                opacity=0.95,
                               ).add_to(m)


    # FEATURE 1 - Walkability Index
colormap_walkind = linear.YlGn_09.scale(
        gdf.NatWalkInd.min(), gdf.NatWalkInd.max()
    )
    
    # Add walkability data for the selected county to the map
folium.GeoJson(
        gdf,
        name=f'<span style="color:#34568B">FEATURE - Walkability</span>',
        style_function=lambda feature: {
            "fillColor": colormap_walkind(walk_ind_dict[feature["properties"]["GEOID"]]),
            "color": "black",
            "weight": 1,
            "dashArray": "5, 5",
            "fillOpacity": 0.5,
        },
        show=False,  # Automatically show the layer for the selected county
    ).add_to(m)

    # FEATURE 2- Total Population
    #colormap_totpop = branca.colormap.LinearColormap(colors=['white', 'yellow', 'orange', 'red'],
    #                                      index = np.round(np.linspace(gdf.TotPop.min(), gdf.TotPop.max()/5, 4)),
    #                                      vmin = gdf.TotPop.min(), vmax = gdf.TotPop.max(), tick_labels = np.round(np.exp(np.linspace(gdf.TotPop.min(), gdf.TotPop.max(), 4)),1)
    #       )

colormap_totpop = linear.YlOrRd_09.scale(
        gdf.TotPop.min(), gdf.TotPop.max()
    )

folium.GeoJson(
        gdf,
    name='<span style="color:#34568B">FEATURE - Total Population</span>',
    style_function=lambda feature: {
        "fillColor": colormap_totpop(tot_pop_dict[feature["properties"]["GEOID"]]),
        "color": "black",
        "weight": 1,
        "dashArray": "5, 5",
        "fillOpacity": 0.5,
        }, 
        show = False
    ).add_to(m)

# # FEATURE 3- Tower Locations
# towerCluster = MarkerCluster(name='<span style="color:#34568B">FEATURE - Cell Towers</span>', show=False).add_to(m)
# tower_locations = [(x.y, x.x) for x in  tower_coordinates['geometry'].sample(100)]
# for coordinates in tower_locations:
#     folium.Marker(location = coordinates,
#                     icon=BeautifyIcon(icon="phone", 
#                                       icon_size=(30,30),
#                                      inner_icon_style="font-size:15px;padding-top:1px;",
#     #                     #   border_color=color, 
#     #                     #     text_color=color, 
#                             icon_shape="circle")
#                     ).add_to(towerCluster)

# FEATURE 4- Restaurants
restaurant_locations = [(x.y, x.x) for x in  restaurants['geometry']]
restaurantCluster = MarkerCluster(name='<span style="color:#34568B">FEATURE - Restaurants</span>', show=False).add_to(m)
for coordinates in restaurant_locations:
    folium.Marker(location = coordinates,
                    icon=BeautifyIcon(icon="cutlery", 
                    border_color="orange", 
                    icon_size=(30,30),
                    inner_icon_style="font-size:15px;padding-top:1px;",
    #               text_color=color, 
                            icon_shape="circle")
                    ).add_to(restaurantCluster)

# FEATURE 5- Parking
parking_locations = [(x.y, x.x) for x in  parkings['geometry']]
parkingCluster = MarkerCluster(name='<span style="color:#34568B">FEATURE - Parking</span>', show=False).add_to(m)
for coordinates in parking_locations:
    folium.Marker(location = coordinates,
                    icon=BeautifyIcon(icon="car", 
                    border_color="blue", 
                    icon_size=(30,30),
                    inner_icon_style="font-size:15px;padding-top:1px;",
                  text_color="black", 
                            icon_shape="circle")
                    ).add_to(parkingCluster)

# FEATURE 6- Fire Stations
fire_station_locations = [(x.y, x.x) for x in  fire_stations['geometry']]
fire_station_Cluster = MarkerCluster(name='<span style="color:#34568B">FEATURE - Fire Stations</span>', show=False).add_to(m)
for coordinates in fire_station_locations:
    folium.Marker(location = coordinates,
                    icon=BeautifyIcon(icon="fire-extinguisher", 
                    border_color="red", 
                    icon_size=(30,30),
                    inner_icon_style="font-size:15px;padding-top:1px;",
    #               text_color=color, 
                            icon_shape="circle")
                    ).add_to(fire_station_Cluster)

# FEATURE 7- Hospitals  
hospital_locations = [(x.y, x.x) for x in  hospitals['geometry']]
hospital_Cluster = MarkerCluster(name='<span style="color:#34568B">FEATURE - Hospitals</span>', show=False).add_to(m)
for coordinates in hospital_locations:
    folium.Marker(location = coordinates,
                    icon=BeautifyIcon(icon="medkit", 
                    border_color="green", 
                    icon_size=(30,30),
                    text_size = (10,10),
                    inner_icon_style="font-size:15px;padding-top:1px;",
    #               text_color=color, 
                            icon_shape="circle")
                    ).add_to(hospital_Cluster)


disaster_type = 'Hurricane'
# Add markers to map with clustering and tooltips
marker_cluster = MarkerCluster(name='<span style="color:green">Location Points</span>', overlay=True,
    control=True,
    show=True ).add_to(m)
for idx, row in filtered_data.iterrows():
    tooltip_text = (
        f"<b>Tweet:</b> {row['text']}<br>"
        f"<b>Location:</b> {row['location_text']}<br>"
        f"<b>Type:</b> {row['location_type']}<br>"
        f"<b>humAID:</b> {row['humAID_class']}<br>"
        #f"<b>latitude:</b> {row['lat']}<br>"
        #f"<b>longitude:</b> {row['lon']}<br>"
        f"<b>Full Location:</b> {row['display_name']}"
    )
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"{disaster_type} at ({row['lat']}, {row['lon']})",
        tooltip=tooltip_text,
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(marker_cluster)

locations = filtered_data[['lat', 'lon']].values
HeatMap(locations, name= '<span style="color:green">Heatmap</span>',show= False).add_to(m)

# Add Layer controls to map
folium.LayerControl().add_to(m)
folium.map.LayerControl('topleft', collapsed= False).add_to(m)
# Add Full screen option
Fullscreen(position="topleft").add_to(m)

# Display Folium map in Streamlit app
#st.markdown("### Impacted Areas Map")
st_data = st_folium(m, height=600,width=2600)

# Add an information section
st.sidebar.markdown("### Insights")
st.sidebar.markdown(f"#### Total Impacted Locations: **{len(filtered_data)}**")

# Footer
#st.markdown("---")
