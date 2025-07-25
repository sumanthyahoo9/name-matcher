#!/usr/bin/env python3
"""
Enhanced NER Pipeline with Multilingual Translation Integration
Key improvements:
1. Dual-language NER (original + translated)
2. Better Spanish name patterns
3. Improved confidence scoring
4. Enhanced deduplication
5. Context-aware validation
"""

import spacy
import argparse
from typing import List, Dict, Set, Tuple
import re
from collections import defaultdict
import unicodedata

# Import our existing multilingual translator
from multi_language_translator import UnifiedTranslator

class PersonEntity:
    """Enhanced person entity with confidence and source tracking"""
    def __init__(self, name: str, start_char: int, end_char: int, context: str = "", 
                 confidence: float = 1.0, source: str = "spacy", language: str = "en"):
        self.name = name
        self.start_char = start_char
        self.end_char = end_char
        self.context = context
        self.confidence = confidence
        self.source = source  # 'spacy', 'regex', 'spanish_spacy'
        self.language = language
        self.normalized_name = self._normalize_name(name)
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        # Remove accents and convert to lowercase
        normalized = unicodedata.normalize('NFD', name)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return normalized.lower().strip()
    
    def __repr__(self):
        return f"PersonEntity(name='{self.name}', confidence={self.confidence:.2f}, source='{self.source}')"

