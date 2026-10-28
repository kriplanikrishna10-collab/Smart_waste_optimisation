"""Smart Waste Collection Dashboard — Bandra, Mumbai."""

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from data_generator import generate_bins
from database import save_bins
from road_network import load_bandra_road_network
from road_routing import generate_road_based_bins
from road_optimizer import optimize_road_route


st.set_page_config(
    page_title="Smart Waste Collection — Bandra",
    page_icon="♻️",
    layout="wide",
)

st.title("♻️ Smart Waste Collection — Bandra")
st.caption("OpenStreetMap roads | OR-Tools | Synthetic waste data")

st.info(
    "Roads are sourced from OpenStreetMap. Bin locations, fill levels, "
    "and waste quantities are simulated. The depot is temporary and is "
    "not a verified municipal depot. Distances do not include live traffic."
)

# Sidebar settings
with st.sidebar:
    st.header("Simulation Settings")

    number_of_bins = st.slider(
        "Number of bins", min_value=5, max_value=30, value=10
    )

    vehicle_capacity = st.slider(
        "Vehicle capacity (kg)",
        min_value=500,
        max_value=3000,
        value=1500,
        step=100,
    )

    fill_threshold = st.slider(
        "Collection threshold (%)",
        min_value=50,
        max_value=100,
        value=80,
        step=5,
    )

    regenerate = st.button(
        "Generate new simulation",
        use_container_width=True,
    )

# Generate reproducible synthetic bin data and real road-node locations.
if "road_bins" not in st.session_state or regenerate:
    if regenerate:
        seed = int(np.random.default_rng().integers(0, 2**32 - 1))
    else:
        seed = 42

    road_bins = generate_road_based_bins(
        number_of_bins=number_of_bins,
        seed=seed,
    )
    waste_data = generate_bins(
        number_of_bins=number_of_bins,
        seed=seed,
    )

    road_bins["capacity_kg"] = waste_data["capacity_kg"].to_numpy()
    road_bins["fill_percentage"] = waste_data["fill_percentage"].to_numpy()
    road_bins["waste_kg"] = waste_data["waste_kg"].to_numpy()

    st.session_state["road_bins"] = road_bins

bins = st.session_state["road_bins"].copy()

bins["needs_collection"] = (
    bins["fill_percentage"] >= fill_threshold
)

bins["map_status"] = bins["needs_collection"].map(
    {
        True: "Needs collection",
        False: "Below collection threshold",
    }
)

collection_bins = (
    bins.loc[bins["needs_collection"]]
    .copy()
    .reset_index(drop=True)
)

# Load locally cached Bandra driving network.
graph = load_bandra_road_network()

# Temporary depot for testing: first simulated bin's road node.
depot_node = bins.iloc[0]["road_node"]

# Store the current simulation in SQLite.
database_bins = bins[
    [
        "bin_id",
        "capacity_kg",
        "fill_percentage",
        "waste_kg",
        "needs_collection",
    ]
].copy()

database_bins["x_coordinate_km"] = bins["longitude"]
database_bins["y_coordinate_km"] = bins["latitude"]

save_bins(
    database_bins,
    PROJECT_ROOT / "data" / "waste_collection.db",
)

# Overview metrics
total_waste = float(bins["waste_kg"].sum())
selected_waste = float(collection_bins["waste_kg"].sum())

st.subheader("Simulation Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total bins", len(bins))
col2.metric("Bins needing collection", len(collection_bins))
col3.metric("Total simulated waste", f"{total_waste:,.1f} kg")
col4.metric("Waste selected", f"{selected_waste:,.1f} kg")

st.divider()
st.subheader("Route Optimization")

result = None

if collection_bins.empty:
    st.success("No bins meet the collection threshold.")
