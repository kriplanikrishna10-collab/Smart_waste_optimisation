"""Optimize waste collection routes using real OpenStreetMap road distances."""

import networkx as nx
import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from road_routing import (
    generate_road_based_bins,
    get_road_graph,
    road_distance_matrix,
)


def optimize_road_route(
    bins: pd.DataFrame,
    depot_node,
    vehicle_capacity_kg: float = 1500,
) -> dict:
    """Optimize one vehicle route using shortest driving-road distances.

    The bins DataFrame must include bin_id, road_node, and waste_kg columns.
    The depot_node must be a node ID in the downloaded road network.
    """
    if vehicle_capacity_kg <= 0:
        raise ValueError("Vehicle capacity must be positive")

    if bins.empty:
        return {
            "status": "No collection required",
            "bin_ids": [],
            "distance_km": 0.0,
        }

    total_waste = float(bins["waste_kg"].sum())

    if total_waste > vehicle_capacity_kg:
        return {
            "status": (
                f"Vehicle capacity exceeded: {total_waste:.1f} kg required, "
                f"{vehicle_capacity_kg:.1f} kg available"
            ),
            "bin_ids": [],
            "distance_km": None,
        }

    graph = get_road_graph()

    road_nodes = [depot_node] + bins["road_node"].tolist()

    try:
        distance_matrix = road_distance_matrix(graph, road_nodes)
    except (nx.NetworkXNoPath, ValueError) as exc:
        return {
            "status": f"Road route unavailable: {exc}",
            "bin_ids": [],
            "distance_km": None,
        }

    manager = pywrapcp.RoutingIndexManager(
        len(road_nodes),
        1,
        0,
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(callback_index)

    parameters = pywrapcp.DefaultRoutingSearchParameters()
    parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    parameters.time_limit.seconds = 5

    solution = routing.SolveWithParameters(parameters)

    if solution is None:
        return {
            "status": "No feasible route found",
            "bin_ids": [],
            "distance_km": None,
        }

    route_bin_indices = []
    index = routing.Start(0)

    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        if node_index != 0:
            route_bin_indices.append(node_index - 1)
        index = solution.Value(routing.NextVar(index))

    ordered_bins = bins.iloc[route_bin_indices]

    return {
        "status": "Success",
        "bin_ids": ordered_bins["bin_id"].tolist(),
        "distance_km": round(solution.ObjectiveValue() / 1000, 2),
        "total_waste_kg": round(total_waste, 2),
        "depot_node": depot_node,
    }


if __name__ == "__main__":
    graph = get_road_graph()

    # Generate reproducible simulated bin locations at real road nodes.
    bins = generate_road_based_bins(number_of_bins=10, seed=42)

    # For this initial test, use the first generated road node as the depot.
    # We will replace this with a separately selected depot location later.
    depot_node = bins.iloc[0]["road_node"]

    # Simulate waste amounts and identify bins requiring collection.
    bins["waste_kg"] = [100, 120, 90, 80, 110, 95, 130, 85, 100, 105]
    bins["needs_collection"] = bins["waste_kg"] >= 100
    collection_bins = bins.loc[bins["needs_collection"]].copy()

    result = optimize_road_route(
        collection_bins,
        depot_node=depot_node,
        vehicle_capacity_kg=1500,
    )

    print(f"\nBins selected for collection: {len(collection_bins)}")
    print(f"Optimization status: {result['status']}")
    print(f"Optimized road distance: {result['distance_km']} km")
    print(f"Collection order: {result['bin_ids']}")
