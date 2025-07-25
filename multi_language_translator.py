#!/usr/bin/env python3
"""
Unified Multi-Language Translator
Handles RTF/TXT files in Spanish, French, German and translates to English
Then passes to NER + LLM pipeline for name matching
"""
import os
import argparse
from striprtf.striprtf import rtf_to_text
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect

class UnifiedTranslator:
    """
    Unified language translator
    """
    def __init__(self):
        # Translation models for each language
        self.models = {}
        self.tokenizers = {}
        
        # Language model mapping
        self.language_models = {
            'es': 'Helsinki-NLP/opus-mt-es-en',  # Spanish
            'fr': 'Helsinki-NLP/opus-mt-fr-en',  # French  
            'de': 'Helsinki-NLP/opus-mt-de-en'   # German
        }
        
        print("Initializing language models (lazy loading)...")
    
    def load_model(self, lang_code):
        """Lazy load translation model for specific language"""
        if lang_code not in self.models:
            if lang_code not in self.language_models:
                raise ValueError(f"Unsupported language: {lang_code}")
            
            model_name = self.language_models[lang_code]
            print(f"Loading {lang_code}→en translation model: {model_name}")
            
            self.tokenizers[lang_code] = MarianTokenizer.from_pretrained(model_name)
            self.models[lang_code] = MarianMTModel.from_pretrained(model_name)
            
            print(f"✅ {lang_code}→en model loaded successfully!")
    
    def read_file(self, file_path):
        """Read RTF or TXT file and extract plain text with robust error handling"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.rtf':
            return self._read_rtf_file(file_path)
        elif ext == '.txt':
            return self._read_txt_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Use .rtf or .txt")
    
    def _read_rtf_file(self, file_path):
        """Read RTF file with multiple encoding fallbacks"""        
        # Method 1: Try striprtf with UTF-8
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return rtf_to_text(content).strip()
        except Exception as e:
            print(f"striprtf with UTF-8 failed: {e}, trying latin-1...")
        
        # Method 2: Try striprtf with latin-1 encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
            return rtf_to_text(content).strip()
        except Exception as e:
            print(f"striprtf with latin-1 failed: {e}, trying cp1252...")
        
        # Method 3: Try striprtf with cp1252 encoding (Windows)
        try:
            with open(file_path, 'r', encoding='cp1252') as file:
                content = file.read()
            return rtf_to_text(content).strip()
        except Exception as e:
            # Method 4: Try reading as binary and decode manually
            try:
                with open(file_path, 'rb') as file:
                    content = file.read().decode('utf-8', errors='ignore')
                return rtf_to_text(content).strip()
            except Exception as final_e:
                raise ValueError(f"All RTF parsing methods failed for {file_path}: {final_e}")
    
    def _read_txt_file(self, file_path):
        """Read TXT file with encoding fallbacks"""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read().strip()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not decode text file {file_path} with any encoding")
    
    def detect_language(self, text):
        """Detect language of input text"""
        try:
            detected = detect(text)
            print(f"Detected language: {detected}")
            
            # Map common language codes
            if detected in ['es', 'fr', 'de']:
                return detected
            elif detected == 'en':
                return 'en'  # Already English
            else:
                print(f"Warning: Unsupported language '{detected}', assuming English")
                return 'en'
                
        except Exception as e:
            print(f"Language detection failed: {e}, assuming English")
            return 'en'
    
    def translate_to_english(self, text, source_lang):
        """Translate text to English if needed"""
        if source_lang == 'en':
            print("Text is already in English, no translation needed")
            return text
        
        if source_lang not in self.language_models:
            raise ValueError(f"Translation not supported for language: {source_lang}")
        
        # Load model if not already loaded
        self.load_model(source_lang)
        
        # Tokenize and translate
        tokenizer = self.tokenizers[source_lang]
        model = self.models[source_lang]
        
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        translated = model.generate(**inputs)
        english_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        
        print(f"✅ Translation completed: {source_lang}→en")
        return english_text
    
    def ner_llm_pipeline(self, english_text, target_name):
        """Placeholder for NER + LLM pipeline"""
        print(f"\n{'='*50}")
        print("🔍 NER + LLM PIPELINE")
        print(f"{'='*50}")
        print(f"Target Name: {target_name}")
        print(f"English Text Length: {len(english_text)} chars")
        print(f"Text Preview: {english_text[:200]}...")
        
        # TODO: Implement actual NER + LLM matching logic here
        print("\n⚠️  NER + LLM pipeline not implemented yet!")
        print("This is where we'll:")
        print("1. Extract person entities using spaCy NER")
        print("2. Use LLM to determine if target_name matches article content")
        print("3. Return MATCH/NO_MATCH with explanation")
        
        return {
            'result': 'PENDING_IMPLEMENTATION',
            'confidence': 0.0,
            'explanation': 'NER + LLM pipeline not implemented yet'
        }
    
    def process(self, file_path, target_name):
        """Main processing pipeline"""
        print(f"\n{'='*60}")
        print(f"PROCESSING: {os.path.basename(file_path)}")
        print(f"TARGET: {target_name}")
        print(f"{'='*60}")
        
        # Step 1: Read file
        print("📖 Reading file...")
        text = self.read_file(file_path)
        print(f"✅ File read successfully ({len(text)} characters)")
        
        # Step 2: Detect language
        print("\n🔍 Detecting language...")
        detected_lang = self.detect_language(text)
        
        # Step 3: Translate to English
        print(f"\n🌐 Translating {detected_lang}→en...")
        english_text = self.translate_to_english(text, detected_lang)

        # Display translation results clearly
        print("\n📝 TRANSLATION RESULTS")
        print("-" * 50)
        print(f"Original Language: {detected_lang}")
        print(f"Original Text Length: {len(text)} characters")
        print(f"Translated Text Length: {len(english_text)} characters")

        print("\n📖 ORIGINAL TEXT:")
        print(f"{'='*60}")
        print(text[:500] + "..." if len(text) > 500 else text)
        print(f"{'='*60}")

        print("\n📝 TRANSLATED TEXT:")
        print(f"{'='*60}")
        print(english_text[:500] + "..." if len(english_text) > 500 else english_text)
        print(f"{'='*60}")

        print("✅ Translation completed successfully")
        
        # Step 4: NER + LLM Pipeline
        result = self.ner_llm_pipeline(english_text, target_name)
        
        return {
            'file_path': file_path,
            'target_name': target_name,
            'detected_language': detected_lang,
            'original_text': text,
            'translated_text': english_text,
            'pipeline_result': result
        }

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='Multi-language adverse media screening tool')
    parser.add_argument('file_path', help='Path to RTF or TXT file')
    parser.add_argument('target_name', help='Name to search for in the article')
    
    args = parser.parse_args()
    
    # Process the file
    translator = UnifiedTranslator()
    result = translator.process(args.file_path, args.target_name)
    
    print(f"\n{'='*60}")
    print("📋 FINAL RESULT")
    print(f"{'='*60}")
    print(f"File: {result['file_path']}")
    print(f"Target: {result['target_name']}")
    print(f"Language: {result['detected_language']}")
    print(f"Result: {result['pipeline_result']['result']}")
    print(f"Explanation: {result['pipeline_result']['explanation']}")

if __name__ == "__main__":
    main()