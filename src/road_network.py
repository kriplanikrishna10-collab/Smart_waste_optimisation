"""Download and cache the OpenStreetMap road network for Bandra."""

from pathlib import Path

import networkx as nx
import osmnx as ox


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GRAPH_PATH = DATA_DIR / "bandra_road_network.graphml"

# Approximate search area; OSMnx will use this place query to find boundaries.
PLACE_QUERY = "Bandra West, Mumbai, Maharashtra, India"


def load_bandra_road_network(force_download: bool = False) -> nx.MultiDiGraph:
    """Load the cached Bandra road graph or download it from OpenStreetMap."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if GRAPH_PATH.exists() and not force_download:
        graph = ox.load_graphml(GRAPH_PATH)
        print(f"Loaded cached road network: {GRAPH_PATH}")
    else:
        print(f"Downloading road network for {PLACE_QUERY} ...")
        graph = ox.graph_from_place(
            PLACE_QUERY,
            network_type="drive",
            simplify=True,
        )
        ox.save_graphml(graph, GRAPH_PATH)
        print(f"Saved road network: {GRAPH_PATH}")

    print(f"Road nodes: {len(graph.nodes):,}")
    print(f"Road edges: {len(graph.edges):,}")
    print("Road network source: OpenStreetMap")
    return graph


if __name__ == "__main__":
    road_graph = load_bandra_road_network()
    print("Road network loaded successfully.")
