import pandas as pd
import networkx as nx
import ast
import folium
from folium import plugins

# Step 1: Read the CSV file, skipping the header row
df = pd.read_csv(r'jeepney\makatiroute.csv', header=0)

# Create an empty graph
G = nx.Graph()

# Function to parse a lat-long string and return a tuple (lat, long)
def parse_latlong(latlong_str):
    try:
        # Clean up the string by stripping any trailing commas or spaces
        latlong_str = latlong_str.strip().rstrip(',')
        # Convert string representation to a list
        latlong_list = ast.literal_eval(latlong_str)
        if isinstance(latlong_list, list) and len(latlong_list) == 2:
            return (float(latlong_list[0]), float(latlong_list[1]))
        else:
            return None
    except Exception:
        return None

# Step 2: Parse the data and add edges
for _, row in df.iterrows():
    line_stops = [parse_latlong(stop) for stop in row.dropna() if parse_latlong(stop) is not None]  # Convert each stop to a (lat, long) tuple
    for i in range(len(line_stops) - 1):
        start_stop = line_stops[i]
        end_stop = line_stops[i + 1]
        if start_stop != end_stop:  # Ensure no self-loops
            G.add_edge(start_stop, end_stop)

# Remove any self-loops that may have been accidentally added
G.remove_edges_from(nx.selfloop_edges(G))

# Step 3: Create a Folium map centered around the graph's central point
# Calculate the mean latitude and longitude for centering the map
latitudes = [lat for lat, lon in G.nodes()]
longitudes = [lon for lat, lon in G.nodes()]
mean_lat = sum(latitudes) / len(latitudes)
mean_lon = sum(longitudes) / len(longitudes)

# Create a Folium map
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=13)

# Add nodes to the map
for node in G.nodes():
    folium.CircleMarker(
        location=[node[0], node[1]],
        radius=5,
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.7
    ).add_to(m)

# Add edges to the map
for edge in G.edges():
    folium.PolyLine(
        locations=[edge[0], edge[1]],
        color='gray',
        weight=2
    ).add_to(m)

# Optionally, add a marker cluster
plugins.MarkerCluster(locations=[(node[0], node[1]) for node in G.nodes()]).add_to(m)

# Save the map to an HTML file and open it
m.save('jeepney_map.html')