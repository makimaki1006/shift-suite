# User Acceptance Testing (UAT) Test Plan
## Holiday Exclusion Fixes Validation

### 1. Overview

This User Acceptance Testing (UAT) plan validates the holiday exclusion fixes implemented in the Shift Suite system. The primary objective is to ensure that holiday/leave entries are correctly excluded from calculations and visualizations across all system components.

#### 1.1 Scope of Testing

**In Scope:**
- Holiday exclusion functionality in data ingestion
- Accurate staff shortage calculations after exclusion
- Dashboard visualizations reflecting exclusion
- Heatmap accuracy with holiday data filtered
- Report generation with correct metrics
- End-to-end workflow validation

**Out of Scope:**
- Performance optimization testing
- Security penetration testing
- Cross-browser compatibility (UI testing)

#### 1.2 Business Requirements Validated

1. **Primary Requirement**: Staff marked as on holiday/leave should not count toward availability calculations
2. **Secondary Requirement**: System should maintain data integrity when excluding holiday entries
3. **Tertiary Requirement**: Users should see accurate shortage calculations reflecting actual working staff

### 2. Test Environment Setup

#### 2.1 Prerequisites

- Python environment with all dependencies installed
- Sample Excel files with various holiday patterns
- Dashboard application accessible
- Test data sets prepared with known holiday patterns

#### 2.2 Test Data Categories

1. **Clean Test Data**: No holidays/leaves
2. **Simple Holiday Data**: Basic holiday patterns (×, 休, 有給)
3. **Complex Holiday Data**: Multiple holiday types, partial days
4. **Edge Case Data**: Empty entries, special characters, overnight shifts with holidays
5. **Real-world Data**: Actual production-like data sets

### 3. Test Scenarios

#### 3.1 Data Ingestion Testing

##### Scenario 1: Basic Holiday Recognition
**Objective**: Verify system recognizes common holiday markers
**Test Data**: Excel file with staff entries containing ×, 休, 有給, 欠勤
**Expected Result**: Holiday entries excluded from calculations

##### Scenario 2: Holiday Code Recognition  
**Objective**: Validate recognition of specific holiday codes
**Test Data**: Excel with codes defined in LEAVE_CODES mapping
**Expected Result**: All defined leave codes properly categorized

##### Scenario 3: Empty/NaN Handling
**Objective**: Ensure empty cells don't break holiday exclusion
**Test Data**: Mixed empty cells and holiday markers
**Expected Result**: System handles gracefully without errors

#### 3.2 Business Logic Validation

##### Scenario 4: Shortage Calculation Accuracy
**Objective**: Verify shortage calculations exclude holiday staff
**Test Data**: Known staffing pattern with calculable shortages
**Steps**:
1. Load data with holiday entries
2. Calculate expected shortage manually (excluding holidays)
3. Compare with system calculation
**Expected Result**: Manual and system calculations match within 5% tolerance

##### Scenario 5: Multi-day Holiday Patterns
**Objective**: Test consecutive holiday handling
**Test Data**: Staff with multiple consecutive holiday days
**Expected Result**: All holiday days excluded consistently

##### Scenario 6: Partial Day Exclusions
**Objective**: Handle partial holiday scenarios
**Test Data**: P有 (partial paid leave) entries
**Expected Result**: Partial exclusion correctly applied

#### 3.3 Dashboard Visualization Testing

##### Scenario 7: Heatmap Accuracy
**Objective**: Heatmaps reflect holiday exclusions
**Test Data**: Dataset with known holiday patterns
**Steps**:
1. Generate heatmap
2. Verify holiday slots show zero or reduced values
3. Check color coding matches adjusted values
**Expected Result**: Heatmap visually represents post-exclusion data

##### Scenario 8: Summary Statistics
**Objective**: Dashboard summaries reflect exclusions
**Test Data**: Controlled dataset with known metrics
**Expected Result**: All summary cards show adjusted values

##### Scenario 9: Role-based Analysis
**Objective**: Holiday exclusions work across different roles
**Test Data**: Multi-role dataset with varied holiday patterns
**Expected Result**: Each role's analysis excludes respective holidays

#### 3.4 Report Generation Testing

##### Scenario 10: Excel Report Accuracy
**Objective**: Generated reports exclude holiday data
**Test Data**: Standard dataset with holidays
**Steps**:
1. Generate shortage report
2. Verify excluded entries not in report
3. Check totals reflect exclusions
**Expected Result**: Reports mathematically consistent with exclusions

##### Scenario 11: Time Series Reports
**Objective**: Time-based reports handle holiday exclusions
**Test Data**: Multi-week dataset with holiday patterns
**Expected Result**: Trend analysis reflects actual working patterns

#### 3.5 Regression Testing

##### Scenario 12: Existing Functionality Preservation
**Objective**: Ensure holiday exclusion doesn't break existing features
**Test Data**: Historical test datasets
**Expected Result**: All existing functionality operates normally

##### Scenario 13: Non-holiday Data Processing
**Objective**: Normal data processing unaffected
**Test Data**: Clean dataset without holidays
**Expected Result**: Processing identical to pre-fix behavior

