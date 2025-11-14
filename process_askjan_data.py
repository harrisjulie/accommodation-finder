#!/usr/bin/env python3
"""
AskJAN Accommodations Finder - Complete Data Pipeline
This script will process the disability database and create a searchable accommodation tool
Run with: python process_askjan_data.py input_file.txt
"""

import json
import re
import os
import sys
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import hashlib

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Disability:
    """Represents a disability with all its associated information"""
    name: str
    about: str
    accommodating_info: str
    questions: List[str]
    limitations: Dict[str, List[str]] = field(default_factory=dict)  # limitation -> accommodations
    barriers: Dict[str, List[str]] = field(default_factory=dict)     # barrier -> accommodations

@dataclass
class ProcessedData:
    """Structured data ready for database insertion"""
    disabilities: List[Dict]
    limitations: List[Dict]
    barriers: List[Dict]
    accommodations: List[Dict]
    relationships: Dict[str, List[Tuple]]

# ============================================================================
# PARSER
# ============================================================================

class AskJANParser:
    """Parses the AskJAN disability document into structured data"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.disabilities = []
        
    def parse(self) -> List[Disability]:
        """Main parsing method"""
        print(f"📖 Reading document from {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into disability sections
        sections = self._split_into_disabilities(content)
        print(f"📊 Found {len(sections)} potential disability sections")
        
        # Parse each section
        for i, section in enumerate(sections, 1):
            try:
                disability = self._parse_disability_section(section)
                if disability and disability.name:
                    self.disabilities.append(disability)
                    print(f"  ✓ Parsed {i}/{len(sections)}: {disability.name}")
            except Exception as e:
                print(f"  ✗ Error parsing section {i}: {str(e)}")
        
        print(f"✅ Successfully parsed {len(self.disabilities)} disabilities")
        return self.disabilities
    
    def _split_into_disabilities(self, content: str) -> List[str]:
        """Split document into individual disability sections"""
        # Common patterns for disability headers
        patterns = [
            r'Accommodating Employees with ([A-Z][^\n]+)',
            r'([A-Z][^\n]+)\n+About',
            r'\n([A-Z][^\n]+)\n+(?:About|Accommodating)',
        ]
        
        sections = []
        current_section = []
        lines = content.split('\n')
        
        for line in lines:
            # Check if this line starts a new disability section
            is_header = False
            for pattern in patterns:
                if re.match(pattern, line):
                    if current_section:
                        sections.append('\n'.join(current_section))
                    current_section = [line]
                    is_header = True
                    break
            
            if not is_header:
                current_section.append(line)
        
        # Don't forget the last section
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def _parse_disability_section(self, section: str) -> Disability:
        """Parse a single disability section"""
        # Extract disability name
        name = self._extract_disability_name(section)
        if not name:
            return None
        
        # Extract main sections
        about = self._extract_section(section, "About", 
                                     ["Questions to Consider", "Accommodating Employees"])
        
        accommodating = self._extract_section(section, 
                                             f"Accommodating Employees with {name}",
                                             ["Questions to Consider", "Accommodation Ideas"])
        
        questions = self._extract_questions(section)
        limitations = self._extract_limitations(section)
        barriers = self._extract_barriers(section)
        
        return Disability(
            name=name,
            about=about,
            accommodating_info=accommodating,
            questions=questions,
            limitations=limitations,
            barriers=barriers
        )
    
    def _extract_disability_name(self, section: str) -> str:
        """Extract the disability name from section"""
        patterns = [
            r'Accommodating Employees with ([^\n]+)',
            r'^([A-Z][^\n]+)\n+About',
            r'^([A-Z][^\n]+)\n+Accommodating',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, section, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                name = name.replace(':', '').strip()
                return name
        
        return None
    
    def _extract_section(self, text: str, start_marker: str, end_markers: List[str]) -> str:
        """Extract text between markers"""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""
        
        start_idx += len(start_marker)
        end_idx = len(text)
        
        for end_marker in end_markers:
            idx = text.find(end_marker, start_idx)
            if idx != -1 and idx < end_idx:
                end_idx = idx
        
        content = text[start_idx:end_idx].strip()
        return content
    
    def _extract_questions(self, section: str) -> List[str]:
        """Extract questions to consider"""
        questions_text = self._extract_section(section, 
                                              "Questions to Consider",
                                              ["Accommodation Ideas", "Limitations", "Work-Related Functions"])
        
        if not questions_text:
            return []
        
        # Split by bullet points or numbered lists
        questions = []
        patterns = [r'•\s*([^•]+)', r'\d+\.\s*([^0-9]+)', r'[-*]\s*([^-*]+)']
        
        for pattern in patterns:
            matches = re.findall(pattern, questions_text)
            if matches:
                questions.extend([q.strip() for q in matches if len(q.strip()) > 10])
                break
        
        if not questions:
            # Fall back to splitting by question marks
            sentences = questions_text.split('?')
            questions = [s.strip() + '?' for s in sentences if len(s.strip()) > 10]
        
        return questions
    
    def _extract_limitations(self, section: str) -> Dict[str, List[str]]:
        """Extract limitations and their accommodations"""
        limitations = {}
        
        # Find the limitations section
        lim_start = section.find("Accommodation Ideas by Limitation")
        if lim_start == -1:
            lim_start = section.find("Limitations:")
        if lim_start == -1:
            return limitations
        
        # Find where it ends (usually at Work-Related Functions)
        work_start = section.find("Work-Related Functions", lim_start)
        if work_start == -1:
            work_start = section.find("Work Functions", lim_start)
        if work_start == -1:
            lim_section = section[lim_start:]
        else:
            lim_section = section[lim_start:work_start]
        
        # Parse limitation blocks
        # Pattern: Limitation name followed by accommodations
        lines = lim_section.split('\n')
        current_limitation = None
        current_accommodations = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a limitation header (usually ends with : or is in caps)
            if line.endswith(':') or (line.isupper() and len(line) > 3):
                # Save previous limitation
                if current_limitation and current_accommodations:
                    limitations[current_limitation] = current_accommodations
                
                # Start new limitation
                current_limitation = line.replace(':', '').strip()
                current_accommodations = []
            
            # Otherwise it might be an accommodation
            elif current_limitation:
                # Clean up accommodation text
                acc = line.strip('•-* \t')
                if len(acc) > 5:  # Filter out very short strings
                    current_accommodations.append(acc)
        
        # Don't forget the last limitation
        if current_limitation and current_accommodations:
            limitations[current_limitation] = current_accommodations
        
        return limitations
    
    def _extract_barriers(self, section: str) -> Dict[str, List[str]]:
        """Extract work-related function barriers and their accommodations"""
        barriers = {}
        
        # Find the barriers section
        barrier_start = section.find("Work-Related Functions")
        if barrier_start == -1:
            barrier_start = section.find("Work Functions")
        if barrier_start == -1:
            barrier_start = section.find("Barriers:")
        if barrier_start == -1:
            return barriers
        
        barrier_section = section[barrier_start:]
        
        # Similar parsing to limitations
        lines = barrier_section.split('\n')
        current_barrier = None
        current_accommodations = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a barrier header
            if line.endswith(':') or (line.isupper() and len(line) > 3):
                # Save previous barrier
                if current_barrier and current_accommodations:
                    barriers[current_barrier] = current_accommodations
                
                # Start new barrier
                current_barrier = line.replace(':', '').strip()
                # Skip if it's the section header
                if 'Work' in current_barrier and 'Function' in current_barrier:
                    current_barrier = None
                    continue
                current_accommodations = []
            
            # Otherwise it might be an accommodation
            elif current_barrier:
                acc = line.strip('•-* \t')
                if len(acc) > 5:
                    current_accommodations.append(acc)
        
        # Don't forget the last barrier
        if current_barrier and current_accommodations:
            barriers[current_barrier] = current_accommodations
        
        return barriers

# ============================================================================
# NORMALIZER
# ============================================================================

class DataNormalizer:
    """Normalizes and deduplicates parsed data"""
    
    def __init__(self, disabilities: List[Disability]):
        self.disabilities = disabilities
        self.processed = ProcessedData(
            disabilities=[],
            limitations=[],
            barriers=[],
            accommodations=[],
            relationships=defaultdict(list)
        )
        
        # ID tracking
        self.disability_id = 1
        self.limitation_id = 1
        self.barrier_id = 1
        self.accommodation_id = 1
        
        # Deduplication tracking
        self.accommodation_map = {}  # text -> id
        self.limitation_map = {}     # name -> id
        self.barrier_map = {}        # name -> id
    
    def normalize(self) -> ProcessedData:
        """Main normalization process"""
        print("\n🔄 Starting normalization process...")
        
        # First pass: collect all unique entities
        self._collect_unique_entities()
        
        # Second pass: build relationships
        self._build_relationships()
        
        print(f"✅ Normalization complete:")
        print(f"  • {len(self.processed.disabilities)} disabilities")
        print(f"  • {len(self.processed.limitations)} limitations")
        print(f"  • {len(self.processed.barriers)} barriers")
        print(f"  • {len(self.processed.accommodations)} accommodations")
        print(f"  • {sum(len(v) for v in self.processed.relationships.values())} relationships")
        
        return self.processed
    
    def _collect_unique_entities(self):
        """Collect and deduplicate all entities"""
        for disability in self.disabilities:
            # Add disability
            self.processed.disabilities.append({
                'disability_id': self.disability_id,
                'name': disability.name,
                'about_description': disability.about,
                'accommodating_employees_info': disability.accommodating_info,
                'questions_to_consider': disability.questions
            })
            
            disability_id = self.disability_id
            self.disability_id += 1
            
            # Process limitations
            for limitation_name, accommodations in disability.limitations.items():
                limitation_id = self._get_or_create_limitation(limitation_name)
                
                # Add relationship
                self.processed.relationships['disability_limitations'].append(
                    (disability_id, limitation_id)
                )
                
                # Process accommodations for this limitation
                for acc_text in accommodations:
                    acc_id = self._get_or_create_accommodation(acc_text)
                    
                    # Add relationships
                    self.processed.relationships['limitation_accommodations'].append(
                        (limitation_id, acc_id)
                    )
                    self.processed.relationships['disability_accommodations'].append(
                        (disability_id, acc_id)
                    )
            
            # Process barriers
            for barrier_name, accommodations in disability.barriers.items():
                barrier_id = self._get_or_create_barrier(barrier_name)
                
                # Process accommodations for this barrier
                for acc_text in accommodations:
                    acc_id = self._get_or_create_accommodation(acc_text)
                    
                    # Add relationships
                    self.processed.relationships['barrier_accommodations'].append(
                        (barrier_id, acc_id)
                    )
                    self.processed.relationships['disability_accommodations'].append(
                        (disability_id, acc_id)
                    )
    
    def _get_or_create_limitation(self, name: str) -> int:
        """Get existing or create new limitation"""
        normalized = self._normalize_text(name)
        
        if normalized in self.limitation_map:
            return self.limitation_map[normalized]
        
        # Create new limitation
        limitation_id = self.limitation_id
        self.limitation_id += 1
        
        self.processed.limitations.append({
            'limitation_id': limitation_id,
            'limitation_name': normalized,
            'category': self._categorize_limitation(normalized)
        })
        
        self.limitation_map[normalized] = limitation_id
        return limitation_id
    
    def _get_or_create_barrier(self, name: str) -> int:
        """Get existing or create new barrier"""
        normalized = self._normalize_text(name)
        
        if normalized in self.barrier_map:
            return self.barrier_map[normalized]
        
        # Create new barrier
        barrier_id = self.barrier_id
        self.barrier_id += 1
        
        self.processed.barriers.append({
            'barrier_id': barrier_id,
            'barrier_name': normalized,
            'barrier_category': self._categorize_barrier(normalized)
        })
        
        self.barrier_map[normalized] = barrier_id
        return barrier_id
    
    def _get_or_create_accommodation(self, text: str) -> int:
        """Get existing or create new accommodation"""
        normalized = self._normalize_text(text)
        
        # Check for similar existing accommodations
        for existing_text, existing_id in self.accommodation_map.items():
            if self._are_similar(normalized, existing_text):
                return existing_id
        
        # Create new accommodation
        accommodation_id = self.accommodation_id
        self.accommodation_id += 1
        
        self.processed.accommodations.append({
            'accommodation_id': accommodation_id,
            'accommodation_text': normalized,
            'accommodation_type': self._categorize_accommodation(normalized)
        })
        
        self.accommodation_map[normalized] = accommodation_id
        return accommodation_id
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistency"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove bullet points and special characters
        text = re.sub(r'^[•\-*]\s*', '', text)
        # Trim
        text = text.strip()
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        return text
    
    def _are_similar(self, text1: str, text2: str) -> bool:
        """Check if two texts are similar enough to be considered duplicates"""
        # Simple similarity check - can be enhanced
        if text1 == text2:
            return True
        
        # Check if one is a substring of the other (with some tolerance)
        if len(text1) > 20 and len(text2) > 20:
            if text1 in text2 or text2 in text1:
                return True
        
        return False
    
    def _categorize_limitation(self, name: str) -> str:
        """Categorize a limitation"""
        name_lower = name.lower()
        
        categories = {
            'physical': ['fatigue', 'pain', 'mobility', 'strength', 'weakness', 'tremor'],
            'cognitive': ['memory', 'concentration', 'focus', 'processing', 'learning'],
            'sensory': ['vision', 'hearing', 'sensitivity', 'sensory'],
            'emotional': ['anxiety', 'stress', 'mood', 'depression']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _categorize_barrier(self, name: str) -> str:
        """Categorize a barrier"""
        name_lower = name.lower()
        
        categories = {
            'Environmental': ['temperature', 'lighting', 'noise', 'space', 'air'],
            'Process': ['procedure', 'workflow', 'method', 'system', 'protocol'],
            'Communication': ['speaking', 'writing', 'reading', 'listening', 'presenting'],
            'Technology': ['computer', 'software', 'equipment', 'device', 'tool'],
            'Schedule/Time': ['hours', 'shift', 'deadline', 'break', 'schedule', 'time'],
            'Social/Interpersonal': ['interaction', 'team', 'customer', 'colleague', 'meeting'],
            'Cognitive/Information': ['memory', 'concentration', 'learning', 'processing', 'organizing'],
            'Physical/Mobility': ['lifting', 'standing', 'sitting', 'walking', 'reaching', 'carrying']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'Other'
    
    def _categorize_accommodation(self, text: str) -> str:
        """Categorize an accommodation"""
        text_lower = text.lower()
        
        types = {
            'equipment': ['chair', 'desk', 'keyboard', 'mouse', 'device', 'tool'],
            'schedule': ['break', 'hours', 'time', 'schedule', 'flexible', 'leave'],
            'environment': ['lighting', 'noise', 'temperature', 'space', 'quiet'],
            'policy': ['allow', 'permit', 'policy', 'procedure', 'remote'],
            'assistance': ['help', 'assist', 'support', 'aide', 'mentor']
        }
        
        for acc_type, keywords in types.items():
            if any(keyword in text_lower for keyword in keywords):
                return acc_type
        
        return 'general'
    
    def _build_relationships(self):
        """Build limitation-barrier relationships based on shared accommodations"""
        # Create reverse mappings
        acc_to_limitations = defaultdict(set)
        acc_to_barriers = defaultdict(set)
        
        for lim_id, acc_id in self.processed.relationships['limitation_accommodations']:
            acc_to_limitations[acc_id].add(lim_id)
        
        for bar_id, acc_id in self.processed.relationships['barrier_accommodations']:
            acc_to_barriers[acc_id].add(bar_id)
        
        # Find connections through shared accommodations
        for acc_id, lim_ids in acc_to_limitations.items():
            if acc_id in acc_to_barriers:
                bar_ids = acc_to_barriers[acc_id]
                for lim_id in lim_ids:
                    for bar_id in bar_ids:
                        relationship = (lim_id, bar_id)
                        if relationship not in self.processed.relationships['limitation_barriers']:
                            self.processed.relationships['limitation_barriers'].append(relationship)
    
    def export_to_json(self, output_dir: str = 'processed_data'):
        """Export processed data to JSON files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export entities
        with open(f'{output_dir}/disabilities.json', 'w') as f:
            json.dump(self.processed.disabilities, f, indent=2)
        
        with open(f'{output_dir}/limitations.json', 'w') as f:
            json.dump(self.processed.limitations, f, indent=2)
        
        with open(f'{output_dir}/barriers.json', 'w') as f:
            json.dump(self.processed.barriers, f, indent=2)
        
        with open(f'{output_dir}/accommodations.json', 'w') as f:
            json.dump(self.processed.accommodations, f, indent=2)
        
        # Export relationships
        relationships_dir = f'{output_dir}/relationships'
        os.makedirs(relationships_dir, exist_ok=True)
        
        for rel_type, relationships in self.processed.relationships.items():
            formatted = []
            
            if rel_type == 'disability_limitations':
                for d_id, l_id in relationships:
                    formatted.append({'disability_id': d_id, 'limitation_id': l_id})
            elif rel_type == 'limitation_barriers':
                for l_id, b_id in relationships:
                    formatted.append({'limitation_id': l_id, 'barrier_id': b_id})
            elif rel_type == 'barrier_accommodations':
                for b_id, a_id in relationships:
                    formatted.append({'barrier_id': b_id, 'accommodation_id': a_id})
            elif rel_type == 'disability_accommodations':
                for d_id, a_id in relationships:
                    formatted.append({'disability_id': d_id, 'accommodation_id': a_id})
            elif rel_type == 'limitation_accommodations':
                for l_id, a_id in relationships:
                    formatted.append({'limitation_id': l_id, 'accommodation_id': a_id})
            
            with open(f'{relationships_dir}/{rel_type}.json', 'w') as f:
                json.dump(formatted, f, indent=2)
        
        print(f"\n📁 Data exported to {output_dir}/")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("=" * 60)
    print("  AskJAN Accommodations Finder - Data Processing Pipeline")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide the input file path")
        print("Usage: python process_askjan_data.py <input_file>")
        print("Example: python process_askjan_data.py disability_database.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"\n❌ Error: File not found: {input_file}")
        sys.exit(1)
    
    try:
        # Step 1: Parse the document
        parser = AskJANParser(input_file)
        disabilities = parser.parse()
        
        if not disabilities:
            print("\n❌ Error: No disabilities found in the document")
            print("Please check the document format")
            sys.exit(1)
        
        # Step 2: Normalize the data
        normalizer = DataNormalizer(disabilities)
        processed_data = normalizer.normalize()
        
        # Step 3: Export to JSON
        normalizer.export_to_json()
        
        # Step 4: Generate summary report
        print("\n" + "=" * 60)
        print("  PROCESSING COMPLETE - SUMMARY REPORT")
        print("=" * 60)
        print(f"\n📊 Final Statistics:")
        print(f"  • Disabilities: {len(processed_data.disabilities)}")
        print(f"  • Unique Limitations: {len(processed_data.limitations)}")
        print(f"  • Unique Barriers: {len(processed_data.barriers)}")
        print(f"  • Unique Accommodations: {len(processed_data.accommodations)}")
        print(f"\n🔗 Relationships Created:")
        for rel_type, relationships in processed_data.relationships.items():
            print(f"  • {rel_type}: {len(relationships)}")
        
        print("\n✅ SUCCESS! Data ready for database import.")
        print("📁 Check the 'processed_data' folder for JSON files.")
        print("\nNext step: Run 'python load_to_database.py' to import into PostgreSQL")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
