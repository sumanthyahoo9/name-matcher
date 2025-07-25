"""
Clean LLM Matching Component for Adverse Media Screening
Regulatory-compliant name matching with refined prompt engineering
"""
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

# Try OpenAI first, fallback to local models
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available, will use fallback methods")

@dataclass
class PersonEntity:
    """Person entity with context information"""
    name: str
    confidence: float
    source: str
    context: str
    start_char: int = 0
    end_char: int = 0
    
    def to_dict(self) -> Dict:
        """
        Convert the entity to a dictionary
        """
        return {
            'name': self.name,
            'confidence': self.confidence,
            'source': self.source,
            'context': self.context[:100] + '...' if len(self.context) > 100 else self.context
        }

@dataclass
class LLMMatchingResult:
    """LLM matching result with regulatory compliance info"""
    result: str  # "MATCH", "NO_MATCH", "UNCERTAIN"
    confidence: float  # 0.0 to 1.0
    explanation: str
    method: str
    entities_analyzed: List[str]
    
    def to_dict(self) -> Dict:
        """
        Convert the result to a dictionary
        """
        return {
            'result': self.result,
            'confidence': self.confidence,
            'explanation': self.explanation,
            'method': self.method,
            'entities_analyzed': self.entities_analyzed
        }
    
    def is_match(self) -> bool:
        """Check if result indicates a match"""
        return self.result == "MATCH"

class RegulatoryLLMMatcher:
    """
    LLM-based name matcher for regulatory compliance adverse media screening.
    Implements refined prompt engineering for precise name matching.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM matcher
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-3.5-turbo, gpt-4, etc.)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key
            self.use_openai = True
            print(f"✅ OpenAI LLM matcher initialized with {model}")
        else:
            self.use_openai = False
            print("⚠️  OpenAI not available, using rule-based fallback")
    
    def create_regulatory_prompt(self, target_name: str, original_text: str, 
                               translated_text: str, entities: List[PersonEntity], 
                               detected_language: str) -> str:
        """
        Create regulatory-compliant prompt with refined name matching rules
        """
        # Format entities for prompt
        if entities:
            entities_text = ""
            person_entities = [e for e in entities if any(keyword in e.source.lower() 
                             for keyword in ['person', 'per', 'people'])]
            
            if person_entities:
                for i, entity in enumerate(person_entities, 1):
                    context_snippet = entity.context[:80].replace('\n', ' ')
                    entities_text += f"{i}. NAME: '{entity.name}'\n"
                    entities_text += f"   CONFIDENCE: {entity.confidence:.2f}\n"
                    entities_text += f"   SOURCE: {entity.source}\n"
                    entities_text += f"   CONTEXT: \"{context_snippet}...\"\n\n"
            else:
                entities_text = "No individual person entities found in the article.\n"
        else:
            entities_text = "No entities extracted from the article.\n"
        
        # Create the refined regulatory prompt
        prompt = f"""You are an expert analyst for **INDIVIDUAL PERSON** adverse media screening in regulated financial services.

## CRITICAL COMPLIANCE GUIDELINES:
1. **FALSE NEGATIVES are REGULATORY VIOLATIONS** - missing a real individual match can result in sanctions
2. **FALSE POSITIVES are MANAGEABLE COSTS** - extra analyst review is acceptable  
3. **PERSONS ONLY**: You are screening for INDIVIDUAL PEOPLE, not organizations, companies, or groups
4. When in doubt between similar names, provide **DETAILED reasoning** for your decision
5. Consider: Could these be the same person with name variations, spelling differences, or cultural adaptations?

## SIMILARITY THRESHOLD GUIDANCE:
- **Identical names**: MATCH (high confidence)
- **Common nicknames** (Jim/James, Bob/Robert, Bill/William): MATCH with explanation
- **Established spelling variations** (Mohammad/Mohammed, Catherine/Katherine): MATCH with explanation
- **Cultural name variations** (Christopher/Christoph, Michael/Mikhail): MATCH with explanation
- **Minor typographical differences** (single letter changes that preserve phonetic sound): CAREFUL ANALYSIS REQUIRED
- **Different names that sound similar** (Carol/Caroline, Anne/Annie, Sujay/Sanjay): NO_MATCH unless strong contextual evidence
- **Similar surnames with different first names**: NO_MATCH unless context strongly suggests same person

## CRITICAL DISTINCTION:
**SPELLING VARIATION** (same name, different spelling) vs **DIFFERENT NAMES** (distinct names that happen to be similar)
- Mohammad/Mohammed = SPELLING VARIATION → MATCH
- Christopher/Christoph = CULTURAL VARIATION → MATCH  
- Anne/Annie = DIFFERENT NAMES → NO_MATCH (even with contextual overlap)
- Sujay/Sanjay = DIFFERENT NAMES → NO_MATCH
- **Conservative approach means being precise about name relationships first, then considering context**
- **Strong contextual evidence alone cannot override clear name differences**

