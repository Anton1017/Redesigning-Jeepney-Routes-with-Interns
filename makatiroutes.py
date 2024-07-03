import pandas as pd
import networkx as nx
import ast
import folium
import osmnx as ox
from folium import plugins

# Step 1: Read the CSV file, skipping the header row
df = pd.read_csv(r'jeepney\makatiroute.csv', header=0)

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

# Limit the DataFrame to the first 15 rows
df_limited = df.head(15)

# Get the bounding box for the area of interest from the limited DataFrame
latitudes = [parse_latlong(stop)[0] for _, row in df_limited.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]
longitudes = [parse_latlong(stop)[1] for _, row in df_limited.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]
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
for _, row in df_limited.iterrows():
    print("Processing row...")
    line_stops = [parse_latlong(stop) for stop in row.dropna() if parse_latlong(stop) is not None]
    
    if line_stops:
        print("Route completed!")
        for i in range(len(line_stops) - 1):
            start_stop = line_stops[i]
            end_stop = line_stops[i + 1]
            if start_stop != end_stop:
                draw_route(start_stop, end_stop)
    else:
        print("No valid stops in this row.")

# Add node markers (optional)
for node in [(parse_latlong(stop)) for _, row in df_limited.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]:
    folium.CircleMarker(location=[node[0], node[1]], radius=5, color='red', fill=True, fill_color='red', fill_opacity=0.7).add_to(m)

# Optionally, add a marker cluster
plugins.MarkerCluster(locations=[(node[0], node[1]) for node in [(parse_latlong(stop)) for _, row in df_limited.iterrows() for stop in row.dropna() if parse_latlong(stop) is not None]]).add_to(m)

# Save the map to an HTML file and open it
m.save('makati_jeepney_map_with_routes.html')