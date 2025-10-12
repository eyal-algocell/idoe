# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- OR Python 3.11+ and pip

## Option 1: Using Docker (Recommended)

### Run the Application
```bash
# Build and run the optimizer
docker-compose up app

# View results
cat output/results.json
```

### Run Tests
```bash
# Build and run all tests
docker-compose up test

# View test results
cat test-results/status.txt
cat test-results/junit.xml

# View coverage report (open in browser)
open test-results/coverage/index.html
```

## Option 2: Using Python Locally

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application
```bash
# Run with default parameters
python -m src.main

# Save results to file
python -m src.main --output my_results.json

# Enable verbose output
python -m src.main --verbose
```

### Run Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_optimizer.py -v
```

## Expected Output

### Application Output
```
Initializing iDoE Optimizer...
Running optimization...

================================================================================
Optimization Status: Optimal
Objective Value: 0.675000
Number of Experiments Used: 5
Total Stages Used: 15

Experiment Assignments:
Experiment 1: Stage 1: Combo 9 (μ_set=0.1225, Temp=33.0°C), Stage 2: Combo 6 (μ_set=0.11, Temp=31.0°C), Stage 3: Combo 6 (μ_set=0.11, Temp=31.0°C)
Experiment 2: Stage 1: Combo 7 (μ_set=0.1225, Temp=29.0°C), Stage 2: Combo 1 (μ_set=0.135, Temp=31.0°C), Stage 3: Combo 8 (μ_set=0.1475, Temp=29.0°C)
...
================================================================================
```

### Test Output
```
============================= test session starts ==============================
...
============================== 38 passed in 7.84s ==============================

Coverage: 80%
```

## What Happens

1. **Application Run:**
   - Loads DOE factor values (9 combinations)
   - Builds MILP optimization problem
   - Solves for optimal experiment design
   - Outputs 5 experiments with 3 stages each
   - Saves results to JSON file

2. **Test Run:**
   - Runs 38 automated tests
   - Validates configuration
   - Tests data models
   - Verifies optimizer constraints
   - Executes end-to-end workflows
   - Generates coverage report

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [SUMMARY.md](SUMMARY.md) for project overview
- Review [TEST_RESULTS.md](TEST_RESULTS.md) for test details
- Explore [src/config.py](src/config.py) to customize parameters

## Troubleshooting

### Docker Issues
```bash
# Clean up containers
docker-compose down

# Rebuild images
docker-compose build

# Check container logs
docker logs idoe-app
docker logs idoe-test
```

### Python Issues
```bash
# Verify Python version
python --version  # Should be 3.11+

# Check installed packages
pip list

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Getting Help

- Check the logs for error messages
- Verify all dependencies are installed
- Ensure Docker has sufficient resources (if using Docker)
- Review the test output for specific failures

## Success Indicators

✅ Application completes with "Optimization Status: Optimal"
✅ Results file created in output directory
✅ All 38 tests pass
✅ Test results saved to test-results directory
✅ Coverage report shows 80% coverage