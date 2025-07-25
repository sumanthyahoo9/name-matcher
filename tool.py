#!/usr/bin/env python3
"""
Complete Name Matcher AI Adverse Media Screening Pipeline
Command-line interface for the full Translation → NER → LLM pipeline

Usage:
    python name_matcher_pipeline.py <file_path> <target_name> [--debug] [--api-key YOUR_KEY]

Example:
    python name_matcher_pipeline.py data/my_text.txt "John Smith" --debug
    python name_matcher_pipeline.py data/french_article.rtf "Marie Dubois" --api-key sk-...
"""

import argparse
import sys
import os
import json
import traceback

# Import our pipeline components - CORRECTED IMPORTS
try:
    from ner_pipeline_overall import LLMReadyPipeline  # Changed from MultilingualIntegratedPipeline
    from llm_matching import RegulatoryLLMMatcher      # Changed from clean_llm_matcher
except ImportError as e:
    print(f"❌ Error importing pipeline components: {e}")
    print("Make sure ner_pipeline_overall.py and llm_matching.py are in the same directory")
    print("Required classes: LLMReadyPipeline, RegulatoryLLMMatcher")
    sys.exit(1)

class NameMatcherPipeline:
    """Complete Name Matcher AI adverse media screening pipeline"""
    
    def __init__(self, openai_api_key=None, debug=False):
        """Initialize the complete pipeline"""
        self.debug = debug
        
        if self.debug:
            print("🚀 Initializing Name Matcher AI Pipeline...")
        
        # Initialize NER pipeline - CORRECTED CLASS NAME
        try:
            self.ner_pipeline = LLMReadyPipeline()  # Changed from MultilingualIntegratedPipeline
            if self.debug:
                print("✅ NER Pipeline initialized")
        except Exception as e:
            print(f"❌ Failed to initialize NER pipeline: {e}")
            raise
        
        # Initialize LLM matcher
        try:
            self.llm_matcher = RegulatoryLLMMatcher(api_key=openai_api_key)
            if self.debug:
                print("✅ LLM Matcher initialized")
        except Exception as e:
            print(f"❌ Failed to initialize LLM matcher: {e}")
            raise
        
        if self.debug:
            print("🎯 Pipeline ready for adverse media screening!")
    
    def process_file(self, file_path, target_name):
        """
        Process a file through the complete pipeline
        
        Args:
            file_path: Path to text/RTF file
            target_name: Name to search for
            
        Returns:
            dict: Complete results with all pipeline stages
        """
        if self.debug:
            print(f"\n{'='*80}")
            print("📋 NAME MATCHER AI ADVERSE MEDIA SCREENING")
            print(f"{'='*80}")
            print(f"File: {file_path}")
            print(f"Target: {target_name}")
            print(f"{'='*80}")
        
        # Step 1: NER Pipeline (Translation + Entity Extraction) - CORRECTED METHOD NAME
        if self.debug:
            print("\n🔄 STEP 1: Running NER Pipeline...")
        
        try:
            # Changed method name to match actual implementation
            ner_result = self.ner_pipeline.process_for_llm(file_path, target_name, debug=self.debug)
            
            # Extract data from the result structure
            ner_data = {
                'target_name': ner_result['target_name'],
                'original_text': ner_result['original_text'],
                'translated_text': ner_result['translated_text'],
                'detected_language': ner_result['detected_language'],
                'entities': self._convert_entities_to_person_format(ner_result['extraction_result']['all_entities'])
            }
            
            if self.debug:
                print("✅ NER Pipeline complete:")
                print(f"   Language: {ner_data['detected_language']}")
                print(f"   Original text: {len(ner_data['original_text'])} chars")
                print(f"   Translated text: {len(ner_data['translated_text'])} chars")
                print(f"   Entities extracted: {len(ner_data['entities'])}")
                
                # Show top person entities
                person_entities = [e for e in ner_data['entities'] 
                                 if any(keyword in e.source.lower() 
                                       for keyword in ['person', 'per', 'people'])]
                if person_entities:
                    print("   Person entities found:")
                    for i, entity in enumerate(person_entities[:5], 1):
                        print(f"     {i}. {entity.name} (conf: {entity.confidence:.2f})")
                
        except Exception as e:
            print(f"❌ NER Pipeline failed: {e}")
            if self.debug:
                traceback.print_exc()
            return {"error": f"NER Pipeline failed: {e}"}
        
        # Step 2: LLM Matching
        if self.debug:
            print(f"\n🔄 STEP 2: Running LLM Matching...")
        
        try:
            llm_result = self.llm_matcher.match_with_full_context(
                target_name=ner_data['target_name'],
                original_text=ner_data['original_text'],
                translated_text=ner_data['translated_text'],
                entities=ner_data['entities'],
                detected_language=ner_data['detected_language'],
                debug=self.debug
            )
            
            if self.debug:
                print("✅ LLM Matching complete:")
                print(f"   Result: {llm_result.result}")
                print(f"   Confidence: {llm_result.confidence:.2f}")
                print(f"   Method: {llm_result.method}")
        
        except Exception as e:
            print(f"❌ LLM Matching failed: {e}")
            if self.debug:
                traceback.print_exc()
            return {"error": f"LLM Matching failed: {e}"}
        
        # Step 3: Compile Final Results
        final_results = {
            "file_path": file_path,
            "target_name": target_name,
            "detected_language": ner_data['detected_language'],
            "original_text_length": len(ner_data['original_text']),
            "translated_text_length": len(ner_data['translated_text']),
            "entities_found": len(ner_data['entities']),
            "person_entities_found": len([e for e in ner_data['entities'] 
                                        if any(keyword in e.source.lower() 
                                              for keyword in ['person', 'per'])]),
            "match_result": llm_result.result,
            "match_confidence": llm_result.confidence,
            "match_explanation": llm_result.explanation,
            "match_method": llm_result.method,
            "entities_analyzed": llm_result.entities_analyzed,
            "pipeline_version": "NameMatcher_AI_v1.0"
        }
        
        return final_results
    
    def _convert_entities_to_person_format(self, entities):
        """Convert Entity objects to PersonEntity format expected by LLM matcher"""
        from llm_matching import PersonEntity
        
        converted_entities = []
        for entity in entities:
            person_entity = PersonEntity(
                name=entity.name,
                confidence=entity.confidence,
                source=entity.source,
                context=entity.context,
                start_char=getattr(entity, 'start_char', 0),
                end_char=getattr(entity, 'end_char', 0)
            )
            converted_entities.append(person_entity)
        
        return converted_entities
    
    def print_final_summary(self, results):
        """Print a clean final summary"""
        print(f"\n{'='*80}")
        print("📊 FINAL NAME MATCHER AI SCREENING RESULTS")
        print(f"{'='*80}")
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        # Basic info
        print(f"📁 File: {results['file_path']}")
        print(f"🎯 Target: {results['target_name']}")
        print(f"🌐 Language: {results['detected_language']}")
        print(f"📝 Text processed: {results['original_text_length']} → {results['translated_text_length']} chars")
        print(f"👥 Entities found: {results['entities_found']} total, {results['person_entities_found']} persons")
        
        print(f"\n{'─'*50}")
        print("🎯 MATCH DECISION")
        print(f"{'─'*50}")
        
        # Match result with color coding
        result = results['match_result']
        confidence = results['match_confidence']
        
        if result == "MATCH":
            print(f"✅ RESULT: {result}")
            print(f"📊 CONFIDENCE: {confidence:.2f}")
            print("⚠️  ACTION: Human analyst should review this potential match")
        elif result == "NO_MATCH":
            print(f"❌ RESULT: {result}")
            print(f"📊 CONFIDENCE: {confidence:.2f}")
            print("✅ ACTION: Article can be discarded - no match found")
        else:
            print(f"❓ RESULT: {result}")
            print(f"📊 CONFIDENCE: {confidence:.2f}")
            print("⚠️  ACTION: Manual review recommended")
        
        print("\n💭 EXPLANATION:")
        print(f"   {results['match_explanation']}")
        
        print(f"\n🔧 METHOD: {results['match_method']}")
        
        if results['entities_analyzed']:
            print(f"\n👥 ENTITIES ANALYZED: {', '.join(results['entities_analyzed'][:5])}")
        
        print("\n📋 REGULATORY COMPLIANCE:")
        if result == "MATCH":
            print("   ✅ No false negative risk - potential match flagged for review")
        else:
            print("   ✅ Conservative screening applied - low false negative risk")
        
        print(f"\n{'='*80}")

