# TVT-Code: Network Service Computing Node Selection Algorithms

This project implements and compares different algorithms for selecting computing nodes in network services.

## Implemented Algorithms

The project includes the following algorithms:

- **MINLP (Mixed Integer Non-Linear Programming)**: Mixed integer non-linear programming algorithm
- **CPEG (Computing Power Expansion Graph)**: Computing power expanded graph algorithm
- **CNE (Computing Node Extended)**: Computing node extended algorithm
- **CCN (Closest Computing Node)**: Closest computing node algorithm
- **MPCN (Maximum Processing Capacity Node)**: Maximum processing capacity node algorithm

## Main Features

### Network Parameter Generation
`network_parameters.py` generates random network topologies and parameters:
- Generates specified number of nodes and edges
- Randomly selects computing nodes (approximately 60% of nodes)
- Assigns properties like bandwidth and propagation delay to edges
- Outputs network configuration in YAML format

### Performance Comparison Analysis
The project provides multiple comparison scripts:

- `compare2.py`: Compares algorithm performance in small networks (100 nodes, 2000 edges)
- `compare3.py`: Compares performance across different network scales (200-2000 nodes)
- `compare4.py`: Compares performance across different network densities
- `compare5.py`: Compares performance with fixed nodes (1000) and varying edges
- `compare6.py`: Specifically compares expansion performance of CPEG and CNE algorithms

### Performance Metrics
The comparison analysis includes:
- End-to-end delay
- Running time
- Memory usage
- Network expansion time (for CPEG and CNE)
- Number of nodes and edges after expansion (for CPEG and CNE)

## Usage
1. Generate network parameters:

```bash
python network_parameters.py
```

2. Run individual algorithm:
```bash
python <algorithm_name>.py
```

3. Perform performance comparison:
```bash
python compare<number>.py
```

## Output Results

All comparison analysis results are saved as CSV files:
- detailed_results.csv: Contains detailed data for each run
- summary_results.csv: Contains statistical summary data

## Dependencies

- networkx
- matplotlib
- yaml
- gurobipy (for MINLP algorithm)
- pympler (for memory usage analysis)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
