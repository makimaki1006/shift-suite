# UAT Manual Testing Checklist
## Holiday Exclusion Fixes - User Acceptance Testing

### Overview
This checklist provides step-by-step instructions for manually validating the holiday exclusion functionality from a user perspective. Each test should be performed by business users who understand the operational requirements.

---

## Pre-Test Setup ✅

### Prerequisites Checklist
- [ ] Dashboard application is running and accessible
- [ ] Test Excel files are prepared and available
- [ ] Browser is compatible (Chrome, Firefox, Edge recommended)
- [ ] User has understanding of normal shift operations
- [ ] Screenshots/documentation tools are ready

### Test Data Preparation
- [ ] **Test Set 1**: Clean data with no holidays
- [ ] **Test Set 2**: Simple holidays (×, 休, 有給)
- [ ] **Test Set 3**: Complex holidays (multiple types)
- [ ] **Test Set 4**: Real operational data sample
- [ ] **Test Set 5**: Edge cases (empty cells, special characters)

---

## Core Functionality Tests

### Test Group A: Data Upload and Recognition

#### A1: Basic Holiday Recognition ✅
**Objective**: Verify system recognizes common holiday markers

**Steps**:
1. [ ] Open the dashboard
2. [ ] Upload test Excel file with simple holidays
3. [ ] Navigate to data ingestion results
4. [ ] Check system log or processing messages

**Expected Results**:
- [ ] Holiday markers (×, 休, 有給) are identified
- [ ] System displays confirmation of exclusions
- [ ] No error messages appear

**Actual Results**: _________________

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### A2: Holiday Code Mapping ✅
**Objective**: Validate specific holiday codes are properly categorized

**Steps**:
1. [ ] Upload Excel with various holiday codes (×, 休, 有, 特, 欠, 研)
2. [ ] Check processing log for holiday type identification
3. [ ] Verify each code is properly categorized

**Expected Results**:
- [ ] × → 希望休 (voluntary leave)
- [ ] 休 → 施設休 (facility closure)
- [ ] 有 → 有給 (paid leave)
- [ ] 特 → 特休 (special leave)
- [ ] 欠 → 欠勤 (absence)
- [ ] 研 → 研修 (training)

**Actual Results**: _________________

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

### Test Group B: Calculation Accuracy

#### B1: Staff Count Calculation ✅
**Objective**: Verify staff counts exclude holiday entries

**Test Data**: Excel with 5 staff, 2 on holiday
**Steps**:
1. [ ] Upload test data
2. [ ] Navigate to staff summary section
3. [ ] Check displayed staff counts
4. [ ] Manually verify by counting non-holiday entries

**Expected Results**:
- [ ] Available staff count: 3 (not 5)
- [ ] Holiday staff properly excluded from counts
- [ ] Totals are mathematically correct

**Manual Calculation**: 
- Total Staff: _____ 
- Holiday Staff: _____ 
- Expected Available: _____

**System Result**: _____

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### B2: Shortage Calculation Verification ✅
**Objective**: Shortage calculations reflect holiday exclusions

**Steps**:
1. [ ] Upload dataset with known staffing requirements
2. [ ] Note original shortage calculations
3. [ ] Add holiday entries to reduce available staff
4. [ ] Re-upload and compare shortage calculations

**Expected Results**:
- [ ] Shortage increases when staff are on holiday
- [ ] Mathematical relationship is correct
- [ ] No negative shortage values (unless overstaffed)

**Before Holiday**: Shortage = _____
**After Holiday**: Shortage = _____
**Expected Change**: _____

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

### Test Group C: Dashboard Visualization

#### C1: Heatmap Accuracy ✅
**Objective**: Heatmaps visually represent holiday exclusions

**Steps**:
1. [ ] Upload data with clear holiday patterns
2. [ ] Navigate to heatmap view
3. [ ] Identify time slots where staff are on holiday
4. [ ] Verify visual representation matches data

**Expected Results**:
- [ ] Holiday time slots show reduced staff numbers
- [ ] Color coding reflects adjusted values
- [ ] Hover/click information is accurate
- [ ] Legend and scale are appropriate

**Visual Verification**:
- Holiday slots appear: [ ] Lighter [ ] Different color [ ] Zero value
- Values match expectations: [ ] YES [ ] NO

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### C2: Summary Cards Update ✅
**Objective**: Dashboard summary statistics reflect exclusions

**Steps**:
1. [ ] Load clean dataset, note summary values
2. [ ] Load same dataset with holidays added
3. [ ] Compare summary card values
4. [ ] Verify all cards are updated consistently

**Summary Cards to Check**:
- [ ] Total Staff Available
- [ ] Average Daily Coverage
- [ ] Peak Shortage Hours
- [ ] Coverage Percentage
- [ ] Other relevant metrics

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### C3: Role-based Analysis ✅
**Objective**: Holiday exclusions work across different staff roles

**Steps**:
1. [ ] Upload multi-role dataset (nurses, caregivers, etc.)
2. [ ] Add holidays for different roles
3. [ ] Check role-specific analysis tabs
4. [ ] Verify each role's exclusions are independent

**Role Analysis Verification**:
- [ ] Nurse holidays don't affect caregiver counts
- [ ] Role-specific shortages calculated correctly
- [ ] Cross-role analysis reflects individual exclusions

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

### Test Group D: Report Generation

#### D1: Excel Report Accuracy ✅
**Objective**: Generated reports exclude holiday data