def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Name Matcher AI Adverse Media Screening Pipeline - Regulatory-compliant name matching for adverse media articles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported File Formats:
  • TXT files (plain text)
  • RTF files (Rich Text Format)
  • Note: PDF support can be added with additional libraries

Supported Languages:
  • English, Spanish, French, German
  • Automatic language detection and translation

Examples:
  name_matcher_tool data/article.txt "John Smith"
  name_matcher_tool data/french_article.rtf "Marie Dubois" --debug
  name_matcher_tool data/german_article.rtf "Klaus Mueller" --api-key sk-proj-...
  name_matcher_tool data/spanish_article.txt "Carlos Rodriguez" --output results.json
  
  # With environment variable (recommended):
  export OPENAI_API_KEY="sk-proj-your-key-here"
  name_matcher_tool my_article.rtf "Target Person" --debug
        """
    )
    
    parser.add_argument('file_path', 
                       help='Path to article file (TXT, RTF supported; PDF can be added), recommended <3,000 words')
    parser.add_argument('target_name', 
                       help='Name of the individual to search for in the article')
    parser.add_argument('--debug', 
                       action='store_true',
                       help='Enable debug output')
    parser.add_argument('--api-key', 
                       help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    parser.add_argument('--output', 
                       help='Save results to JSON file')
    parser.add_argument('--model',
                       default='gpt-3.5-turbo',
                       help='OpenAI model to use (default: gpt-3.5-turbo)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.file_path):
        print(f"❌ Error: File not found: {args.file_path}")
        sys.exit(1)
    
    if not args.target_name.strip():
        print("❌ Error: Target name cannot be empty")
        sys.exit(1)
    
    # Initialize and run pipeline
    try:
        pipeline = NameMatcherPipeline(
            openai_api_key=args.api_key,
            debug=args.debug
        )
        
        results = pipeline.process_file(args.file_path, args.target_name)
        
        # Print summary
        pipeline.print_final_summary(results)
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {args.output}")
        
        # Exit with appropriate code
        if "error" in results:
            sys.exit(1)
        elif results.get('match_result') == 'MATCH':
            sys.exit(0)  # Match found - success
        else:
            sys.exit(0)  # No match - also success
            
    except KeyboardInterrupt:
        print("\n❌ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()