class EnhancedNERPipeline:
    """Enhanced Named Entity Recognition pipeline with multilingual support"""
    
    def __init__(self, english_model="en_core_web_sm", spanish_model="es_core_news_sm"):
        """Initialize NER pipeline with both English and Spanish models"""
        print(f"Loading spaCy models...")
        
        # Load English model
        try:
            self.nlp_en = spacy.load(english_model)
            print(f"✅ English model '{english_model}' loaded successfully!")
        except OSError:
            print(f"❌ English model '{english_model}' not found!")
            print("Install it with: python -m spacy download en_core_web_sm")
            raise
        
        # Load Spanish model
        try:
            self.nlp_es = spacy.load(spanish_model)
            print(f"✅ Spanish model '{spanish_model}' loaded successfully!")
        except OSError:
            print(f"⚠️ Spanish model '{spanish_model}' not found!")
            print("Install it with: python -m spacy download es_core_news_sm")
            print("Continuing with English-only processing...")
            self.nlp_es = None
        
        # Enhanced Spanish name patterns
        self.spanish_name_patterns = [
            # Full Spanish names with particles
            r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de|del|de\s+la|de\s+los|y|e)\s+)?(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*){1,3}\b',
            # Names with Spanish titles
            r'\b(?:Don|Doña|Sr\.|Sra\.|Dr\.|Dra\.)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)\b',
            # Names in quotes (often used in Spanish news)
            r'["\']([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)["\']',
            # Compound surnames common in Spanish
            r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+-[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b'
        ]
    
    def extract_entities_spacy(self, text: str, language: str = "en") -> List[PersonEntity]:
        """Extract person entities using appropriate spaCy model"""
        if language == "es" and self.nlp_es:
            nlp = self.nlp_es
            source = "spanish_spacy"
        else:
            nlp = self.nlp_en
            source = "spacy"
        
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "PER"]:  # Different models use different labels
                # Get surrounding context
                context_start = max(0, ent.start_char - 75)
                context_end = min(len(text), ent.end_char + 75)
                context = text[context_start:context_end].strip()
                
                # Calculate confidence based on context and entity properties
                confidence = self._calculate_spacy_confidence(ent, context)
                
                entity = PersonEntity(
                    name=ent.text.strip(),
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    context=context,
                    confidence=confidence,
                    source=source,
                    language=language
                )
                entities.append(entity)
        
        return entities
    
    def extract_entities_regex(self, text: str, language: str = "en") -> List[PersonEntity]:
        """Extract person entities using enhanced regex patterns"""
        entities = []
        
        if language == "es":
            patterns = self.spanish_name_patterns
        else:
            # English patterns (improved)
            patterns = [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # Standard names
                r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Titled names
                r'\b[A-Z][a-z]+\s+[A-Z]\.?\s+[A-Z][a-z]+\b',  # Middle initial names
            ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1) if match.groups() else match.group(0)
                name = name.strip()
                
                # Skip if too short or contains numbers
                if len(name.split()) < 1 or re.search(r'\d', name):
                    continue
                
                # Get context
                context_start = max(0, match.start() - 75)
                context_end = min(len(text), match.end() + 75)
                context = text[context_start:context_end].strip()
                
                # Calculate confidence for regex matches
                confidence = self._calculate_regex_confidence(name, context, language)
                
                entity = PersonEntity(
                    name=name,
                    start_char=match.start(),
                    end_char=match.end(),
                    context=context,
                    confidence=confidence,
                    source="regex",
                    language=language
                )
                entities.append(entity)
        
        return entities
    
    def _calculate_spacy_confidence(self, ent, context: str) -> float:
        """Calculate confidence score for spaCy entities"""
        confidence = 0.8  # Base confidence for spaCy
        
        # Boost confidence for longer names
        if len(ent.text.split()) >= 2:
            confidence += 0.1
        
        # Boost for capitalization patterns
        if all(word[0].isupper() for word in ent.text.split() if word):
            confidence += 0.05
        
        # Reduce for suspicious patterns
        if re.search(r'\d', ent.text):
            confidence -= 0.3
        
        if ent.text.lower() in ['easter', 'office', 'although', 'government']:
            confidence -= 0.5
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_regex_confidence(self, name: str, context: str, language: str) -> float:
        """Calculate confidence score for regex matches"""
        confidence = 0.6  # Base confidence for regex
        
        # Language-specific boosts
        if language == "es":
            # Spanish-specific indicators
            if any(particle in name.lower() for particle in ['de', 'del', 'de la']):
                confidence += 0.1
            if re.search(r'[áéíóúñ]', name.lower()):
                confidence += 0.1
        
        # Context-based adjustments
        context_lower = context.lower()
        person_indicators = ['said', 'according to', 'señor', 'señora', 'presidente', 'director']
        if any(indicator in context_lower for indicator in person_indicators):
            confidence += 0.15
        
        # Penalize common false positives
        false_positives = ['real madrid', 'united states', 'new york', 'los angeles']
        if name.lower() in false_positives:
            confidence -= 0.4
        
        return max(0.1, min(1.0, confidence))
    
    def clean_and_normalize_entities(self, entities: List[PersonEntity]) -> List[PersonEntity]:
        """Enhanced cleaning and normalization"""
        cleaned_entities = []
        
        for entity in entities:
            cleaned_name = entity.name
            
            # Remove titles and prefixes
            cleaned_name = re.sub(r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Don|Doña|Sr\.|Sra\.|Dra?\.)\s*', '', cleaned_name)
            
            # Remove suffixes
            cleaned_name = re.sub(r'\s*(?:Jr\.?|Sr\.?|III|IV|V)$', '', cleaned_name)
            
            # Clean extra whitespace
            cleaned_name = ' '.join(cleaned_name.split())
            
            # Skip if too short or problematic
            if len(cleaned_name.split()) < 1 or re.search(r'\d', cleaned_name):
                continue
            
            # Skip obvious false positives
            if cleaned_name.lower() in ['easter', 'office', 'although', 'government', 'the', 'in', 'on', 'at']:
                continue
            
            entity.name = cleaned_name
            cleaned_entities.append(entity)
        
        return cleaned_entities
    
    def smart_deduplicate_entities(self, entities: List[PersonEntity]) -> List[PersonEntity]:
        """Smart deduplication that handles name variations"""
        # Group by normalized names
        name_groups = defaultdict(list)
        for entity in entities:
            name_groups[entity.normalized_name].append(entity)
        
        final_entities = []
        for normalized_name, group in name_groups.items():
            if not group:
                continue
            
            # Select best entity from group (highest confidence, longest name)
            best_entity = max(group, key=lambda e: (e.confidence, len(e.name)))
            
            # If we have multiple high-confidence entities, prefer the longest/most complete name
            high_conf_entities = [e for e in group if e.confidence > 0.7]
            if len(high_conf_entities) > 1:
                best_entity = max(high_conf_entities, key=lambda e: len(e.name))
            
            final_entities.append(best_entity)
        
        return final_entities
    
    def process_dual_language_ner(self, original_text: str, translated_text: str, 
                                original_lang: str, debug: bool = True) -> Dict:
        """Process NER on both original and translated text"""
        if debug:
            print(f"\n{'='*60}")
            print("🔍 ENHANCED DUAL-LANGUAGE NER PIPELINE")
            print(f"{'='*60}")
            print(f"Original text ({original_lang}): {len(original_text)} chars")
            print(f"Translated text (en): {len(translated_text)} chars")
        
        all_entities = []
        
        # Step 1: Extract from original text (if Spanish model available)
        if debug:
            print(f"\n1️⃣ Extracting from original {original_lang} text...")
        
        if original_lang == "es" and self.nlp_es:
            original_spacy_entities = self.extract_entities_spacy(original_text, "es")
            original_regex_entities = self.extract_entities_regex(original_text, "es")
            
            if debug:
                print(f"   Spanish spaCy: {len(original_spacy_entities)} entities")
                print(f"   Spanish regex: {len(original_regex_entities)} entities")
            
            all_entities.extend(original_spacy_entities)
            all_entities.extend(original_regex_entities)
        
        # Step 2: Extract from translated text
        if debug:
            print(f"\n2️⃣ Extracting from translated English text...")
        
        translated_spacy_entities = self.extract_entities_spacy(translated_text, "en")
        translated_regex_entities = self.extract_entities_regex(translated_text, "en")
        
        if debug:
            print(f"   English spaCy: {len(translated_spacy_entities)} entities")
            print(f"   English regex: {len(translated_regex_entities)} entities")
        
        all_entities.extend(translated_spacy_entities)
        all_entities.extend(translated_regex_entities)
        
        # Step 3: Clean and normalize
        if debug:
            print(f"\n3️⃣ Cleaning and normalizing...")
        
        cleaned_entities = self.clean_and_normalize_entities(all_entities)
        
        if debug:
            print(f"   After cleaning: {len(cleaned_entities)} entities")
        
        # Step 4: Smart deduplication
        if debug:
            print(f"\n4️⃣ Smart deduplication...")
        
        final_entities = self.smart_deduplicate_entities(cleaned_entities)
        
        if debug:
            print(f"\n📋 FINAL EXTRACTED ENTITIES")
            print("-" * 50)
            print(f"Total unique entities: {len(final_entities)}")
            
            if final_entities:
                # Sort by confidence
                final_entities.sort(key=lambda x: x.confidence, reverse=True)
                
                for i, entity in enumerate(final_entities, 1):
                    print(f"\n{i}. Name: '{entity.name}'")
                    print(f"   Confidence: {entity.confidence:.2f}")
                    print(f"   Source: {entity.source}")
                    print(f"   Language: {entity.language}")
                    print(f"   Context: {entity.context[:100]}...")
            else:
                print("   No person entities detected.")
        
        return {
            'person_entities': final_entities,
            'total_entities_found': len(final_entities),
            'processing_stats': {
                'total_raw_entities': len(all_entities),
                'after_cleaning': len(cleaned_entities),
                'after_deduplication': len(final_entities),
                'by_source': {
                    'spanish_spacy': len([e for e in all_entities if e.source == 'spanish_spacy']),
                    'spacy': len([e for e in all_entities if e.source == 'spacy']),
                    'regex': len([e for e in all_entities if e.source == 'regex'])
                }
            }
        }

