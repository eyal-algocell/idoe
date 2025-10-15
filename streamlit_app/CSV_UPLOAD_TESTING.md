# CSV Upload Feature - Testing Guide

## Overview
This document provides testing instructions for the CSV upload feature in the iDoE Planner Streamlit application.

## Feature Description
The CSV upload feature allows users to:
- Download an example CSV file with the correct format
- Upload their own CSV file containing experiment combinations
- Automatically extract parameters and their values from the CSV

## Automated Tests

### Unit Tests
All unit tests are located in `tests/test_parameter_manager.py`.

**Run all tests:**
```bash
docker exec idoe-streamlit-app pytest tests/test_parameter_manager.py -v
```

**Run only CSV tests:**
```bash
docker exec idoe-streamlit-app pytest tests/test_parameter_manager.py::TestCSVFunctionality -v
```

### Test Coverage
The following scenarios are tested:
1. ✅ Generate example CSV
2. ✅ Load CSV with "Combo #" index column
3. ✅ Load CSV without index column
4. ✅ Case-insensitive index column detection
5. ✅ Load parameters without units
6. ✅ Replace existing parameters when loading CSV
7. ✅ Error handling for non-numeric values
8. ✅ Error handling for empty columns
9. ✅ Load three or more parameters
10. ✅ Roundtrip export/import preserves data

## Manual Testing Guide

### Prerequisites
- Docker container is running: `docker ps | grep idoe-streamlit-app`
- Access app at: http://localhost:8501

### Test Case 1: Download and Upload Example CSV

**Steps:**
1. Open http://localhost:8501 in your browser
2. Navigate to Section 1: "Define Parameters"
3. Expand the "📤 Upload Combinations from CSV" section
4. Click "📥 Download Example CSV" button
5. Save the file as `example_combinations.csv`
6. Open the file in a text editor or Excel to verify format
7. Click "Choose a CSV file" and select the downloaded file
8. Verify parameters are loaded correctly

**Expected Result:**
- File downloads successfully
- File contains "Combo #", "Temperature (°C)", and "μ_set (h⁻¹)" columns
- 15 rows of data (3 temperatures × 5 mu values)
- After upload, you should see:
  - Success message: "✅ Successfully loaded 2 parameters!"
  - Parameters displayed in "Current Parameters" section
  - Info box showing "📊 Total combinations: **15**"

### Test Case 2: Custom CSV with Different Parameters

**Steps:**
1. Create a new CSV file named `custom_test.csv` with this content:
```csv
Combo #,Temperature (°C),pH,DO (%)
1,29.0,6.5,20.0
2,29.0,6.5,40.0
3,29.0,7.0,20.0
4,29.0,7.0,40.0
5,31.0,6.5,20.0
6,31.0,6.5,40.0
7,31.0,7.0,20.0
8,31.0,7.0,40.0
```
2. Upload this CSV via the file uploader
3. Verify parameters are loaded

**Expected Result:**
- Success message shows "✅ Successfully loaded 3 parameters!"
- Three parameters displayed: Temperature, pH, DO
- Total combinations: **8**
- Values are correctly extracted for each parameter

### Test Case 3: CSV Without Index Column

**Steps:**
1. Create a CSV file named `no_index.csv`:
```csv
Temperature (°C),pH
29.0,6.5
29.0,7.0
31.0,6.5
31.0,7.0
```
2. Upload this CSV
3. Verify parameters are loaded

**Expected Result:**
- Success message shows "✅ Successfully loaded 2 parameters!"
- Both parameters loaded correctly
- Total combinations: **4**

### Test Case 4: Invalid CSV (Error Handling)

**Steps:**
1. Create a CSV with non-numeric values:
```csv
Temperature (°C),pH
hot,acidic
cold,basic
```
2. Upload this CSV
3. Observe error message

**Expected Result:**
- Error message: "❌ Parameter 'Temperature' contains non-numeric values" (or similar)
- No parameters loaded
- App remains functional

### Test Case 5: End-to-End Workflow

**Steps:**
1. Upload a valid CSV (use the example CSV)
2. Configure experiment structure (e.g., 6 runs, 3 stages, 30 hours)
3. Configure constraints as desired
4. Click "🚀 Run Planner"
5. Wait for optimization
6. Verify results are displayed

**Expected Result:**
- Optimization completes successfully
- Results section shows:
  - Summary metrics (Runs Used, Total Stages, Combos Covered, Coverage)
  - Combined and Per-Run tables
  - Visualizations (heatmap, design space, run timelines)
- Download Excel button appears in sidebar

## CSV Format Specification

### Valid Format
```csv
Combo #,Parameter1 (unit1),Parameter2 (unit2),...
1,value1_1,value2_1,...
2,value1_2,value2_2,...
...
```

### Format Rules
1. **First Column (Optional):** Can be "Combo #", "combo", "#", or "index" (case-insensitive)
   - If present, it will be ignored during import
   - If not present, all columns will be treated as parameters

2. **Parameter Columns:**
   - Format: `ParameterName (Unit)` or just `ParameterName`
   - Units are optional and extracted from parentheses
   - Examples:
     - `Temperature (°C)` → Name: "Temperature", Unit: "°C"
     - `pH` → Name: "pH", Unit: ""

3. **Values:**
   - Must be numeric (integers or floats)
   - Unique values for each parameter are automatically extracted
   - Values are sorted automatically

4. **Combinations:**
   - Each row represents one possible combination
   - The tool automatically extracts unique values for each parameter
   - Generates all possible combinations from unique values

## Troubleshooting

### Issue: CSV upload doesn't work
**Solution:**
- Check that file is valid CSV format
- Ensure all values are numeric
- Verify CSV has at least one parameter column

### Issue: Parameters not showing after upload
**Solution:**
- Check browser console for errors
- Verify CSV format matches specification
- Try downloading and uploading the example CSV first

### Issue: "Too many combinations" error
**Solution:**
- Reduce number of unique values per parameter
- Reduce number of parameters
- Limit is 200 combinations

## Test Results Summary

### Automated Tests: ✅ PASSED
- **Total Tests:** 30
- **Passed:** 30
- **Failed:** 0
- **CSV-Specific Tests:** 10/10 passed

### Integration Tests: ✅ VERIFIED
- CSV generation works correctly
- CSV loading works correctly
- Parameter extraction works correctly
- Validation works correctly

### Manual Testing Status: ⏳ READY FOR TESTING
Access the app at: **http://localhost:8501**

---

**Last Updated:** 2025-10-15
**Docker Container:** idoe-streamlit-app
**Version:** 1.0
