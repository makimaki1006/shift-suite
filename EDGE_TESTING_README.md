# Edge Case Testing Suite for Holiday Exclusion Fixes

This testing suite provides comprehensive validation of the holiday exclusion fixes implemented in the Shift-Suite system. The suite tests various edge cases, boundary conditions, data integrity, performance, and UI functionality.

## Files Created

### 1. `EDGE_CASE_TESTING.py`
Main testing framework that includes:
- **Extreme Cases**: All holidays, no holidays, single day, full year scenarios
- **Boundary Conditions**: Month/year boundaries, partial weeks, mixed holiday types
- **Data Integrity**: Parquet consistency, aggregation accuracy, time slot alignment
- **Performance Testing**: Processing time, memory usage, cache efficiency
- **UI/UX Validation**: Dashboard tabs, heatmaps, dropdowns, date selectors

### 2. `PERFORMANCE_BENCHMARK.md`
Comprehensive performance documentation including:
- Processing speed improvements (50.8% average)
- Memory usage reduction (37.9% average) 
- Scalability analysis and benchmarks
- Real-world scenario performance metrics
- Detailed technical implementation analysis

### 3. `run_edge_case_tests.py`
Quick demonstration script that shows:
- Basic edge case scenarios
- Performance testing examples
- Data integrity validation
- Simple usage examples without full system setup

### 4. `EDGE_TESTING_README.md` (this file)
Documentation explaining usage and setup

## Quick Start

### Option 1: Run Quick Demo (Recommended for first time)
```bash
# Run basic demonstration
python run_edge_case_tests.py

# Run with full test suite
python run_edge_case_tests.py --full
```

### Option 2: Run Full Test Suite
```bash
# Run comprehensive testing
python EDGE_CASE_TESTING.py --data-dir ./test_data --output-dir ./test_results

# Run with verbose logging
python EDGE_CASE_TESTING.py --data-dir ./test_data --output-dir ./test_results --verbose
```

## Test Categories

### 1. Extreme Cases Testing

#### All Holiday Days (100% Exclusion)
Tests scenarios where every record should be excluded:
- Staff names: `×`, `休`, `OFF`, `-`, `有`
- Expected behavior: All records filtered out
- Performance: Measures efficiency of mass exclusion

#### No Holiday Days (0% Exclusion)  
Tests scenarios with only working staff:
- Staff names: `田中太郎`, `佐藤花子`, etc.
- Expected behavior: All records preserved
- Performance: Measures overhead of filtering logic

#### Single Day Periods
Tests minimal datasets:
- Holiday single day: Should be completely filtered
- Working single day: Should be completely preserved
- Edge case: Boundary between inclusion/exclusion

#### Full Year Periods (365 days)
Tests system scalability:
- Large dataset processing (52+ weeks of data)
- Memory usage under load
- Performance degradation analysis

### 2. Boundary Conditions Testing

#### Month Boundaries
Tests transitions between months:
- Month-end holidays (e.g., 月末休暇)
- Month-start holidays (e.g., 月初休暇)  
- Consistency across month transitions
- Date handling edge cases

#### Year Boundaries  
Tests year transitions:
- New Year holidays (年末年始)
- Leap year handling
- Year rollover consistency
- Long-term date accuracy

#### Partial Week Scenarios
Tests incomplete week periods:
- Week starting mid-week (Thu-Sun)
- Week ending mid-week (Mon-Wed)
- Mixed week patterns
- Weekend/weekday holiday distribution

#### Mixed Holiday Types
Tests multiple holiday categories simultaneously:
- `有給` (paid leave)
- `希望休` (requested leave)
- `施設休` (facility closure)  
- `研修` (training)
- `通常勤務` (regular work)

### 3. Data Integrity Testing

#### Parquet File Consistency
Tests data persistence:
- Save/load data integrity
- Column type preservation
- Content accuracy after serialization
- Filter consistency post-reload

#### Aggregation Accuracy
Tests calculation correctness:
- Staff counts before/after filtering
- Role distribution accuracy
- Time slot totals
- Statistical measure consistency

#### Time Slot Alignment
Tests temporal data handling:
- Chronological ordering maintenance
- No duplicate timestamps
- Interval consistency
- Date/time parsing accuracy

### 4. Performance Testing

