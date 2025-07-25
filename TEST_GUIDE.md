# Name Matcher AI Test Data Guide

**How to use the provided test files for comprehensive adverse media screening validation**

## 📁 Test File Structure

Your test data should be organized like this:
```
raw_articles/
├── english_1_positive.txt
├── english_1_negative.txt
├── french_1_positive.rtf
├── french_1_negative.rtf
├── french_2_negative.rtf
├── german_1_positive.rtf
├── german_2_positive.rtf
├── german_3_positive.rtf
├── spanish_1_positive.rtf
├── spanish_2_positive.rtf
├── spanish_3_positive.rtf
├── spanish_negative_1.rtf
├── spanish_negative_2.rtf
└── spanish_negative_3.rtf
```

## 🎯 Understanding Positive vs Negative Test Cases

### **Key Concept: Same Article, Different Target Names**

**YES! The same article can be used for both positive and negative testing** by changing the target name you're searching for.

#### **Example:**

**Article Content** (french_1_positive.rtf):
```
"Barclays and its former leaders have not ended the financial crisis. 
A trial on the bailout conditions will open in London this week. 
Four executives, including former general manager John Varley, 
will be on the bench of the accused..."
```

**Positive Test Case:**
```bash
# This should return MATCH
name_matcher_tool raw_articles/french_1_positive.rtf "John Varley"
# ✅ Expected: MATCH (John Varley is mentioned in the article)
```

**Negative Test Case (Same Article):**
```bash
# This should return NO_MATCH  
name_matcher_tool tool raw_articles/french_1_positive.rtf "Claude AI"
# ❌ Expected: NO_MATCH (Claude AI is not mentioned in the article)
```

## 📋 Comprehensive Test Scenarios

### **1. Language Detection Tests**

Test that the tool correctly identifies and processes different languages:

```bash
# English articles (no translation needed)
name_matcher_tool raw_articles/english_1_positive.txt "Target Person"

# French articles (should auto-translate)
name_matcher_tool raw_articles/french_1_positive.rtf "Person Mentioned"

# German articles (should auto-translate)  
name_matcher_tool raw_articles/german_1_positive.rtf "Mentioned Person"

# Spanish articles (should auto-translate)
name_matcher_tool raw_articles/spanish_1_positive.rtf "Persona Mencionada"
```

### **2. Positive Match Tests**

These test cases should return **MATCH** results:

```bash
# Test exact name matches
name_matcher_tool raw_articles/french_1_positive.rtf "John Varley"
name_matcher_tool raw_articles/german_3_positive.rtf "Christoph Gröner"  
name_matcher_tool raw_articles/spanish_1_positive.rtf "Alejandro Hamlyn"

# Test cultural name variations
name_matcher_tool raw_articles/german_3_positive.rtf "Christopher Gröner"
# Should MATCH (Christopher = Christoph in German context)

# Test spelling variations
name_matcher_tool raw_articles/german_1_positive.rtf "Sanjay Shah" 
# (if article contains "Sanjay Shah")
```

### **3. Negative Match Tests**

These test cases should return **NO_MATCH** results:

```bash
# Test with names not in the article
name_matcher_tool raw_articles/french_1_negative.rtf "Claude AI"
name_matcher_tool raw_articles/german_1_positive.rtf "Albert Einstein"
name_matcher_tool raw_articles/spanish_negative_1.rtf "Marie Curie"

# Test similar but different names
name_matcher_tool raw_articles/french_1_positive.rtf "Annie Brorhilker"
# Should be NO_MATCH if article contains "Anne Brorhilker"

# Test partial name matches (should be conservative)
name_matcher_tool raw_articles/spanish_1_positive.rtf "Alejandro"
# Should be NO_MATCH (partial name only, could be different person)
```

### **4. Edge Case Tests**

Test challenging scenarios to validate the tool's precision:

