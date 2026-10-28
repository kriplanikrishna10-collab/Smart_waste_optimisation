# Smart Waste Collection Simulation and Route Optimization System

## 1. Project Overview

This project simulates municipal waste collection in a Mumbai-inspired urban environment. It models waste-bin fill levels, collection vehicles, and depot locations, then compares a baseline collection strategy with an optimized routing strategy.

## 2. Objectives

- Simulate waste accumulation in collection bins.
- Track bin capacity and collection status.
- Model collection vehicles and their capacity constraints.
- Optimize vehicle routes using open-source technologies.
- Compare travel distance and collection efficiency.
- Visualize simulation results through an interactive dashboard.

## 3. Technology Stack

- Python — core programming language
- SQLite — database
- Google OR-Tools — route optimization
- NetworkX — road-network graph modelling
- Streamlit — interactive dashboard
- Plotly — data visualization
- pytest — testing

## 4. Data

The initial version uses simulated data. Generated locations, bin fill levels, and collection records are synthetic and are not official municipal measurements.

## 5. Evaluation

The system will compare a baseline collection strategy with an optimized strategy using measures such as total travel distance, number of bins collected, vehicle utilization, overflow incidents, and estimated collection cost.

Improvements will be reported only after the strategies have been tested.

## 6. Reproducibility

Project dependencies, simulation settings, and evaluation methods will be documented so that the results can be reproduced.

## 7. Project Status

Stage 1: Project structure created.  
Next: Python environment and dependency setup.