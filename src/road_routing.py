"""Road-based routing utilities for the Bandra waste collection project."""

from pathlib import Path

import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd

from road_network import load_bandra_road_network


def get_road_graph():
    """Load the saved Bandra road network."""
    return load_bandra_road_network()


def generate_road_based_bins(
    number_of_bins: int = 50,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic bin locations at randomly selected road nodes.

    These are simulated locations, not verified municipal waste-bin locations.
    """
    if number_of_bins < 1:
        raise ValueError("number_of_bins must be at least 1")

    graph = get_road_graph()
    nodes, _ = ox.graph_to_gdfs(graph)

    if len(nodes) < number_of_bins:
        raise ValueError(
            f"Requested {number_of_bins} bins, but only {len(nodes)} road nodes exist"
        )

    rng = np.random.default_rng(seed)
    selected_nodes = rng.choice(
        nodes.index.to_numpy(),
        size=number_of_bins,
        replace=False,
    )

    rows = []

    for index, node_id in enumerate(selected_nodes, start=1):
        node = graph.nodes[node_id]

        rows.append(
            {
                "bin_id": f"BIN-{index:03d}",
                "latitude": float(node["y"]),
                "longitude": float(node["x"]),
                "road_node": node_id,
            }
        )

    return pd.DataFrame(rows)


def road_distance_km(graph, origin_node, destination_node) -> float:
    """Calculate shortest directed road distance in kilometres."""
    distance_m = nx.shortest_path_length(
        graph,
        source=origin_node,
        target=destination_node,
        weight="length",
    )
    return float(distance_m) / 1000.0


def road_distance_matrix(graph, road_nodes: list) -> list[list[int]]:
    """Build a road-distance matrix in metres for selected road nodes."""
    matrix = []

    for origin in road_nodes:
        lengths = nx.single_source_dijkstra_path_length(
            graph,
            source=origin,
            weight="length",
        )

        row = []

        for destination in road_nodes:
            if destination not in lengths:
                raise ValueError(
                    f"No directed road route from {origin} to {destination}"
                )

            row.append(int(round(lengths[destination])))

        matrix.append(row)

    return matrix


if __name__ == "__main__":
    graph = get_road_graph()
    bins = generate_road_based_bins(number_of_bins=10)

    print(f"\nGenerated simulated geographic bins: {len(bins)}")
    print(bins.head().to_string(index=False))

    if len(bins) >= 2:
        origin = bins.iloc[0]["road_node"]
        destination = bins.iloc[1]["road_node"]

        try:
            distance = road_distance_km(graph, origin, destination)
            print(f"\nRoad distance between first two bins: {distance:.2f} km")
        except nx.NetworkXNoPath:
            print("No directed route exists between the selected road nodes.")