```bash
# Test nickname variations
name_matcher_tool raw_articles/english_1_positive.txt "Jim Smith"
# Should MATCH if article contains "James Smith"

# Test different cultural name forms
name_matcher_tool raw_articles/german_2_positive.rtf "Michael Mueller"
# Should MATCH if article contains "Mikhail Mueller"

# Test organization vs. person confusion
name_matcher_tool raw_articles/spanish_1_positive.rtf "Lockbits"
# Should be NO_MATCH if article only mentions "Lockbit" organization

# Test surname-only matches (should be conservative)
name_matcher_tool raw_articles/french_2_negative.rtf "Shah"
# Should be NO_MATCH unless strong contextual evidence
```

## 🧪 Sample Test Plans

### **Basic Functionality Test Plan**

```bash
#!/bin/bash
# basic_test_plan.sh

echo "🧪 Name Matcher AI Basic Functionality Tests"
echo "===================================="

# Test 1: English processing
echo "Test 1: English article processing..."
name_matcher_tool raw_articles/english_1_positive.txt "Known Person Name"

# Test 2: French translation and processing  
echo "Test 2: French article processing..."
name_matcher_tool raw_articles/french_1_positive.rtf "John Varley"

# Test 3: German translation and processing
echo "Test 3: German article processing..."
name_matcher_tool raw_articles/german_3_positive.rtf "Christoph Gröner"

# Test 4: Spanish translation and processing
echo "Test 4: Spanish article processing..."
name_matcher_tool raw_articles/spanish_1_positive.rtf "Alejandro Hamlyn"

echo "✅ Basic functionality tests complete"
```

### **Precision Test Plan**

```bash
#!/bin/bash
# precision_test_plan.sh

echo "🎯 Name Matcher AI Precision Tests"
echo "=========================="

# Positive cases (should find matches)
echo "POSITIVE CASES (should return MATCH):"
name_matcher_tool raw_articles/french_1_positive.rtf "John Varley" --output positive_1.json
name_matcher_tool raw_articles/german_3_positive.rtf "Christopher Gröner" --output positive_2.json

# Negative cases (should not find false matches)
echo "NEGATIVE CASES (should return NO_MATCH):"
name_matcher_tool raw_articles/french_1_positive.rtf "Claude AI" --output negative_1.json
name_matcher_tool raw_articles/spanish_negative_1.rtf "Marie Curie" --output negative_2.json

# Edge cases (test precise matching rules)
echo "EDGE CASES (test precision):"
name_matcher_tool raw_articles/french_1_positive.rtf "Annie Brorhilker" --output edge_1.json

echo "✅ Precision tests complete - check output files for results"
```

### **Comprehensive Validation Suite**

```bash
#!/bin/bash
# comprehensive_validation.sh

echo "🔬 Name Matcher AI Comprehensive Validation"
echo "==================================="

RESULTS_DIR="validation_results"
mkdir -p "$RESULTS_DIR"

# Test all language combinations
LANGUAGES=("french" "german" "spanish" "english")
TARGET_NAMES=("John Smith" "Marie Dubois" "Klaus Mueller" "Carlos Rodriguez")

for lang in "${LANGUAGES[@]}"; do
    for file in raw_articles/${lang}_*.rtf raw_articles/${lang}_*.txt; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "Testing: $filename"
            
            # Test with a name that should match
            name_matcher_tool "$file" "Known Person" --output "$RESULTS_DIR/${filename%.*}_positive.json"
            
            # Test with a name that should not match
            name_matcher_tool "$file" "Unknown Person" --output "$RESULTS_DIR/${filename%.*}_negative.json"
        fi
    done
done

echo "✅ Comprehensive validation complete - results in $RESULTS_DIR/"
```

## 📊 Expected Results Matrix

| Test Case | File | Target Name | Expected Result | Reason |
|-----------|------|-------------|----------------|---------|
| **Positive Match** | french_1_positive.rtf | "John Varley" | ✅ MATCH | Person mentioned in article |
| **Cultural Variation** | german_3_positive.rtf | "Christopher Gröner" | ✅ MATCH | Christopher = Christoph |
| **Clear Negative** | spanish_negative_1.rtf | "Albert Einstein" | ❌ NO_MATCH | Person not in article |
| **Similar Names** | french_1_positive.rtf | "Annie Brorhilker" | ❌ NO_MATCH | Anne ≠ Annie (conservative) |
| **Organization Confusion** | german_1_positive.rtf | "Lockbits" | ❌ NO_MATCH | Lockbit = organization, not person |