class EnhancedIntegratedPipeline:
    """Enhanced integrated pipeline with dual-language NER"""
    
    def __init__(self):
        print("Initializing Enhanced Integrated Pipeline...")
        self.translator = UnifiedTranslator()
        self.ner = EnhancedNERPipeline()
        print("✅ Enhanced integrated pipeline ready!")
    
    def process_file(self, file_path: str, target_name: str, debug: bool = True):
        """Process file with enhanced dual-language NER"""
        print(f"\n{'='*70}")
        print("🚀 ENHANCED INTEGRATED PIPELINE")
        print(f"File: {file_path}")
        print(f"Target: {target_name}")
        print(f"{'='*70}")
        
        # Step 1: Translation phase
        print("\n🌐 TRANSLATION PHASE")
        print("-" * 30)
        
        print("📖 Reading file...")
        text = self.translator.read_file(file_path)
        print(f"✅ File read successfully ({len(text)} characters)")
        
        print("\n🔍 Detecting language...")
        detected_lang = self.translator.detect_language(text)
        
        print(f"\n🌐 Translating {detected_lang}→en...")
        english_text = self.translator.translate_to_english(text, detected_lang)
        print(f"✅ Translation completed ({len(english_text)} characters)")
        
        # Step 2: Enhanced NER phase
        print(f"\n🔍 ENHANCED NER PHASE")
        print("-" * 30)
        
        ner_result = self.ner.process_dual_language_ner(
            original_text=text,
            translated_text=english_text,
            original_lang=detected_lang,
            debug=debug
        )
        
        # Step 3: Target matching analysis
        print(f"\n🎯 TARGET MATCHING ANALYSIS")
        print("-" * 30)
        
        target_matches = self.find_target_matches(target_name, ner_result['person_entities'])
        
        return {
            'file_info': {
                'file_path': file_path,
                'target_name': target_name,
                'detected_language': detected_lang
            },
            'translation': {
                'original_text': text,
                'translated_text': english_text
            },
            'ner_results': ner_result,
            'target_matches': target_matches
        }
    
    def find_target_matches(self, target_name: str, entities: List[PersonEntity]) -> Dict:
        """Find potential matches for target name"""
        target_normalized = unicodedata.normalize('NFD', target_name.lower())
        target_normalized = ''.join(c for c in target_normalized if unicodedata.category(c) != 'Mn')
        
        exact_matches = []
        partial_matches = []
        
        for entity in entities:
            entity_normalized = entity.normalized_name
            
            # Exact match
            if target_normalized == entity_normalized:
                exact_matches.append(entity)
            # Partial match (contains or is contained)
            elif target_normalized in entity_normalized or entity_normalized in target_normalized:
                partial_matches.append(entity)
        
        print(f"🎯 Target: '{target_name}'")
        print(f"   Exact matches: {len(exact_matches)}")
        print(f"   Partial matches: {len(partial_matches)}")
        
        if exact_matches:
            print("   ✅ EXACT MATCH FOUND!")
            for match in exact_matches:
                print(f"      → '{match.name}' (confidence: {match.confidence:.2f})")
        
        if partial_matches:
            print("   ⚠️ Partial matches found:")
            for match in partial_matches:
                print(f"      → '{match.name}' (confidence: {match.confidence:.2f})")
        
        return {
            'exact_matches': exact_matches,
            'partial_matches': partial_matches,
            'has_match': len(exact_matches) > 0,
            'match_confidence': max([m.confidence for m in exact_matches], default=0.0)
        }

