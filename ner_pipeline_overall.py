#!/usr/bin/env python3
"""
Enhanced Multilingual NER Pipeline for LLM Integration
Displays full text content and extracts all entity types for comprehensive LLM analysis
"""
import argparse
from typing import List, Dict
import re
from collections import defaultdict
import unicodedata
import spacy

# Import our existing multilingual translator
from multi_language_translator import UnifiedTranslator

class Entity:
    """Enhanced entity class for all entity types (PERSON, ORG, GPE, etc.)"""
    def __init__(self, name: str, entity_type: str, start_char: int, end_char: int, 
                 context: str = "", confidence: float = 1.0, source: str = "spacy", language: str = "en"):
        self.name = name
        self.entity_type = entity_type  # PERSON, ORG, GPE, MONEY, etc.
        self.start_char = start_char
        self.end_char = end_char
        self.context = context
        self.confidence = confidence
        self.source = source  # 'spacy', 'regex', 'spanish_spacy', 'french_spacy', 'german_spacy'
        self.language = language
        self.normalized_name = self._normalize_name(name)
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison (remove accents, lowercase)"""
        normalized = unicodedata.normalize('NFD', name)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return normalized.lower().strip()
    
    def __repr__(self):
        return f"Entity(name='{self.name}', type={self.entity_type}, confidence={self.confidence:.2f}, source='{self.source}')"

class EnhancedMultilingualNER:
    """Enhanced NER pipeline that extracts all entity types for LLM analysis"""
    
    def __init__(self):
        """Initialize NER pipeline with all language models"""
        print("Loading multilingual spaCy models...")
        
        # Language model configurations
        self.models = {
            'en': {'model': 'en_core_web_sm', 'nlp': None},
            'es': {'model': 'es_core_news_sm', 'nlp': None},
            'fr': {'model': 'fr_core_news_sm', 'nlp': None},
            'de': {'model': 'de_core_news_sm', 'nlp': None}
        }
        
        # Load models with error handling
        self.available_languages = ['en']  # English is required
        self._load_models()
        
        # Initialize language-specific patterns for person names
        self._init_person_patterns()
    
    def _load_models(self):
        """Load all available spaCy models"""
        for lang, config in self.models.items():
            try:
                config['nlp'] = spacy.load(config['model'])
                if lang not in self.available_languages:
                    self.available_languages.append(lang)
                print(f"✅ {lang.upper()} model '{config['model']}' loaded successfully!")
            except OSError:
                if lang == 'en':
                    print(f"❌ English model '{config['model']}' not found! This is required.")
                    print("Install it with: python -m spacy download en_core_web_sm")
                    raise
                else:
                    print(f"⚠️ {lang.upper()} model '{config['model']}' not found!")
                    print(f"Install it with: python -m spacy download {config['model']}")
                    print(f"Continuing without {lang.upper()} support...")
    
    def _init_person_patterns(self):
        """Initialize regex patterns for person names in each language"""
        self.person_patterns = {
            'es': [
                r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de|del|de\s+la|de\s+los|y|e)\s+)?(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*){1,3}\b',
                r'\b(?:Don|Doña|Sr\.|Sra\.|Dr\.|Dra\.)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)\b',
            ],
            'fr': [
                r'\b[A-ZÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜÇ][a-záàâäéèêëíìîïóòôöúùûüç]+(?:\s+(?:de|du|des|d\'|le|la|les)\s+)?(?:[A-ZÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜÇ][a-záàâäéèêëíìîïóòôöúùûüç]+\s*){1,3}\b',
                r'\b(?:M\.|Mme|Mlle|Dr\.|Pr\.)\s+([A-ZÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜÇ][a-záàâäéèêëíìîïóòôöúùûüç]+(?:\s+[A-ZÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜÇ][a-záàâäéèêëíìîïóòôöúùûüç]+)*)\b',
            ],
            'de': [
                r'\b[A-ZÄÖÜ][a-zäöüß]+(?:\s+(?:von|zu|der|des|den)\s+)?(?:[A-ZÄÖÜ][a-zäöüß]+\s*){1,3}\b',
                r'\b(?:Herr|Frau|Dr\.|Prof\.)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)\b',
            ],
            'en': [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',
                r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            ]
        }
        
        # Common false positives to filter
        self.false_positives = {
            'es': {'según', 'aunque', 'también', 'después', 'durante', 'mientras', 'entonces', 'además'},
            'fr': {'selon', 'depuis', 'pendant', 'maintenant', 'toujours', 'encore', 'ainsi', 'donc'},
            'de': {'jedoch', 'außerdem', 'während', 'bereits', 'dennoch', 'schließlich', 'allerdings'},
            'en': {'however', 'therefore', 'although', 'meanwhile', 'furthermore', 'nevertheless'}
        }
    
    def extract_all_entities_spacy(self, text: str, language: str) -> List[Entity]:
        """Extract ALL entity types using spaCy model"""
        if language not in self.available_languages:
            print(f"⚠️ Language '{language}' not available, skipping spaCy extraction")
            return []
        
        nlp = self.models[language]['nlp']
        source = f"{language}_spacy" if language != 'en' else 'spacy'
        
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Skip obvious false positives
            if ent.text.lower() in self.false_positives.get(language, set()):
                continue
            
            # Get surrounding context
            context_start = max(0, ent.start_char - 75)
            context_end = min(len(text), ent.end_char + 75)
            context = text[context_start:context_end].strip()
            
            # Calculate confidence based on entity type and context
            confidence = self._calculate_confidence(ent.text, ent.label_, context, language)
            
            entity = Entity(
                name=ent.text.strip(),
                entity_type=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
                context=context,
                confidence=confidence,
                source=source,
                language=language
            )
            entities.append(entity)
        
        return entities
    
    def extract_person_entities_regex(self, text: str, language: str) -> List[Entity]:
        """Extract person entities using language-specific regex patterns"""
        if language not in self.person_patterns:
            return []
        
        entities = []
        patterns = self.person_patterns[language]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1) if match.groups() else match.group(0)
                name = name.strip()
                
                # Skip if too short, contains numbers, or is false positive
                if (len(name.split()) < 1 or 
                    re.search(r'\d', name) or 
                    name.lower() in self.false_positives.get(language, set())):
                    continue
                
                # Get context
                context_start = max(0, match.start() - 75)
                context_end = min(len(text), match.end() + 75)
                context = text[context_start:context_end].strip()
                
                confidence = self._calculate_confidence(name, 'PERSON', context, language, is_regex=True)
                
                entity = Entity(
                    name=name,
                    entity_type='PERSON',
                    start_char=match.start(),
                    end_char=match.end(),
                    context=context,
                    confidence=confidence,
                    source="regex",
                    language=language
                )
                entities.append(entity)
        
        return entities
    
    def _calculate_confidence(self, text: str, entity_type: str, context: str, 
                            language: str, is_regex: bool = False) -> float:
        """Calculate confidence score for entities"""
        confidence = 0.7 if is_regex else 0.85  # Base confidence
        
        # Boost for longer names/entities
        if len(text.split()) >= 2:
            confidence += 0.1
        
        # Boost for proper capitalization
        if all(word[0].isupper() for word in text.split() if word):
            confidence += 0.05
        
        # Language-specific character boosts
        if language == 'es' and any(char in text.lower() for char in 'áéíóúñ'):
            confidence += 0.1
        elif language == 'fr' and any(char in text.lower() for char in 'àâäéèêëíìîïóòôöúùûüç'):
            confidence += 0.1
        elif language == 'de' and any(char in text.lower() for char in 'äöüß'):
            confidence += 0.1
        
        # Entity type specific adjustments
        if entity_type in ['PERSON', 'PER']:
            # Context indicators for persons
            person_indicators = {
                'es': ['señor', 'señora', 'presidente', 'director', 'fiscal', 'juez'],
                'fr': ['monsieur', 'madame', 'président', 'directeur', 'procureur', 'juge'],
                'de': ['herr', 'frau', 'präsident', 'direktor', 'staatsanwalt', 'richter'],
                'en': ['mr', 'mrs', 'president', 'director', 'prosecutor', 'judge']
            }
            if any(indicator in context.lower() for indicator in person_indicators.get(language, [])):
                confidence += 0.15
        
        # Penalize suspicious patterns
        if re.search(r'\d', text):
            confidence -= 0.2
        
        return max(0.1, min(1.0, confidence))
    
    def clean_and_deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Clean and deduplicate entities"""
        # Group by normalized names and entity type
        entity_groups = defaultdict(list)
        for entity in entities:
            key = (entity.normalized_name, entity.entity_type)
            entity_groups[key].append(entity)
        
        final_entities = []
        for _, group in entity_groups.items():
            if not group:
                continue
            
            # Select best entity from group (highest confidence, then longest name)
            best_entity = max(group, key=lambda e: (e.confidence, len(e.name)))
            final_entities.append(best_entity)
        
        return sorted(final_entities, key=lambda x: (x.entity_type, x.confidence), reverse=True)
    
    def process_multilingual_extraction(self, original_text: str, translated_text: str, 
                                      original_lang: str, debug: bool = True) -> Dict:
        """Process entity extraction on both original and translated text"""
        if debug:
            print(f"\n{'='*80}")
            print("🌍 ENHANCED MULTILINGUAL ENTITY EXTRACTION")
            print(f"{'='*80}")
            print(f"Original language: {original_lang}")
            print(f"Available models: {', '.join(self.available_languages)}")
        
        all_entities = []
        
        # Step 1: Extract from original text
        if debug:
            print(f"\n1️⃣ Extracting from original {original_lang} text...")
        
        if original_lang in self.available_languages:
            original_spacy_entities = self.extract_all_entities_spacy(original_text, original_lang)
            original_person_regex = self.extract_person_entities_regex(original_text, original_lang)
            
            if debug:
                print(f"   {original_lang.upper()} spaCy entities: {len(original_spacy_entities)}")
                print(f"   {original_lang.upper()} person regex: {len(original_person_regex)}")
            
            all_entities.extend(original_spacy_entities)
            all_entities.extend(original_person_regex)
        else:
            if debug:
                print(f"   ⚠️ {original_lang.upper()} model not available")
        
        # Step 2: Extract from translated English text
        if debug:
            print("\n2️⃣ Extracting from translated English text...")
        
        english_spacy_entities = self.extract_all_entities_spacy(translated_text, "en")
        english_person_regex = self.extract_person_entities_regex(translated_text, "en")
        
        if debug:
            print(f"   English spaCy entities: {len(english_spacy_entities)}")
            print(f"   English person regex: {len(english_person_regex)}")
        
        all_entities.extend(english_spacy_entities)
        all_entities.extend(english_person_regex)
        
        # Step 3: Clean and deduplicate
        if debug:
            print("\n3️⃣ Cleaning and deduplicating...")
        
        final_entities = self.clean_and_deduplicate_entities(all_entities)
        
        return {
            'all_entities': final_entities,
            'person_entities': [e for e in final_entities if e.entity_type in ['PERSON', 'PER']],
            'organization_entities': [e for e in final_entities if e.entity_type in ['ORG', 'ORGANIZATION']],
            'other_entities': [e for e in final_entities if e.entity_type not in ['PERSON', 'PER', 'ORG', 'ORGANIZATION']],
            'total_entities_found': len(final_entities),
            'processing_stats': {
                'total_raw_entities': len(all_entities),
                'after_deduplication': len(final_entities),
                'available_languages': self.available_languages
            }
        }