#### 3.6 End-to-End Workflow Testing

##### Scenario 14: Complete Workflow Validation
**Objective**: Full process from Excel upload to final analysis
**Steps**:
1. Prepare Excel file with known holiday patterns
2. Upload through dashboard
3. Navigate through all analysis tabs
4. Generate and download reports
5. Verify consistency across all outputs
**Expected Result**: Consistent holiday exclusion throughout entire workflow

##### Scenario 15: Multi-user Scenario Simulation
**Objective**: Concurrent usage with different datasets
**Test Data**: Multiple Excel files with different holiday patterns
**Expected Result**: No cross-contamination between datasets

### 4. User Experience Testing

#### 4.1 Usability Validation

##### Scenario 16: Dashboard Responsiveness
**Objective**: UI remains responsive with holiday data
**Test Data**: Large dataset with many holidays
**Expected Result**: Dashboard loads and responds within acceptable time limits

##### Scenario 17: Error Handling from User Perspective
**Objective**: User-friendly error messages for invalid holiday data
**Test Data**: Malformed Excel with invalid holiday entries
**Expected Result**: Clear, actionable error messages displayed

##### Scenario 18: Workflow Efficiency
**Objective**: Holiday exclusion doesn't impact user workflow efficiency
**Test Data**: Standard operational dataset
**Expected Result**: User workflow completion time unchanged or improved

### 5. Performance Testing

#### 5.1 Processing Time Validation

##### Scenario 19: Large Dataset Performance
**Objective**: Holiday exclusion processing scales appropriately
**Test Data**: Large Excel file (1000+ entries) with 30% holiday entries
**Expected Result**: Processing completes within reasonable time (< 5 minutes)

##### Scenario 20: Memory Usage Validation
**Objective**: Memory consumption remains acceptable
**Test Data**: Multiple large datasets processed sequentially
**Expected Result**: No memory leaks, stable memory usage

### 6. Pass/Fail Criteria

#### 6.1 Critical Pass Criteria (Must Pass)
- All holiday markers correctly identified and excluded
- Shortage calculations mathematically accurate (within 5% tolerance)
- No system crashes or unhandled exceptions
- Data integrity maintained throughout process
- Reports generated successfully with correct exclusions

#### 6.2 Important Pass Criteria (Should Pass)
- Dashboard visualization accurately reflects exclusions
- User workflow efficiency maintained or improved
- Error messages clear and actionable
- Processing completes within acceptable time limits

#### 6.3 Nice-to-Have Pass Criteria (Could Pass)
- Advanced holiday pattern recognition
- Performance improvements over baseline
- Enhanced user interface feedback

### 7. Test Execution Strategy

#### 7.1 Phase 1: Automated Core Functionality
- Run automated test scenarios 1-15
- Validate core business logic
- Generate baseline metrics

#### 7.2 Phase 2: Manual User Experience
- Execute scenarios 16-18 manually
- Document user interaction issues
- Collect usability feedback

#### 7.3 Phase 3: Performance & Scale
- Execute scenarios 19-20
- Monitor system resources
- Document performance characteristics

#### 7.4 Phase 4: Regression Validation  
- Re-run historical test suites
- Validate no functionality degradation
- Confirm backward compatibility

### 8. Risk Assessment

#### 8.1 High Risk Areas
- Complex holiday pattern recognition
- Multi-day consecutive holiday handling
- Integration between dashboard components

#### 8.2 Mitigation Strategies
- Comprehensive test data coverage
- Manual verification of critical calculations
- Multiple dataset validation approaches

### 9. Success Metrics

#### 9.1 Quantitative Metrics
- Test case pass rate: > 95%
- Calculation accuracy: Within 5% of manual calculation
- Processing time: < 5 minutes for large datasets
- Zero critical system failures

#### 9.2 Qualitative Metrics
- User workflow improvement
- Clear error messaging
- Consistent behavior across components
- Maintainable and understandable code

### 10. Test Documentation Requirements

- Detailed test execution logs
- Screenshots of dashboard states
- Calculation verification spreadsheets
- Performance monitoring data
- User experience feedback forms

### 11. Post-UAT Activities

#### 11.1 Issue Resolution
- Categorize and prioritize identified issues
- Create bug fix implementation plan
- Retest after fixes applied

#### 11.2 Go-Live Preparation
- Final validation with production-like data
- User training material updates
- Deployment checklist verification

### 12. Approval Criteria

UAT is considered successful when:
- All critical pass criteria met
- 95% of important pass criteria met
- No unresolved critical or high-priority defects
- User acceptance sign-off obtained
- Performance benchmarks achieved

### 13. Testing Team Responsibilities

#### 13.1 Test Coordinator
- Overall test execution oversight
- Result compilation and reporting
- Issue escalation management

#### 13.2 Business User Representatives
- Scenario validation from business perspective
- User experience feedback
- Final acceptance decision

#### 13.3 Technical Team
- Test environment setup
- Automated test execution
- Defect resolution support

---

**Document Version**: 1.0  
**Last Updated**: 2025-07-22  
**Next Review**: Post-UAT completion