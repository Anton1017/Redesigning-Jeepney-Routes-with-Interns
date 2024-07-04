import pandas as pd
import networkx as nx
import ast
import folium
import osmnx as ox
from folium import plugins
import numpy as np
from geopy.distance import geodesic

# Step 1: Read the CSV file, skipping the header row
df = pd.read_csv('manilaRoutesNew/jeepney_lines.csv', header=0)

df = df.head(10)

# Print out the DataFrame to verify it's loaded correctly
print("DataFrame loaded:")
print(df.head())

# Function to parse a lat-long string and return a tuple (lat, long)
def parse_latlong(latlong_str):
    try:
        # Clean up the string by removing extra brackets and spaces
        latlong_str = latlong_str.strip().strip('[]').rstrip(',').rstrip(']')
        # Convert string representation to a list
        latlong_list = ast.literal_eval(f'[{latlong_str}]')
        if isinstance(latlong_list, list) and len(latlong_list) == 2:
            return (float(latlong_list[0]), float(latlong_list[1]))
        else:
            return None
    except Exception as e:
        print(f"Error parsing lat-long string '{latlong_str}': {e}")
        return None

# Get the bounding box for the area of interest from the entire DataFrame
latitudes = [parse_latlong(stop)[0] for _, row in df.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]
longitudes = [parse_latlong(stop)[1] for _, row in df.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]
north, south = max(latitudes), min(latitudes)
east, west = max(longitudes), min(longitudes)

print(f"Bounding Box: North={north}, South={south}, East={east}, West={west}")

# Step 2: Download the road network within the bounding box
G = ox.graph_from_bbox(north, south, east, west, network_type='all')

# Convert the graph to a directed graph (for shortest path routing)
G = G.to_directed()

# Step 3: Create a Folium map centered around the graph's central point
mean_lat = (north + south) / 2
mean_lon = (east + west) / 2
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=13)

# Function to find and draw the route on the map
def draw_route(start, end):
    try:
        # Get nearest nodes to the start and end points
        start_node = ox.distance.nearest_nodes(G, start[1], start[0])
        end_node = ox.distance.nearest_nodes(G, end[1], end[0])
        
        # Find the shortest path between start and end nodes
        route = nx.shortest_path(G, start_node, end_node, weight='length')
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
        
        # Add the route to the map
        folium.PolyLine(locations=route_coords, color='blue', weight=2.5).add_to(m)
    except Exception as e:
        print(f"Error drawing route from {start} to {end}: {e}")

# Step 4: Add nodes and edges to the map
routes = []
for _, row in df.iterrows():
    print("Processing row...")
    line_stops = [parse_latlong(stop) for stop in row.dropna() if parse_latlong(stop) is not None]
    
    if line_stops:
        print("Route completed!")
        for i in range(len(line_stops) - 1):
            start_stop = line_stops[i]
            end_stop = line_stops[i + 1]
            if start_stop != end_stop:
                draw_route(start_stop, end_stop)
                routes.append((start_stop, end_stop))
    else:
        print("No valid stops in this row.")

# Add node markers (optional)
for node in [(parse_latlong(stop)) for _, row in df.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]:
    folium.CircleMarker(location=[node[0], node[1]], radius=5, color='red', fill=True, fill_color='red', fill_opacity=0.7).add_to(m)

# Optionally, add a marker cluster
plugins.MarkerCluster(locations=[(node[0], node[1]) for node in [(parse_latlong(stop)) for _, row in df.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]]).add_to(m)

# Save the map to an HTML file and open it
m.save('jeepney_map_with_routes.html')

# Create a graph for the jeepney network
jeepney_graph = nx.Graph()

# Function to calculate distance between two lat-long points in km
def calculate_distance(point1, point2):
    return geodesic(point1, point2).kilometers

# Add edges to the graph with weight as distance in km
for route in routes:
    distance = calculate_distance(route[0], route[1])
    jeepney_graph.add_edge(route[0], route[1], weight=distance)

# Calculate the metrics
num_routes = df.shape[0]
unique_stops = len(set(jeepney_graph.nodes()))

# Find the largest connected component
largest_cc = max(nx.connected_components(jeepney_graph), key=len)
largest_cc_graph = jeepney_graph.subgraph(largest_cc).copy()

# Network diameter (longest shortest path) of the largest connected component
try:
    diameter = nx.diameter(largest_cc_graph, weight='weight')
except nx.NetworkXError:
    diameter = "N/A (Graph is not connected)"

# Shortest and longest routes
route_lengths = []
for _, row in df.iterrows():
    route_stops = [parse_latlong(stop) for stop in row.dropna() if parse_latlong(stop) is not None]
    route_length = sum(calculate_distance(route_stops[i], route_stops[i+1]) for i in range(len(route_stops)-1))
    route_lengths.append(route_length)

shortest_route = min(route_lengths)
longest_route = max(route_lengths)

# Average path length of the largest connected component
try:
    avg_path_length = nx.average_shortest_path_length(largest_cc_graph, weight='weight')
except nx.NetworkXError:
    avg_path_length = "N/A (Graph is not connected)"

# Average route length
avg_route_length = sum(route_lengths) / num_routes

# Number of connected components
num_connected_components = nx.number_connected_components(jeepney_graph)

# Print the results
print(f"Number of routes: {num_routes}")
print(f"Number of unique stops: {unique_stops}")
print(f"Network diameter of largest connected component: {diameter:.2f} km" if isinstance(diameter, float) else diameter)
print(f"Shortest route: {shortest_route:.2f} km")
print(f"Longest route: {longest_route:.2f} km")
print(f"Average path length of largest connected component: {avg_path_length:.2f} km" if isinstance(avg_path_length, float) else avg_path_length)
print(f"Average route length: {avg_route_length:.2f} km")
print(f"Number of connected components: {num_connected_components}")
