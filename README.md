# Name Matcher: AI Adverse Media Screening Tool

**Regulatory-compliant name matching for adverse media articles in multiple languages**

## 📋 What This Tool Does

The Name matcher AI tool helps analysts quickly determine if a person's name appears in adverse media articles. It:

- ✅ **Reads articles** in English, Spanish, French, and German (TXT and RTF files)
- ✅ **Translates foreign articles** to English automatically
- ✅ **Finds person names** using advanced AI entity recognition
- ✅ **Matches names intelligently** considering nicknames, spelling variations, and cultural differences
- ✅ **Provides clear explanations** for regulatory compliance and audit trails
- ✅ **Avoids false negatives** - designed to never miss a real match

## 🎯 For Analysts (Non-Technical Users)

### Quick Start Guide

1. **Get the tool** - Ask your IT team to install it following the Technical Setup section below
2. **Get your OpenAI API key** - Your organization should provide this
3. **Run the tool** - Use the simple commands below

### Basic Usage

```bash
# Simple check - does "John Smith" appear in this article?
name_matcher_tool my_article.txt "John Smith"

# Check with detailed output (recommended for learning)
name_matcher_tool my_article.txt "John Smith" --debug

# Save results to a file for records
name_matcher_tool my_article.txt "John Smith" --output john_smith_results.json
```

### Understanding Results

The tool gives you clear answers:

**✅ MATCH Found:**
```
🎯 MATCH DECISION
✅ RESULT: MATCH
📊 CONFIDENCE: 0.95
⚠️  ACTION: Human analyst should review this potential match

💭 EXPLANATION: Exact name match found: 'John Smith' matches 'John Smith' in article.
```
👉 **Action:** Review the article manually - there's likely a match

**❌ NO MATCH Found:**
```
🎯 MATCH DECISION  
❌ RESULT: NO_MATCH
📊 CONFIDENCE: 0.90
✅ ACTION: Article can be discarded - no match found

💭 EXPLANATION: No sufficiently similar names found for 'John Smith' among persons in article.
```
👉 **Action:** Article can be discarded - no relevant person found

### File Types Supported

- ✅ **TXT files** - Plain text articles
- ✅ **RTF files** - Rich text format documents  
- 📋 **PDF files** - Can be added with additional setup

### Article Length Guidelines

- ✅ Optimal: Up to 3,000 words (~2,000 characters recommended)
- ⚠️ Supported: 3,000-10,000 words (may be summarized for processing)
- 📋 Very Long: 10,000+ words (full entity extraction, but LLM may see truncated content)

For best results: Keep articles focused and under 3,000 words. 
The tool extracts entities from the full text regardless of length, but very long articles may have their content summarized when sent to the AI matching component.

### Languages Supported

- 🇺🇸 **English** - Direct processing
- 🇪🇸 **Spanish** - Auto-translated to English
- 🇫🇷 **French** - Auto-translated to English  
- 🇩🇪 **German** - Auto-translated to English

### Real Examples

```bash
# Check if Christopher Gröner appears in a German article
name_matcher_tool german_insolvency_article.rtf "Christopher Gröner"
# Result: MATCH (recognizes Christopher = Christoph in German)

# Check if Anne Brorhilker appears in French article  
name_matcher_tool french_tax_article.rtf "Annie Brorhilker"
# Result: NO_MATCH (Anne ≠ Annie, different names)

# Check Spanish article with debug details
name_matcher_tool spanish_fraud_article.txt "Carlos Rodriguez" --debug
```

### Getting Help

```bash
# See all available options
name_matcher_tool --help

# Contact your IT team if you get error messages
# Common issues: missing API key, file not found, wrong file format
```

---

## 🔧 Technical Setup (For IT Teams)

### System Requirements

- **Python 3.8+** 
- **16GB RAM minimum** (for AI models)
- **Internet connection** (for OpenAI API)
- **OpenAI API key** with GPT-3.5/GPT-4 access

### Installation

#### Step 1: Download and Setup
```bash
# Clone or download the Name matcher AI tool files
git clone [repository-url] name-matcher
cd name-matcher

# Create Python virtual environment (recommended)
python3 -m venv virtual_env
source virtual_env/bin/activate  # On Windows: virtual_env_env\Scripts\activate
```

#### Step 2: Install Dependencies
```bash
# Install required Python packages
pip install -r requirements.txt

# Download language models (this may take several minutes)
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm  
python -m spacy download fr_core_news_sm
python -m spacy download de_core_news_sm
```

#### Step 3: Setup the Executable
```bash
# Make the tool executable
chmod +x name_matcher_tool

# Test installation
./name_matcher_tool --help
```

#### Step 4: Make Globally Available (Optional)
```bash
# Add to user's PATH (recommended)
echo 'export PATH="$PATH:'$(pwd)'"' >> ~/.bashrc
source ~/.bashrc

# OR install system-wide (requires admin)
sudo cp name_matcher_tool /usr/local/bin/
sudo chmod +x /usr/local/bin/name_matcher_tool
```