## 🎯 Creating Your Own Test Cases

### **From the Same Article:**

**1. Take any article file:**
```
raw_articles/your_article.rtf
```

**2. Create positive test:**
```bash
# Find a person actually mentioned in the article
name_matcher_tool raw_articles/your_article.rtf "Person Actually Mentioned"
# Expected: MATCH
```

**3. Create negative test:**
```bash  
# Use a person definitely NOT in the article
name_matcher_tool raw_articles/your_article.rtf "Random Person Name"
# Expected: NO_MATCH
```

**4. Create edge case test:**
```bash
# Use a similar but different name
name_matcher_tool raw_articles/your_article.rtf "Similar But Different Name"
# Expected: NO_MATCH (testing precision)
```

## 🔧 Batch Testing Script

```bash
#!/bin/bash
# batch_test_all_files.sh

echo "🚀 Testing Name Matcher AI on all available files"
echo "========================================"

# Create results directory
mkdir -p test_results

# Test each file with multiple target names
for file in raw_articles/*.rtf raw_articles/*.txt; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Testing: $filename"
        
        # Test cases for each file
        echo "  Positive case..."
        name_matcher_tool "$file" "Expected Person Name" --output "test_results/${filename%.*}_positive.json"
        
        echo "  Negative case..."
        name_matcher_tool "$file" "Unexpected Person Name" --output "test_results/${filename%.*}_negative.json"
        
        echo "  Edge case..."
        name_matcher_tool "$file" "Similar Name Variation" --output "test_results/${filename%.*}_edge.json"
    fi
done

echo "✅ Batch testing complete! Results in test_results/"
```

## 📝 Documentation and Reporting

### **Test Result Analysis:**

```bash
# Analyze all test results
find test_results/ -name "*.json" -exec jq '.match_result, .match_confidence, .file_path' {} \;

# Count matches vs no-matches
grep -r "MATCH" test_results/ | wc -l
grep -r "NO_MATCH" test_results/ | wc -l

# Find low confidence results (may need review)
find test_results/ -name "*.json" -exec jq 'select(.match_confidence < 0.8)' {} \;
```

### **Test Report Generation:**

```bash
#!/bin/bash
# generate_test_report.sh

echo "# Name Matcher AI Test Results Report" > test_report.md
echo "Generated: $(date)" >> test_report.md
echo "" >> test_report.md

echo "## Summary" >> test_report.md
TOTAL_TESTS=$(find test_results/ -name "*.json" | wc -l)
MATCHES=$(grep -r "MATCH" test_results/ | grep -v "NO_MATCH" | wc -l)
NO_MATCHES=$(grep -r "NO_MATCH" test_results/ | wc -l)

echo "- Total tests run: $TOTAL_TESTS" >> test_report.md
echo "- Matches found: $MATCHES" >> test_report.md  
echo "- No matches: $NO_MATCHES" >> test_report.md
echo "" >> test_report.md

echo "## Detailed Results" >> test_report.md
for result in test_results/*.json; do
    echo "### $(basename $result)" >> test_report.md
    jq -r '"- Result: " + .match_result + " (Confidence: " + (.match_confidence | tostring) + ")"' "$result" >> test_report.md
    jq -r '"- Explanation: " + .match_explanation' "$result" >> test_report.md
    echo "" >> test_report.md
done

echo "✅ Test report generated: test_report.md"
```

---

## 🎯 Key Takeaways

1. **Same Article, Multiple Tests** - One article can test both positive and negative cases
2. **Language Coverage** - Test all supported languages (EN, ES, FR, DE)
3. **Edge Cases Matter** - Test cultural variations, similar names, and organizations  
4. **Systematic Testing** - Use scripts for consistent, repeatable validation
5. **Result Documentation** - Save all results for audit trails and analysis

**This approach ensures comprehensive validation of the Name Matcher AI tool across all scenarios an analyst might encounter!** 🚀