## YOUR TASK:
Analyze whether the target **INDIVIDUAL PERSON** **"{target_name}"** matches any **individual person** mentioned in this adverse media article.

### ORIGINAL ARTICLE ({detected_language.upper()}):
```
{original_text[:500]}{'...' if len(original_text) > 500 else ''}
```

### TRANSLATED ARTICLE (ENGLISH):
```
{translated_text[:500]}{'...' if len(translated_text) > 500 else ''}
```

### INDIVIDUAL PERSONS EXTRACTED:
{entities_text}

**TARGET INDIVIDUAL TO MATCH:** **"{target_name}"**

## REQUIRED RESPONSE FORMAT:
**RESULT:** [MATCH or NO_MATCH]
**CONFIDENCE:** [0.00 to 1.00]  
**EXPLANATION:** [Detailed reasoning explaining your decision, specifically addressing why this is or isn't the same individual person. Include analysis of name variations, spelling differences, and any disambiguating factors.]

**Begin analysis:**"""

        return prompt
    
    def call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API with error handling"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert financial compliance analyst specializing in adverse media screening and name matching."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent regulatory responses
                timeout=30
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️  OpenAI API error: {e}")
            return None
    
    def parse_llm_response(self, response_text: str) -> tuple:
        """Parse LLM response to extract result, confidence, and explanation"""
        try:
            # Extract RESULT
            result_match = re.search(r'\*\*RESULT:\*\*\s*(MATCH|NO_MATCH)', response_text, re.IGNORECASE)
            if not result_match:
                result_match = re.search(r'RESULT:\s*(MATCH|NO_MATCH)', response_text, re.IGNORECASE)
            
            result = result_match.group(1).upper() if result_match else "UNCERTAIN"
            
            # Extract CONFIDENCE
            conf_match = re.search(r'\*\*CONFIDENCE:\*\*\s*([\d.]+)', response_text, re.IGNORECASE)
            if not conf_match:
                conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response_text, re.IGNORECASE)
            
            confidence = float(conf_match.group(1)) if conf_match else 0.5
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            
            # Extract EXPLANATION
            exp_match = re.search(r'\*\*EXPLANATION:\*\*\s*(.+?)(?:\n\n|$)', response_text, re.DOTALL | re.IGNORECASE)
            if not exp_match:
                exp_match = re.search(r'EXPLANATION:\s*(.+?)(?:\n\n|$)', response_text, re.DOTALL | re.IGNORECASE)
            
            explanation = exp_match.group(1).strip() if exp_match else response_text.strip()
            explanation = explanation.replace('\n', ' ').strip()
            
            return result, confidence, explanation
            
        except Exception as e:
            print(f"⚠️  Failed to parse LLM response: {e}")
            return "UNCERTAIN", 0.5, f"Failed to parse response: {response_text[:100]}..."
    
    def rule_based_fallback(self, target_name: str, entities: List[PersonEntity]) -> LLMMatchingResult:
        """Enhanced rule-based fallback when LLM is not available"""
        person_entities = [e for e in entities if 'person' in e.source.lower() or 'per' in e.source.lower()]
        
        if not person_entities:
            return LLMMatchingResult(
                result="NO_MATCH",
                confidence=0.95,
                explanation=f"No individual person entities found in article for target '{target_name}'.",
                method="Rule-based fallback",
                entities_analyzed=[]
            )
        
        target_clean = target_name.lower().strip()
        entity_names = [e.name for e in person_entities]
        
        # Exact match check
        for entity in person_entities:
            if target_clean == entity.name.lower().strip():
                return LLMMatchingResult(
                    result="MATCH",
                    confidence=0.98,
                    explanation=f"Exact name match found: '{target_name}' matches '{entity.name}' in article.",
                    method="Rule-based exact match",
                    entities_analyzed=entity_names
                )
        
        # Partial match check (conservative)
        target_words = set(word.lower() for word in target_name.split() if len(word) > 2)
        best_match = None
        best_score = 0
        
        for entity in person_entities:
            entity_words = set(word.lower() for word in entity.name.split() if len(word) > 2)
            if target_words and entity_words:
                overlap = target_words.intersection(entity_words)
                score = len(overlap) / len(target_words.union(entity_words))
                if score > best_score:
                    best_score = score
                    best_match = entity
        
        if best_score >= 0.8:  # High similarity threshold
            return LLMMatchingResult(
                result="MATCH",
                confidence=0.85,
                explanation=f"High similarity match: '{target_name}' closely matches '{best_match.name}' in article.",
                method="Rule-based similarity match",
                entities_analyzed=entity_names
            )
        else:
            return LLMMatchingResult(
                result="NO_MATCH",
                confidence=0.90,
                explanation=f"No sufficiently similar names found for '{target_name}' among persons in article: {', '.join(entity_names[:3])}.",
                method="Rule-based no match",
                entities_analyzed=entity_names
            )
    
    def match_with_full_context(self, target_name: str, original_text: str, 
                               translated_text: str, entities: List[PersonEntity], 
                               detected_language: str, debug: bool = True) -> LLMMatchingResult:
        """
        Perform regulatory-compliant name matching with full context
        
        Args:
            target_name: Name to search for
            original_text: Original article text
            translated_text: Translated article text  
            entities: Extracted person entities
            detected_language: Original language code
            debug: Print debug information
            
        Returns:
            LLMMatchingResult with match decision and explanation
        """
        if debug:
            print(f"\n{'='*60}")
            print("🤖 REGULATORY LLM MATCHING")
            print(f"{'='*60}")
            print(f"Target: '{target_name}'")
            print(f"Language: {detected_language}")
            print(f"Original text: {len(original_text)} chars")
            print(f"Translated text: {len(translated_text)} chars")
            print(f"Entities: {len(entities)}")
        
        # Filter to person entities only
        person_entities = [e for e in entities if any(keyword in e.source.lower() 
                          for keyword in ['person', 'per', 'people'])]
        entity_names = [e.name for e in person_entities]
        
        if debug and person_entities:
            print("Person entities found:")
            for i, entity in enumerate(person_entities[:5], 1):
                print(f"  {i}. {entity.name} (confidence: {entity.confidence:.2f})")
        
        # Use OpenAI if available
        if self.use_openai:
            if debug:
                print("\n🔄 Creating regulatory prompt...")
            
            prompt = self.create_regulatory_prompt(
                target_name, original_text, translated_text, 
                person_entities, detected_language
            )
            
            if debug:
                print("🔄 Calling OpenAI API...")
            
            llm_response = self.call_openai_api(prompt)
            
            if llm_response and len(llm_response.strip()) > 20:
                try:
                    result, confidence, explanation = self.parse_llm_response(llm_response)
                    
                    if debug:
                        print("✅ LLM Response:")
                        print(f"   Result: {result}")
                        print(f"   Confidence: {confidence:.2f}")
                        print(f"   Explanation: {explanation[:100]}...")
                    
                    return LLMMatchingResult(
                        result=result,
                        confidence=confidence,
                        explanation=explanation,
                        method=f"OpenAI {self.model}",
                        entities_analyzed=entity_names
                    )
                    
                except Exception as e:
                    if debug:
                        print(f"⚠️  Failed to parse LLM response: {e}")
        
        # Fallback to rule-based matching
        if debug:
            print("\n🔄 Using rule-based fallback...")
        
        return self.rule_based_fallback(target_name, person_entities)

def main():
    """Test the regulatory LLM matcher"""
    # Sample test data
    test_entities = [
        PersonEntity(
            name="Anne Brorhilker",
            confidence=1.0,
            source="de_spacy",
            context="Nach Informationen des Handelsblatts kritisiert die Chefermittlerin Anne Brorhilker in einem Brief"
        ),
        PersonEntity(
            name="Benjamin Limbach",
            confidence=1.0,
            source="de_spacy", 
            context="ihren obersten Dienstherrn, Justizminister Benjamin Limbach (Grüne)"
        )
    ]
    
    original_text = "Nach Informationen des Handelsblatts kritisiert die Chefermittlerin Anne Brorhilker in einem Brief ihren obersten Dienstherrn, Justizminister Benjamin Limbach (Grüne)."
    translated_text = "According to Handelsblatt information, chief investigator Anne Brorhilker criticizes her supreme superior, Justice Minister Benjamin Limbach (Greens) in a letter."
    
    # Test cases
    test_cases = [
        "Anne Brorhilker",      # Should be MATCH - exact
        "Annie Brorhilker",     # Should be NO_MATCH - different names  
        "Benjamin Limbach",     # Should be MATCH - exact
        "Ben Limbach",          # Should be MATCH - common nickname
        "John Smith",           # Should be NO_MATCH - not in article
    ]
    
    # Initialize matcher
    matcher = RegulatoryLLMMatcher()
    
    for target_name in test_cases:
        print(f"\n{'='*80}")
        print(f"🧪 TESTING: '{target_name}'")
        print(f"{'='*80}")
        
        result = matcher.match_with_full_context(
            target_name=target_name,
            original_text=original_text,
            translated_text=translated_text,
            entities=test_entities,
            detected_language="de",
            debug=True
        )
        
        print("\n🎯 FINAL RESULT:")
        print(f"   Target: {target_name}")
        print(f"   Result: {result.result}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Method: {result.method}")
        print(f"   Explanation: {result.explanation}")
        print(f"   Entities analyzed: {result.entities_analyzed}")

if __name__ == "__main__":
    main()