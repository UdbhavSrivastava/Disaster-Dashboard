import pandas as pd
import folium
import streamlit as st
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
import base64

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
st.sidebar.markdown("### Select a Disaster Type")
disaster_type = st.sidebar.selectbox(
    "Disaster Type",
    (
        "Ecuador_earthquake", "Cyclone_idai", "Greece_wildfire", "Hurricane_dorian",
        "Hurricane_florence", "Hurricane_harvey", "Hurricane_irma", "Hurricane_maria",
        "Hurricane_matthew", "Italy_earthquake", "Kaikoura_earthquake", "Kerala_flood",
        "Maryland_flood", "Midwestern_us_flood", "Pakistan_earthquake", "Mexico_earthquake",
        "SriLanka_flood", "California_wildfire", "Canada_wildfire"
    )
)
st.sidebar.write("Use the dropdown above to select the type of disaster to view affected areas.")


# Title and subtitle
#st.title("📍 Real-Time Disaster Impact Visualization")
#st.markdown(
#    """
#    This interactive dashboard displays real-time data of various disaster impacts across locations.
#    Select a disaster type from the sidebar to explore affected areas and see aggregated information on the map.
#    """
#)

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
# Load your data
@st.cache_data
def load_data():
    data = pd.read_csv("disaster_data.csv")
    return data

data = load_data()

# Filter data based on selected disaster type
filtered_data = data[data["disaster_type"] == disaster_type]



# Create a Folium map centered around a sample location
map_center = [filtered_data["lat"].mean(), filtered_data["lon"].mean()+10]
m = folium.Map(location=map_center, zoom_start=5, prefer_canvas=True, tiles=None)

folium.raster_layers.TileLayer(tiles="openstreetmap", name='Open Street Map').add_to(m)
folium.raster_layers.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", 
                               attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community', 
                               name='Satellite View',
                                opacity=0.95,
                               ).add_to(m)

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
st.sidebar.markdown(f"#### Selected Disaster Type: **{disaster_type}**")
st.sidebar.markdown(f"#### Total Impacted Locations: **{len(filtered_data)}**")

# Footer
#st.markdown("---")
