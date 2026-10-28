"""Compare baseline and optimized waste collection routes."""

import math

import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


DEPOT = (5.0, 5.0)


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Calculate straight-line distance between two grid points, in km."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def prepare_collection_bins(bins: pd.DataFrame) -> pd.DataFrame:
    """Return only bins that need collection."""
    return bins.loc[bins["needs_collection"]].copy().reset_index(drop=True)


def baseline_route(bins: pd.DataFrame) -> dict:
    """Visit collection-required bins in their existing order."""
    points = [DEPOT]
    points.extend(
        zip(
            bins["x_coordinate_km"],
            bins["y_coordinate_km"],
        )
    )
    points.append(DEPOT)

    total_distance = sum(
        distance(points[i], points[i + 1])
        for i in range(len(points) - 1)
    )

    return {
        "strategy": "Baseline",
        "bin_ids": bins["bin_id"].tolist(),
        "distance_km": round(total_distance, 2),
    }


def optimized_route(
    bins: pd.DataFrame,
    vehicle_capacity_kg: float = 1500,
) -> dict:
    """Optimize a single vehicle route subject to its capacity."""
    if vehicle_capacity_kg <= 0:
        raise ValueError("Vehicle capacity must be positive")

    if bins.empty:
        return {
            "strategy": "Optimized",
            "bin_ids": [],
            "distance_km": 0.0,
            "status": "No collection required",
        }

    total_waste = float(bins["waste_kg"].sum())
    if total_waste > vehicle_capacity_kg:
        return {
            "strategy": "Optimized",
            "bin_ids": [],
            "distance_km": None,
            "status": (
                f"Single vehicle capacity exceeded: {total_waste:.1f} kg "
                f"required, {vehicle_capacity_kg:.1f} kg available"
            ),
        }

    locations = [DEPOT] + list(
        zip(bins["x_coordinate_km"], bins["y_coordinate_km"])
    )

    # OR-Tools uses integer costs, so distances are scaled to metres.
    distance_matrix = [
        [
            int(round(distance(locations[i], locations[j]) * 1000))
            for j in range(len(locations))
        ]
        for i in range(len(locations))
    ]

    manager = pywrapcp.RoutingIndexManager(len(locations), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 5

    solution = routing.SolveWithParameters(search_parameters)

    if solution is None:
        return {
            "strategy": "Optimized",
            "bin_ids": [],
            "distance_km": None,
            "status": "No feasible route found",
        }

    route_indices = []
    index = routing.Start(0)

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node != 0:
            route_indices.append(node - 1)
        index = solution.Value(routing.NextVar(index))

    route_bins = bins.iloc[route_indices]

    return {
        "strategy": "Optimized",
        "bin_ids": route_bins["bin_id"].tolist(),
        "distance_km": round(
            solution.ObjectiveValue() / 1000, 2
        ),
        "status": "Success",
    }


if __name__ == "__main__":
    from data_generator import generate_bins

    all_bins = generate_bins()
    collection_bins = prepare_collection_bins(all_bins)

    baseline = baseline_route(collection_bins)
    optimized = optimized_route(collection_bins)

    print(f"Bins requiring collection: {len(collection_bins)}")
    print(f"Baseline distance: {baseline['distance_km']} km")
    print(f"Optimized distance: {optimized['distance_km']} km")
    print(f"Optimization status: {optimized.get('status', 'Success')}")

    if (
        optimized["distance_km"] is not None
        and baseline["distance_km"] > 0
    ):
        improvement = (
            (baseline["distance_km"] - optimized["distance_km"])
            / baseline["distance_km"]
            * 100
        )
        print(f"Distance reduction: {improvement:.1f}%")