#### Processing Time Analysis
Measures execution speed across dataset sizes:
- Small datasets (1K records): Target <0.1s
- Medium datasets (10K records): Target <1s  
- Large datasets (100K records): Target <10s
- Enterprise datasets (500K+ records): Target <60s

#### Memory Usage Analysis  
Measures memory efficiency:
- Peak memory usage during processing
- Memory cleanup after processing
- Memory growth patterns by dataset size
- Memory leak detection

#### Cache Efficiency Testing
Measures optimization effectiveness:
- Repeated operation performance
- Pattern matching cache hits
- Lookup table efficiency
- Compilation caching benefits

### 5. UI/UX Validation Testing

#### Dashboard Tabs Functionality
Tests user interface components:
- Tab loading without errors
- Data visualization accuracy  
- Interactive element responsiveness
- Cross-tab data consistency

#### Heatmap Color Scales
Tests visualization accuracy:
- Color mapping to data values
- Scale range appropriateness
- Color accessibility compliance
- Visual data representation fidelity

#### Dropdown Filters
Tests filtering interface:
- Staff selection accuracy
- Role filtering correctness
- Date range functionality
- Multi-select behavior

#### Date Range Selectors
Tests temporal filtering:
- Date picker functionality
- Range selection accuracy
- Boundary date handling
- Calendar navigation usability

## Expected Results

### Success Criteria

#### Functional Tests
- ✅ **All Holiday Days**: 100% exclusion rate
- ✅ **No Holiday Days**: 0% exclusion rate  
- ✅ **Mixed Scenarios**: Accurate partial exclusion
- ✅ **Boundary Cases**: Consistent behavior across transitions

#### Performance Tests
- ✅ **Processing Speed**: >50% improvement over baseline
- ✅ **Memory Usage**: <40% reduction from baseline
- ✅ **Scalability**: Linear or near-linear scaling
- ✅ **Cache Efficiency**: >90% cache hit rate for repeated operations

#### Data Integrity Tests
- ✅ **Parquet Consistency**: 100% data preservation accuracy
- ✅ **Aggregation Accuracy**: <1% variance in statistical measures
- ✅ **Time Alignment**: Perfect chronological ordering
- ✅ **Type Consistency**: All data types preserved correctly

### Warning Conditions
- ⚠️ **Processing Time**: >10x expected time (potential performance regression)
- ⚠️ **Memory Usage**: >2x expected memory (potential memory leak)
- ⚠️ **Data Variance**: >5% difference in aggregations (potential logic error)
- ⚠️ **Cache Miss**: <80% cache hit rate (optimization opportunity)

### Failure Conditions
- ❌ **Incorrect Exclusion**: Wrong records filtered/preserved
- ❌ **Data Loss**: Missing records after processing
- ❌ **Type Corruption**: Data type changes during processing  
- ❌ **Temporal Disorder**: Chronological order violated
- ❌ **System Crash**: Unhandled exceptions during processing

## Output Files

### Test Results
```
test_results/
├── edge_case_test_report.md          # Comprehensive test report
├── performance_analysis.png          # Performance visualization graphs
├── memory_usage_analysis.png         # Memory usage charts
├── test_results_detailed.json        # Machine-readable detailed results
└── test_summary.txt                  # Human-readable summary
```

### Sample Report Structure
```markdown
# Edge Case Testing Report

## Executive Summary
- Total Tests: 47
- Passed: 45 (95.7%)
- Failed: 1 (2.1%)  
- Warnings: 1 (2.1%)
- Overall Status: ✅ PASS

## Critical Issues
- boundary_conditions/year_boundaries: Date parsing error on leap year

## Performance Summary  
- Average Processing Improvement: 52.3%
- Average Memory Reduction: 39.1%
- Scalability Score: A+ (linear scaling maintained)

## Recommendations
1. Fix leap year boundary condition handling
2. Consider implementing data chunking for >1M records
3. Add progress indicators for long-running operations
```

## Usage Examples

### Basic Holiday Exclusion Test
```python
from shift_suite.tasks.utils import apply_rest_exclusion_filter
import pandas as pd

# Create test data with mixed staff (working + holiday)
test_data = pd.DataFrame({
    'ds': pd.date_range('2025-01-01', periods=4, freq='H'),
    'staff': ['田中太郎', '×', '休', '佐藤花子'],
    'role': ['nurse'] * 4,
    'parsed_slots_count': [1, 0, 0, 1]
})

# Apply filter
filtered_data = apply_rest_exclusion_filter(test_data, "example_test")

# Verify results
print(f"Original: {len(test_data)} records")
print(f"Filtered: {len(filtered_data)} records")  
print(f"Exclusion rate: {(len(test_data) - len(filtered_data)) / len(test_data) * 100:.1f}%")
# Expected: 50% exclusion (2 out of 4 records filtered)
```