else:
    result = optimize_road_route(
        collection_bins,
        depot_node=depot_node,
        vehicle_capacity_kg=vehicle_capacity,
    )

    if result["distance_km"] is not None:
        st.metric(
            "Optimized road distance",
            f"{result['distance_km']:.2f} km",
        )
        st.success("Optimization status: Success")

        if result["bin_ids"]:
            st.write(
                "**Collection order:** Depot → "
                + " → ".join(result["bin_ids"])
                + " → Depot"
            )
    else:
        st.warning(result["status"])

st.caption(
    "The current optimizer uses one vehicle. A route is not returned "
    "when the selected waste exceeds the vehicle's capacity."
)

st.divider()
st.subheader("Bandra Collection Map")

st.markdown(
    "🔴 **Needs collection** · 🔵 **Below threshold** · "
    "🟡 **Depot** · 🟢 **Optimized road route**"
)

# Create bin markers first.
fig = px.scatter_map(
    bins,
    lat="latitude",
    lon="longitude",
    color="map_status",
    hover_name="bin_id",
    hover_data=[
        "fill_percentage",
        "capacity_kg",
        "waste_kg",
        "road_node",
    ],
    color_discrete_map={
        "Needs collection": "#e53935",
        "Below collection threshold": "#1e88e5",
    },
    map_style="open-street-map",
    center={
        "lat": float(bins["latitude"].mean()),
        "lon": float(bins["longitude"].mean()),
    },
    zoom=13,
    height=650,
    title="Simulated bins on the Bandra road network",
)

fig.update_traces(
    marker={"size": 15, "opacity": 1.0},
    selector={"type": "scattermap"},
)

# Draw the optimized route using the actual road paths.
if (
    result is not None
    and result.get("status") == "Success"
    and result.get("bin_ids")
):
    bin_node_by_id = dict(
        zip(bins["bin_id"], bins["road_node"])
    )

    route_stops = [depot_node]
    route_stops.extend(
        bin_node_by_id[bin_id]
        for bin_id in result["bin_ids"]
    )
    route_stops.append(depot_node)

    route_coordinates = []
    route_error = None

    try:
        for origin, destination in zip(
            route_stops[:-1], route_stops[1:]
        ):
            road_path = nx.shortest_path(
                graph,
                source=origin,
                target=destination,
                weight="length",
            )

            if route_coordinates:
                road_path = road_path[1:]

            route_coordinates.extend(road_path)

        if route_coordinates:
            fig.add_trace(
                go.Scattermap(
                    lat=[
                        graph.nodes[node]["y"]
                        for node in route_coordinates
                    ],
                    lon=[
                        graph.nodes[node]["x"]
                        for node in route_coordinates
                    ],
                    mode="lines",
                    name="Optimized road route",
                    line={
                        "width": 5,
                        "color": "#00C853",
                    },
                    hoverinfo="skip",
                )
            )

    except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
        route_error = str(exc)

    if route_error:
        st.warning(f"Could not draw the complete route: {route_error}")

# Add a distinct depot marker.
depot_data = graph.nodes[depot_node]

fig.add_trace(
    go.Scattermap(
        lat=[depot_data["y"]],
        lon=[depot_data["x"]],
        mode="markers+text",
        name="Temporary depot",
        text=["DEPOT"],
        textposition="top right",
        marker={
            "size": 17,
            "color": "#FFD600",
        },
    )
)

fig.update_layout(
    margin=dict(l=0, r=0, t=45, b=0),
    legend=dict(
        title="Map layers",
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "If the map background is blank, OpenStreetMap map tiles may be "
    "blocked by your network. The road graph is cached locally."
)

st.divider()
st.subheader("Bins Requiring Collection")

if collection_bins.empty:
    st.success("No bins currently require collection.")
else:
    st.dataframe(
        collection_bins[
            [
                "bin_id",
                "latitude",
                "longitude",
                "road_node",
                "capacity_kg",
                "fill_percentage",
                "waste_kg",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Research note: the road network is real OpenStreetMap data, but "
    "bin locations, fill levels, and waste quantities are synthetic. "
    "The displayed depot is temporary, and road distances do not account "
    "for live traffic."
)
