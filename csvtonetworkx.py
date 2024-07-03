import pandas as pd
import networkx as nx
import ast  # To safely evaluate string representations of lists

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
            raise ValueError("Lat-long string is not in the expected format.")
    except Exception as e:
        print(f"Error parsing '{latlong_str}': {e}")
        return None

# Step 2: Parse the data and add edges
for index, row in df.iterrows():
    line_stops = [parse_latlong(stop) for stop in row.dropna() if parse_latlong(stop) is not None]  # Convert each stop to a (lat, long) tuple
    for i in range(len(line_stops) - 1):
        start_stop = line_stops[i]
        end_stop = line_stops[i + 1]
        G.add_edge(start_stop, end_stop, line=index)
        G.remove_edges_from(nx.selfloop_edges(G))

# Step 3: Print basic information about the graph
print("Graph Information:")
print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")
print(f"Nodes: {list(G.nodes())[:10]}")  # Print first 10 nodes
print(f"Edges: {list(G.edges())[:10]}")  # Print first 10 edges

# Optionally, if you want to visualize the graph
import matplotlib.pyplot as plt

# Create positions for visualization
pos = {stop: (stop[1], stop[0]) for stop in G.nodes()}  # Note: (longitude, latitude) for visualization

plt.figure(figsize=(12, 8))
nx.draw(G, pos, with_labels=False, node_size=50, font_size=8)
plt.show()