### Performance Benchmark Test
```python
import time
from EDGE_CASE_TESTING import EdgeCaseTestSuite

# Initialize test suite
suite = EdgeCaseTestSuite(data_dir="./data", output_dir="./results")

# Test different data sizes
sizes = [1000, 10000, 50000]
for size in sizes:
    start_time = time.time()
    test_data = suite._create_performance_test_data(size)
    filtered = apply_rest_exclusion_filter(test_data, f"perf_{size}")
    end_time = time.time()
    
    processing_time = end_time - start_time
    throughput = size / processing_time
    
    print(f"{size:,} records: {processing_time:.3f}s ({throughput:.0f} records/sec)")
```

### Edge Case Validation
```python
# Test all-holiday scenario
all_holiday_data = suite._create_all_holidays_test_data()
result = suite._test_all_holidays_period()

if result['status'] == 'passed':
    print("✅ All-holiday test passed")
    print(f"Excluded {result['details']['original_count']} records as expected")
else:
    print(f"❌ All-holiday test failed: {result.get('error', 'Unknown error')}")

# Test boundary conditions  
boundary_result = suite._test_month_boundaries()
print(f"Month boundary test: {boundary_result['status']}")
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'shift_suite'
# Solution: Ensure you're running from the correct directory
cd /path/to/shift-suite-project
python EDGE_CASE_TESTING.py
```

#### Memory Issues
```bash
# Error: MemoryError during large dataset testing
# Solution: Reduce test data size or increase system memory
python EDGE_CASE_TESTING.py --data-dir ./smaller_test_data
```

#### Dashboard Testing Unavailable
```bash
# Warning: Dashboard module not available for UI testing
# Solution: This is expected if dash_app.py has import issues
# UI tests will be skipped automatically
```

### Performance Optimization Tips

1. **For Large Datasets**: Use data chunking
```python
def process_large_dataset(df, chunk_size=100000):
    results = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        filtered_chunk = apply_rest_exclusion_filter(chunk, f"chunk_{i}")
        results.append(filtered_chunk)
    return pd.concat(results, ignore_index=True)
```

2. **For Memory Constraints**: Enable garbage collection
```python
import gc
# After processing each test
gc.collect()
```

3. **For Slow Tests**: Use sampling
```python  
# Test with 10% sample for quick validation
sample_data = test_data.sample(frac=0.1, random_state=42)
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Edge Case Testing
on: [push, pull_request]

jobs:
  edge_case_tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: python EDGE_CASE_TESTING.py --data-dir ./test_data --output-dir ./results
    - uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: ./results/
```

### Pre-commit Hook Example
```bash
#!/bin/sh
# .git/hooks/pre-commit
python run_edge_case_tests.py
if [ $? -ne 0 ]; then
    echo "Edge case tests failed. Commit aborted."
    exit 1
fi
```

## Contributing

To add new test cases:

1. **Add Test Method**: Create new test method in `EdgeCaseTestSuite`
2. **Update Test Runner**: Add method call in `_run_*_tests()`  
3. **Document Test**: Update this README with test description
4. **Add Expected Results**: Define success/failure criteria

Example new test method:
```python
def _test_custom_scenario(self) -> Dict[str, Any]:
    """Test custom scenario description"""
    result = {"status": "passed", "details": {}}
    
    try:
        # Create test data
        test_data = self._create_custom_test_data()
        
        # Apply processing
        processed_data = apply_rest_exclusion_filter(test_data, "custom_test")
        
        # Validate results
        if len(processed_data) == expected_count:
            result["details"]["validation"] = "PASS"
        else:
            result["status"] = "failed"
            result["details"]["validation"] = "FAIL"
            
    except Exception as e:
        result["status"] = "error"  
        result["error"] = str(e)
    
    return result
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the performance benchmark documentation
3. Run the quick demo first to isolate issues
4. Check system requirements (Python 3.11+, sufficient memory)

## License

This testing suite is part of the Shift-Suite project and follows the same licensing terms.