**Steps**:
1. [ ] Upload test dataset with holidays
2. [ ] Generate shortage analysis report
3. [ ] Download Excel report
4. [ ] Open report and verify holiday exclusions

**Report Verification**:
- [ ] Holiday entries not included in active staff lists
- [ ] Shortage calculations match dashboard
- [ ] Totals and subtotals are correct
- [ ] Report metadata indicates exclusion applied

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### D2: Trend Analysis Reports ✅
**Objective**: Time-series reports handle holiday exclusions

**Steps**:
1. [ ] Upload multi-week dataset with holiday patterns
2. [ ] Generate trend analysis
3. [ ] Check for holiday impact on trends
4. [ ] Verify seasonal patterns account for holidays

**Trend Verification**:
- [ ] Holiday periods show expected changes
- [ ] Trend lines are not distorted by holidays
- [ ] Comparative analysis is meaningful

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

### Test Group E: User Experience

#### E1: Error Handling ✅
**Objective**: User-friendly error messages for invalid holiday data

**Steps**:
1. [ ] Upload Excel with malformed holiday entries
2. [ ] Upload Excel with unrecognized holiday codes
3. [ ] Upload corrupted or empty files
4. [ ] Note error messages displayed

**Error Message Quality**:
- [ ] Messages are clear and understandable
- [ ] Suggested actions are provided
- [ ] Technical jargon is minimized
- [ ] User can recover from errors easily

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### E2: Workflow Efficiency ✅
**Objective**: Holiday exclusion doesn't impact user workflow

**Test Process**:
1. [ ] Time complete workflow without holidays: _____ minutes
2. [ ] Time complete workflow with holidays: _____ minutes
3. [ ] Compare user experience

**Workflow Efficiency**:
- [ ] Processing time is acceptable (< 5 minutes for large files)
- [ ] User interface remains responsive
- [ ] No unexpected delays or hangs
- [ ] Workflow steps are intuitive

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### E3: Dashboard Responsiveness ✅
**Objective**: UI performance with holiday data processing

**Steps**:
1. [ ] Load large dataset with many holidays
2. [ ] Navigate between dashboard tabs
3. [ ] Interact with visualizations
4. [ ] Monitor system responsiveness

**Performance Metrics**:
- [ ] Page loads within 10 seconds
- [ ] Tab switching is smooth
- [ ] Visualizations render properly
- [ ] No browser freezing or crashes

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

### Test Group F: Edge Cases

#### F1: Empty and Invalid Data ✅
**Objective**: System handles edge cases gracefully

**Test Cases**:
1. [ ] Empty Excel files
2. [ ] Files with only holiday entries
3. [ ] Mixed valid/invalid holiday codes
4. [ ] Special characters in holiday fields

**Expected Behavior**:
- [ ] System provides appropriate warnings
- [ ] Processing completes without crashes
- [ ] Results are logical and expected

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

#### F2: Boundary Conditions ✅
**Objective**: Testing at system limits

**Test Scenarios**:
- [ ] 100% staff on holiday (all entries excluded)
- [ ] 0% staff on holiday (no exclusions)
- [ ] Very large files (1000+ entries)
- [ ] Files with minimal data (1-2 entries)

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

## Regression Testing

### R1: Existing Functionality ✅
**Objective**: Ensure existing features still work

**Steps**:
1. [ ] Test normal operation with clean data
2. [ ] Verify all dashboard tabs function
3. [ ] Check report generation works
4. [ ] Confirm no new bugs introduced

**Regression Areas**:
- [ ] Data upload process
- [ ] Visualization rendering
- [ ] Report generation
- [ ] User interface navigation
- [ ] Performance characteristics

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

### R2: Backward Compatibility ✅
**Objective**: Older Excel formats still supported

**Steps**:
1. [ ] Test with historical Excel files
2. [ ] Try different Excel versions/formats
3. [ ] Verify consistent behavior

**Status**: [ ] PASS [ ] FAIL [ ] NOTES: _________________

---

## Final Validation

### Overall System Assessment ✅

#### Business Requirements Met:
- [ ] Holiday staff are excluded from availability calculations
- [ ] Shortage calculations are accurate
- [ ] Reports reflect real operational needs
- [ ] User workflow is efficient
- [ ] System provides clear feedback

#### Technical Requirements Met:
- [ ] No system crashes or errors
- [ ] Performance is acceptable
- [ ] Data integrity is maintained
- [ ] Integration between components works
- [ ] Error handling is appropriate

#### User Experience Quality:
- [ ] Interface is intuitive
- [ ] Error messages are helpful
- [ ] Processing time is reasonable
- [ ] Results are clearly presented
- [ ] Workflow supports business operations

---

## Sign-off Section

### Test Completion Summary

**Total Test Items**: _____
**Passed**: _____
**Failed**: _____
**Notes/Issues**: _____

### Critical Issues Identified:
1. _________________________________
2. _________________________________
3. _________________________________

### Recommendations:
1. _________________________________
2. _________________________________
3. _________________________________

### Business User Acceptance

**Tester Name**: _________________________________
**Role**: _________________________________
**Date**: _________________________________
**Signature**: _________________________________

**Acceptance Decision**: 
- [ ] **APPROVED** - System ready for production use
- [ ] **APPROVED WITH MINOR ISSUES** - Acceptable with documented workarounds
- [ ] **REJECTED** - Critical issues must be resolved before deployment

**Comments**: 
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

**Checklist Version**: 1.0  
**Last Updated**: 2025-07-22  
**Document Owner**: UAT Team