#### Step 5: Configure API Key
```bash
# Set environment variable (recommended)
echo 'export OPENAI_API_KEY="sk-proj-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# OR create a .env file in the tool directory
echo "OPENAI_API_KEY=sk-proj-your-api-key-here" > .env
```

### Dependencies (requirements.txt)
```
openai>=1.0.0
transformers>=4.20.0
torch>=1.12.0
spacy>=3.4.0
langdetect>=1.0.9
striprtf>=0.0.26
python-dotenv>=0.19.0
```

---

## 📖 Advanced Usage

### Command Line Options

```bash
name_matcher_tool [FILE] [TARGET_NAME] [OPTIONS]

Required:
  FILE          Path to article file (TXT or RTF)
  TARGET_NAME   Name of person to search for (in quotes)

Options:
  --debug       Show detailed processing steps
  --api-key     OpenAI API key (if not using environment variable)
  --output      Save results to JSON file
  --model       OpenAI model to use (default: gpt-3.5-turbo)
  --help        Show help message
```

### Batch Processing Script

For processing multiple files, create a batch script:

```bash
#!/bin/bash
# batch_process.sh - Process multiple articles for the same person

TARGET_NAME="John Smith"
OUTPUT_DIR="results"

mkdir -p "$OUTPUT_DIR"

for file in raw_articles/*.txt raw_articles/*.rtf; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Processing: $filename"
        name_matcher_tool "$file" "$TARGET_NAME" --output "$OUTPUT_DIR/${filename%.*}_results.json"
    fi
done

echo "Batch processing complete. Results in $OUTPUT_DIR/"
```

### Integration with Other Systems

The tool outputs structured JSON when using `--output`:

```json
{
  "file_path": "article.txt",
  "target_name": "John Smith",
  "detected_language": "en",
  "match_result": "MATCH",
  "match_confidence": 0.95,
  "match_explanation": "Exact name match found...",
  "match_method": "OpenAI gpt-3.5-turbo",
  "entities_analyzed": ["John Smith", "Mary Johnson"],
  "pipeline_version": "NAME_MATCHER_AI_v1.0"
}
```

---

## 🔍 How It Works (Technical Details)

### Processing Pipeline

1. **File Reading** - Supports TXT and RTF formats with encoding detection
2. **Language Detection** - Automatically identifies article language  
3. **Translation** - Translates foreign articles to English using Helsinki-NLP models
4. **Entity Extraction** - Uses spaCy NER models to find person names
5. **LLM Matching** - Advanced name matching using OpenAI GPT with regulatory prompts
6. **Result Generation** - Structured output with confidence scores and explanations

### Name Matching Intelligence

The tool handles complex name variations:

- ✅ **Exact matches** - "John Smith" = "John Smith"
- ✅ **Common nicknames** - "Jim Smith" = "James Smith"  
- ✅ **Spelling variations** - "Mohammed Ali" = "Mohammad Ali"
- ✅ **Cultural variations** - "Christopher" = "Christoph" (German)
- ❌ **Different names** - "Anne" ≠ "Annie" (conservative approach)

### Regulatory Compliance Features

- **Conservative matching** - Designed to avoid false negatives
- **Detailed explanations** - Every decision includes reasoning
- **Confidence scores** - Quantified certainty levels
- **Audit trails** - Complete processing logs available
- **Language transparency** - Shows original and translated text

---

## 🛠️ Troubleshooting

### Common Issues

**❌ "OpenAI API key not found"**
```bash
# Solution: Set your API key
export OPENAI_API_KEY="sk-proj-your-key-here"
# Or use --api-key flag
name_matcher_tool article.txt "Name" --api-key sk-proj-your-key-here
```

**❌ "File not found"**
```bash
# Solution: Check file path and ensure file exists
ls -la my_article.txt
# Use full path if needed
name_matcher_tool /full/path/to/article.txt "Name"
```

**❌ "spaCy model not found"**
```bash
# Solution: Install required language models
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm
```

**❌ "ModuleNotFoundError"**
```bash
# Solution: Install dependencies in virtual environment
pip install -r requirements.txt
```

**❌ "Permission denied"**
```bash
# Solution: Make script executable
chmod +x name_matcher_tool
```

### Debug Mode

Use `--debug` to see detailed processing:

```bash
name_matcher_tool article.txt "John Smith" --debug
```

This shows:
- File reading and language detection
- Translation process
- Entity extraction results  
- LLM reasoning process
- Final decision logic

### Support

For technical issues:
1. Run with `--debug` flag to see detailed error messages
2. Check that all dependencies are installed
3. Verify OpenAI API key is valid and has sufficient credits
4. Ensure input file is in supported format (TXT or RTF)

---

## 📄 License and Usage

This tool is designed for regulatory compliance in financial services adverse media screening. 

**Important Notes:**
- Requires valid OpenAI API key (costs apply per API call)
- Designed for regulated financial services compliance
- Conservative approach prioritizes avoiding false negatives
- Human review recommended for all MATCH results
- Not suitable for high-volume automated processing without human oversight

---

## 🚀 Version History

**v1.0** - Initial release
- Multi-language support (EN, ES, FR, DE)
- OpenAI GPT integration
- Regulatory-compliant prompt engineering
- TXT and RTF file support
- Command-line interface