import cv2
import numpy as np
from paddleocr import PaddleOCR
import re
import time
import os

class NIDOCRService:
    def __init__(self):
        """Initialize the OCR service with PaddleOCR"""
        self.ocr = PaddleOCR(
            lang="en",
            use_angle_cls=False,
            use_gpu=False,
            show_log=False,
            det_db_box_thresh=0.3,
            cpu_threads=4
        )
        
        # Patterns for NID information
        self.nid_patterns = [
            r'NID No\.?\s*:?\s*([\d\s]+)',
            r'ID No\.?\s*:?\s*([\d\s]+)',
            r'National ID\s*:?\s*([\d\s]+)',
            r'\b(\d{10,17})\b'
        ]

    def extract_text_with_rotation(self, image):
        """Process image at 0 degrees only (optimized)"""
        angles = [0]  # Only process original orientation
        all_results = []
        
        for angle in angles:
            rotated_img = image.copy()
            
            # Run OCR
            result = self.ocr.ocr(rotated_img, cls=False)
            
            # Collect lines and compute confidence
            lines = []
            total_conf = 0
            total_chars = 0
            
            if result and result[0] is not None:
                for line in result[0]:
                    text = line[1][0].strip()
                    conf = line[1][1]
                    if text and len(text) > 2:
                        lines.append((text, conf))
                        total_conf += conf * len(text)
                        total_chars += len(text)
            
            avg_conf = total_conf / total_chars if total_chars > 0 else 0
            
            all_results.append({
                'angle': angle,
                'avg_conf': avg_conf,
                'lines': lines,
                'full_text': ' '.join([t for t, _ in lines])
            })
        
        return all_results[0] if all_results else None

    def extract_nid_number(self, full_text):
        """Extract NID number from text"""
        for pattern in self.nid_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                nid = re.sub(r'\s+', '', match.group(1))
                if 10 <= len(nid) <= 17 and nid.isdigit():
                    return nid
        return None

    def extract_date_of_birth(self, text_lines, full_text):
        """Extract date of birth with flexible format handling"""
        # Search in lines first (more accurate)
        for line in text_lines:
            if any(kw in line for kw in ['Date of Birth', 'DOB', 'Birth', 'জন্ম']):
                # Handle formats: "10Oct 1986", "10 Oct 1986", "10Oct1986"
                match = re.search(r'(\d{1,2})\s*([A-Za-z]{3,})\s*(\d{4})', line)
                if match:
                    day, month, year = match.groups()
                    month_abbr = month[:3].capitalize()
                    
                    # Validate month
                    valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    if month_abbr in valid_months:
                        return f"{day} {month_abbr} {year}"
        
        # Fallback: search entire text
        match = re.search(r'(\d{1,2})\s*([A-Za-z]{3,})\s*(\d{4})', full_text)
        if match:
            day, month, year = match.groups()
            month_abbr = month[:3].capitalize()
            
            valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            if month_abbr in valid_months:
                return f"{day} {month_abbr} {year}"
        
        return None

    def extract_name(self, text_lines):
        """Extract name from line immediately after 'Name' label - PRESERVES PERIODS"""
        
        # Find "Name" label and take the VERY NEXT line (offset=1)
        for i, line in enumerate(text_lines):
            if 'Name' in line or 'নাম' in line:
                # Take the immediate next line (offset=1)
                if i + 1 < len(text_lines):
                    candidate = text_lines[i + 1].strip()
                    
                    # Minimal validation: must have at least 4 characters and not be a single letter
                    if len(candidate) >= 4 and candidate not in ['R', 'A', 'T', 'O', 'AR', 'AT']:
                        # PRESERVE PERIODS - only normalize case and whitespace
                        return ' '.join(candidate.split()).upper()
        
        # Fallback: If no "Name" label found, return first line with 2+ words and length > 6
        for line in text_lines:
            words = line.strip().split()
            if len(words) >= 2 and len(line) > 6:
                # Skip obvious metadata lines
                if not any(kw in line.upper() for kw in [
                    'GOVERNMENT', 'PEOPLE', 'REPUBLIC', 'BANGLADESH', 'NATIONAL',
                    'ID', 'CARD', 'DATE', 'BIRTH', 'NID', 'NO',
                    '/NATIONALDCARD'
                ]):
                    return ' '.join(line.split()).upper()
        
        return None

    def extract_information(self, text_lines):
        """Extract all information from text lines"""
        full_text = ' '.join(text_lines)
        
        # Print all text lines for debugging
        print("\n--- Extracted Text Lines ---")
        for i, line in enumerate(text_lines):
            print(f"{i}: {line}")
        print("---------------------------\n")
        
        # Extract fields
        name = self.extract_name(text_lines)
        dob = self.extract_date_of_birth(text_lines, full_text)
        nid = self.extract_nid_number(full_text)
        
        return {
            'name': name,
            'date_of_birth': dob,
            'nid_number': nid
        }

    def process_image(self, image_path):
        """Main method to process NID image and extract information"""
        start_time = time.time()
        
        try:
            # Read image (in color format)
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # ✅ Convert to grayscale for optimal OCR accuracy
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Extract text
            best_result = self.extract_text_with_rotation(image)
            
            if not best_result or not best_result['lines']:
                return {
                    'success': False,
                    'error': 'No text detected in image',
                    'processing_time': time.time() - start_time
                }
            
            # Separate text lines (no confidence scores needed)
            text_lines = [text for text, _ in best_result['lines']]
            
            # Extract information
            extracted_info = self.extract_information(text_lines)
            
            # Calculate metrics
            processing_time = time.time() - start_time
            confidence_scores = [conf for _, conf in best_result['lines']]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Final output
            print(f"\n{'='*50}")
            print("FINAL EXTRACTION RESULTS")
            print(f"{'='*50}")
            print(f"Name          : {extracted_info['name']}")
            print(f"Date of Birth : {extracted_info['date_of_birth']}")
            print(f"NID Number    : {extracted_info['nid_number']}")
            print(f"Confidence    : {avg_confidence:.2%}")
            print(f"Processing    : {processing_time:.2f}s")
            print(f"{'='*50}\n")
            
            return {
                'success': True,
                'name': extracted_info['name'],
                'date_of_birth': extracted_info['date_of_birth'],
                'nid_number': extracted_info['nid_number'],
                'filename': os.path.basename(image_path),
                'full_text': ' '.join(text_lines),
                'confidence_score': avg_confidence,
                'processing_time': processing_time
            }
            
        except Exception as e:
            print(f"[ERROR] Processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
