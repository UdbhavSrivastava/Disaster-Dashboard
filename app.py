import pandas as pd
import geopandas as gpd
import folium
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap


# Setting the page configuration for a better look
st.set_page_config(
    page_title="Disaster Impact Dashboard",
    page_icon="🌍",
    layout="wide",
)

# Sidebar for disaster type selection
st.sidebar.title("Disaster Impact Dashboard")
st.sidebar.markdown("### Select a Disaster Type")
disaster_type = st.sidebar.selectbox(
    "Disaster Type",
    ("Ecuador_earthquake",
    "Cyclone_idai",
    "Greece_wildfire",
    "Hurricane_dorian",
    "Hurricane_florence",
    "Hurricane_harvey",
    "Hurricane_irma",
    "Hurricane_maria",
    "Hurricane_matthew",
    "Italy_earthquake",
    "Kaikoura_earthquake",
    "Kerala_flood",
    "Maryland_flood",
    "Midwestern_us_flood",
    "Pakistan_earthquake",
    "Mexico_earthquake",
    "SriLanka_flood",
    "California_wildfire",
    "Canada_wildfire")
)

st.sidebar.write("Use the dropdown above to select the type of disaster to view affected areas.")

# Title and subtitle
st.title("📍 Real-Time Disaster Impact Visualization")
st.markdown(
    """
    This interactive dashboard displays real-time data of various disaster impacts across locations.
    Select a disaster type from the sidebar to explore affected areas and see aggregated information on the map.
    """
)

# Load your data
@st.cache_data
def load_data():
    data = pd.read_csv("disaster_data.csv")
    return data

data = load_data()

# Filter data based on selected disaster type
filtered_data = data[data["disaster_type"] == disaster_type]

# Create a Folium map centered around a sample location
map_center = [filtered_data["lat"].mean(), filtered_data["lon"].mean()]
m = folium.Map(location=map_center, zoom_start=5, tiles="Stamen Terrain")

# Add markers to map with clustering
marker_cluster = MarkerCluster().add_to(m)
for idx, row in filtered_data.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"{disaster_type} at ({row['lat']}, {row['lon']})",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(marker_cluster)

# Add heatmap if there are enough data points
if len(filtered_data) > 1:
    HeatMap(filtered_data[["lat", "lon"]].values, radius=10).add_to(m)

# Display Folium map in Streamlit app
st.markdown("### Impacted Areas Map")
st_data = st_folium(m, width=1000, height=600)

# Add an information section
st.sidebar.markdown("### Insights")
st.sidebar.markdown(
    f"#### Selected Disaster Type: **{disaster_type}**"
)
st.sidebar.markdown(f"#### Total Impacted Locations: **{len(filtered_data)}**")

# Footer
st.markdown("---")
st.markdown(
    """
    #### About This Dashboard
    This tool helps visualize disaster impacts, with data aggregated in real-time. Switch between disaster types
    to view affected areas, and gain insights into the geographical distribution of each event.
    """
)