def main():
    """Enhanced command line interface"""
    parser = argparse.ArgumentParser(description='Enhanced Integrated Translation + NER Pipeline')
    parser.add_argument('file_path', help='Path to RTF or TXT file')
    parser.add_argument('target_name', help='Name to search for in the article')
    parser.add_argument('--debug', action='store_true', default=True, help='Enable debug output')
    
    args = parser.parse_args()
    
    # Process the file
    pipeline = EnhancedIntegratedPipeline()
    result = pipeline.process_file(args.file_path, args.target_name, debug=args.debug)
    
    # Final summary
    print(f"\n{'='*70}")
    print("📊 ENHANCED PIPELINE SUMMARY")
    print(f"{'='*70}")
    print(f"📁 File: {result['file_info']['file_path']}")
    print(f"🎯 Target: {result['file_info']['target_name']}")
    print(f"🌐 Language: {result['file_info']['detected_language']}")
    print(f"🔍 Entities Found: {result['ner_results']['total_entities_found']}")
    print(f"🎯 Target Match: {'✅ YES' if result['target_matches']['has_match'] else '❌ NO'}")
    
    if result['target_matches']['has_match']:
        print(f"🎯 Match Confidence: {result['target_matches']['match_confidence']:.2f}")
    
    print(f"\n📋 ALL ENTITIES EXTRACTED:")
    entities = result['ner_results']['person_entities']
    if entities:
        for i, entity in enumerate(entities, 1):
            print(f"   {i}. {entity.name} (conf: {entity.confidence:.2f}, src: {entity.source})")
    else:
        print("   None found")
    
    print(f"\n📊 Processing Stats:")
    stats = result['ner_results']['processing_stats']
    print(f"   Raw entities: {stats['total_raw_entities']}")
    print(f"   After cleaning: {stats['after_cleaning']}")
    print(f"   Final count: {stats['after_deduplication']}")
    print(f"   By source: {stats['by_source']}")

if __name__ == "__main__":
    main()