class LLMReadyPipeline:
    """Complete pipeline optimized for LLM integration"""
    
    def __init__(self):
        print("Initializing LLM-Ready Pipeline...")
        self.translator = UnifiedTranslator()
        self.ner = EnhancedMultilingualNER()
        print("✅ LLM-ready pipeline initialized!")
        print(f"📍 Supported languages: {', '.join(self.ner.available_languages)}")
    
    def process_for_llm(self, file_path: str, target_name: str, debug: bool = True) -> Dict:
        """Process file and return LLM-ready data structure"""
        print(f"\n{'='*80}")
        print("🤖 LLM-READY PROCESSING PIPELINE")
        print(f"File: {file_path}")
        print(f"Target: {target_name}")
        print(f"{'='*80}")
        
        # Step 1: Translation phase
        print("\n📖 Reading and translating file...")
        text = self.translator.read_file(file_path)
        detected_lang = self.translator.detect_language(text)
        english_text = self.translator.translate_to_english(text, detected_lang)
        
        print(f"✅ File processed: {detected_lang} → en")
        print(f"   Original: {len(text)} chars")
        print(f"   Translated: {len(english_text)} chars")
        
        # Step 2: Entity extraction
        print("\n🔍 Extracting entities...")
        extraction_result = self.ner.process_multilingual_extraction(
            original_text=text,
            translated_text=english_text,
            original_lang=detected_lang,
            debug=debug
        )
        
        # Step 3: Display content for LLM
        if debug:
            self._display_llm_content(text, english_text, extraction_result, detected_lang, target_name)
        
        return {
            'target_name': target_name,
            'original_text': text,
            'translated_text': english_text,
            'detected_language': detected_lang,
            'extraction_result': extraction_result
        }
    
    def _display_llm_content(self, original_text: str, translated_text: str, 
                           extraction_result: Dict, detected_lang: str, target_name: str):
        """Display content in LLM-ready format"""
        
        print(f"\n{'='*80}")
        print("📝 LLM INPUT CONTENT")
        print(f"{'='*80}")
        
        print(f"\n🎯 TARGET NAME: {target_name}")
        
        print(f"\n📄 ORIGINAL ARTICLE ({detected_lang.upper()}):")
        print("─" * 80)
        print(original_text)
        print("─" * 80)
        
        print("\n🌐 TRANSLATED ARTICLE (ENGLISH):")
        print("─" * 80)
        print(translated_text)
        print("─" * 80)
        
        print("\n👥 ALL ENTITIES FOUND IN ARTICLE:")
        print("─" * 80)
        
        entities = extraction_result['all_entities']
        if entities:
            for i, entity in enumerate(entities, 1):
                print(f"{i}. NAME: '{entity.name}'")
                print(f"   TYPE: {entity.entity_type}")
                print(f"   CONFIDENCE: {entity.confidence:.2f}")
                print(f"   SOURCE: {entity.source} (language: {entity.language})")
                print(f"   CONTEXT: \"{entity.context[:100]}...\"")
                print()
        else:
            print("No entities found in the article.")
        
        print("─" * 80)
        
        # Summary statistics
        person_count = len(extraction_result['person_entities'])
        org_count = len(extraction_result['organization_entities'])
        other_count = len(extraction_result['other_entities'])
        
        print("\n📊 ENTITY SUMMARY:")
        print(f"   👥 Persons: {person_count}")
        print(f"   🏢 Organizations: {org_count}")
        print(f"   🔖 Other entities: {other_count}")
        print(f"   📍 Total entities: {extraction_result['total_entities_found']}")

def main():
    """LLM-ready command line interface"""
    parser = argparse.ArgumentParser(description='LLM-Ready Multilingual Entity Extraction Pipeline')
    parser.add_argument('file_path', help='Path to RTF or TXT file')
    parser.add_argument('target_name', help='Name to search for in the article')
    parser.add_argument('--debug', action='store_true', default=True, help='Enable detailed output')
    
    args = parser.parse_args()
    
    # Process the file for LLM
    pipeline = LLMReadyPipeline()
    result = pipeline.process_for_llm(args.file_path, args.target_name, debug=args.debug)
    
    print(f"\n{'='*80}")
    print("✅ PROCESSING COMPLETE - READY FOR LLM INTEGRATION")
    print(f"{'='*80}")
    print(f"📁 File: {result['target_name']}")
    print(f"🌐 Language: {result['detected_language']}")
    print(f"🔍 Total entities: {result['extraction_result']['total_entities_found']}")
    print("\nData structure ready for LLM matching component!")

if __name__ == "__main__":
    main()