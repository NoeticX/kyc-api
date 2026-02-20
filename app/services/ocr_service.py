# import cv2
# import numpy as np
# from paddleocr import PaddleOCR
# import re
# import time
# import os

# class NIDOCRService:
#     def __init__(self):
#         """Initialize the OCR service with PaddleOCR"""
#         self.ocr = PaddleOCR(
#             lang="en",
#             use_angle_cls=False,
#             use_gpu=False,
#             show_log=False,
#             det_db_box_thresh=0.3,
#             cpu_threads=4
#         )
        
#         # Patterns for NID information
#         self.dob_patterns = [
#             r'Date of Birth\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'Birth\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'DOB\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'জন্ম\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
#             r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
#         ]
        
#         self.nid_patterns = [
#             r'NID No\.?\s*:?\s*([\d\s]+)',
#             r'ID No\.?\s*:?\s*([\d\s]+)',
#             r'National ID\s*:?\s*([\d\s]+)',
#             r'([\d\s]{10,})',
#         ]
        
#         self.blood_patterns = [
#             r'Blood Group\s*:?\s*([A-Z][+-])',
#             r'Blood\s*:?\s*([A-Z][+-])',
#             r'রক্তের গ্রুপ\s*:?\s*([A-Z][+-])',
#         ]

#     def extract_text_with_rotation(self, image):
#         """Try multiple rotations to find the best text extraction"""
#         angles = [0, 90, 180, 270]
#         all_results = []
        
#         for angle in angles:
#             # Rotate image
#             if angle == 0:
#                 rotated_img = image.copy()
#             elif angle == 90:
#                 rotated_img = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
#             elif angle == 180:
#                 rotated_img = cv2.rotate(image, cv2.ROTATE_180)
#             elif angle == 270:
#                 rotated_img = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
#             # Run OCR
#             result = self.ocr.ocr(rotated_img, cls=False)
            
#             # Collect lines and compute confidence
#             lines = []
#             total_conf = 0
#             total_chars = 0
            
#             if result and result[0] is not None:
#                 for line in result[0]:
#                     text = line[1][0]
#                     conf = line[1][1]
#                     if text.strip():
#                         lines.append((text, conf))
#                         total_conf += conf * len(text)
#                         total_chars += len(text)
            
#             avg_conf = total_conf / total_chars if total_chars > 0 else 0
            
#             all_results.append({
#                 'angle': angle,
#                 'avg_conf': avg_conf,
#                 'lines': lines,
#                 'full_text': ' '.join([t for t, _ in lines])
#             })
        
#         # Sort by confidence and return best result
#         all_results.sort(key=lambda x: x['avg_conf'], reverse=True)
#         return all_results[0] if all_results else None


#     def extract_nid_number(self, text_lines, full_text):
#         """Extract NID number from text"""
#         for pattern in self.nid_patterns:
#             match = re.search(pattern, full_text, re.IGNORECASE)
#             if match:
#                 nid = match.group(1)
#                 # Remove spaces but keep the digits
#                 nid = re.sub(r'\s+', '', nid)
#                 if len(nid) >= 10 and len(nid) <= 17:
#                     return nid
#         return None

#     def extract_date_of_birth(self, text_lines, full_text):
#         """Extract date of birth from text - Handles both '05 Jan 1972' and '05Jan 1972' formats"""
        
#         # Print for debugging
#         print("Searching for DOB in lines:")
#         for i, line in enumerate(text_lines):
#             print(f"  Line {i}: {line}")
        
#         # Method 1: Look for line containing "Date of Birth" 
#         for line in text_lines:
#             if 'Date of Birth' in line or 'Birth' in line or 'DOB' in line:
#                 print(f"Found DOB label in line: {line}")
                
#                 # Try pattern with space: "05 Jan 1972"
#                 date_match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', line)
#                 if date_match:
#                     day = date_match.group(1)
#                     month = date_match.group(2).capitalize()
#                     year = date_match.group(3)
#                     return f"{day} {month} {year}"
                
#                 # Try pattern without space: "05Jan 1972" or "05Jan1972"
#                 date_match = re.search(r'(\d{1,2})([A-Za-z]+)[\s]*(\d{4})', line)
#                 if date_match:
#                     day = date_match.group(1)
#                     month = date_match.group(2).capitalize()
#                     year = date_match.group(3)
#                     return f"{day} {month} {year}"
        
#         # Method 2: Look for date pattern anywhere in text
#         # Pattern with space
#         date_match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', full_text)
#         if date_match:
#             day = date_match.group(1)
#             month = date_match.group(2).capitalize()
#             year = date_match.group(3)
#             return f"{day} {month} {year}"
        
#         # Pattern without space (like "05Jan1972" or "05Jan 1972")
#         date_match = re.search(r'(\d{1,2})([A-Za-z]+)[\s]*(\d{4})', full_text)
#         if date_match:
#             day = date_match.group(1)
#             month = date_match.group(2).capitalize()
#             year = date_match.group(3)
#             return f"{day} {month} {year}"
        
#         # Method 3: Look for any numbers that might be a date (dd mm yyyy)
#         alt_pattern = r'\b(\d{1,2})[-\s](\d{1,2})[-\s](\d{4})\b'
#         date_match = re.search(alt_pattern, full_text)
#         if date_match:
#             return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        
#         return None

#     def extract_name(self, text_lines):
#         """Extract name from text - Works for both MAHMUDUL ISLAM and HASAN MAHMUD"""
        
#         # Method 1: Look for English name after "Name" label
#         for i, line in enumerate(text_lines):
#             if 'Name' in line:
#                 print(f"Found Name label in line {i}: {line}")
                
#                 # Check if name is in the same line after colon or space
#                 if ':' in line:
#                     parts = line.split(':')
#                     if len(parts) > 1 and parts[1].strip():
#                         name = parts[1].strip()
#                         if name.isupper() and len(name) > 3:
#                             return name
                
#                 # Check next line
#                 elif i + 1 < len(text_lines):
#                     next_line = text_lines[i + 1].strip()
#                     if next_line and next_line.isupper() and len(next_line) > 3:
#                         # Skip if it contains common non-name words
#                         skip_words = ['GOVERNMENT', 'PEOPLE', 'REPUBLIC', 'BANGLADESH']
#                         if not any(word in next_line for word in skip_words):
#                             return next_line
        
#         # Method 2: Look for all caps name patterns (HASAN MAHMUD, MAHMUDUL ISLAM)
#         for line in text_lines:
#             line = line.strip()
#             if line.isupper() and len(line.split()) >= 2:
#                 # Skip lines that are likely labels
#                 skip_words = ['GOVERNMENT', 'PEOPLE', 'REPUBLIC', 'BANGLADESH', 
#                              'NATIONAL', 'ID', 'CARD', 'DATE', 'BIRTH', 
#                              'FATHER', 'MOTHER', 'NID', 'NO', 'BLOOD', 'GROUP']
#                 words = line.split()
#                 if not any(word in skip_words for word in words):
#                     # Make sure it's at least two words
#                     if len(words) >= 2:
#                         return line
        
#         return None

#     def extract_blood_group(self, full_text):
#         """Extract blood group from text"""
#         for pattern in self.blood_patterns:
#             match = re.search(pattern, full_text, re.IGNORECASE)
#             if match:
#                 return match.group(1)
#         return None

#     def extract_information(self, text_lines):
#         """Extract all information from text lines"""
#         full_text = ' '.join(text_lines)
        
#         # Print all text lines for debugging
#         print("\n--- Extracted Text Lines ---")
#         for i, line in enumerate(text_lines):
#             print(f"{i}: {line}")
#         print("---------------------------\n")
        
#         result = {
#             'name': self.extract_name(text_lines),
#             'date_of_birth': self.extract_date_of_birth(text_lines, full_text),
#             'nid_number': self.extract_nid_number(text_lines, full_text),
#             'blood_group': self.extract_blood_group(full_text)
#         }
        
#         return result

#     def process_image(self, image_path):
#         """Main method to process NID image and extract information"""
#         start_time = time.time()
        
#         try:
#             # Read image
#             image = cv2.imread(image_path)
#             if image is None:
#                 raise ValueError(f"Could not read image from {image_path}")
            
#             # Extract text with best rotation
#             best_result = self.extract_text_with_rotation(image)
            
#             if not best_result or not best_result['lines']:
#                 return {
#                     'success': False,
#                     'error': 'No text detected in image',
#                     'processing_time': time.time() - start_time
#                 }
            
#             # Extract text lines
#             text_lines = [text for text, _ in best_result['lines']]
            
#             # Extract specific information
#             extracted_info = self.extract_information(text_lines)
            
#             # Calculate overall confidence
#             high_conf_texts = [conf for _, conf in best_result['lines'] if conf > 0.7]
#             avg_confidence = sum(high_conf_texts) / len(high_conf_texts) if high_conf_texts else 0
            
#             processing_time = time.time() - start_time
            
#             print(f"\n=== FINAL EXTRACTED INFO ===")
#             print(f"Name: {extracted_info['name']}")
#             print(f"DOB: {extracted_info['date_of_birth']}")
#             print(f"NID: {extracted_info['nid_number']}")
#             print(f"Blood Group: {extracted_info['blood_group']}")
#             print(f"Confidence: {avg_confidence}")
#             print(f"Processing Time: {processing_time:.2f}s")
#             print("============================\n")
            
#             return {
#                 'success': True,
#                 'name': extracted_info['name'],
#                 'date_of_birth': extracted_info['date_of_birth'],
#                 'nid_number': extracted_info['nid_number'],
#                 # Keep these for database but they won't be in API response
#                 'filename': os.path.basename(image_path),
#                 'full_text': ' '.join(text_lines),
#                 'blood_group': extracted_info['blood_group'],
#                 'confidence_score': avg_confidence,
#                 'processing_time': processing_time,
#                 'best_angle': best_result['angle']
#             }
            
#         except Exception as e:
#             print(f"Error processing image: {str(e)}")
#             return {
#                 'success': False,
#                 'error': str(e),
#                 'processing_time': time.time() - start_time
#             }







# import cv2
# import numpy as np
# from paddleocr import PaddleOCR
# import re
# import time
# import os

# class NIDOCRService:
#     def __init__(self):
#         """Initialize the OCR service with PaddleOCR"""
#         self.ocr = PaddleOCR(
#             lang="en",
#             use_angle_cls=False,
#             use_gpu=False,
#             show_log=False,
#             det_db_box_thresh=0.3,
#             cpu_threads=4
#         )
        
#         # Patterns for NID information
#         self.dob_patterns = [
#             r'Date of Birth\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'Birth\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'DOB\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'জন্ম\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
#             r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
#             r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
#         ]
        
#         self.nid_patterns = [
#             r'NID No\.?\s*:?\s*([\d\s]+)',
#             r'ID No\.?\s*:?\s*([\d\s]+)',
#             r'National ID\s*:?\s*([\d\s]+)',
#             r'([\d\s]{10,})',
#         ]
#         # Blood group patterns REMOVED per requirements

#     def extract_text_with_rotation(self, image):
#         """Try multiple rotations to find the best text extraction"""
#         angles = [0]
#         all_results = []
        
#         for angle in angles:
#             # Rotate image
#             if angle == 0:
#                 rotated_img = image.copy()
#             elif angle == 90:
#                 rotated_img = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
#             elif angle == 180:
#                 rotated_img = cv2.rotate(image, cv2.ROTATE_180)
#             elif angle == 270:
#                 rotated_img = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
#             # Run OCR
#             result = self.ocr.ocr(rotated_img, cls=False)
            
#             # Collect lines and compute confidence
#             lines = []
#             total_conf = 0
#             total_chars = 0
            
#             if result and result[0] is not None:
#                 for line in result[0]:
#                     text = line[1][0]
#                     conf = line[1][1]
#                     if text.strip():
#                         lines.append((text, conf))
#                         total_conf += conf * len(text)
#                         total_chars += len(text)
            
#             avg_conf = total_conf / total_chars if total_chars > 0 else 0
            
#             all_results.append({
#                 'angle': angle,
#                 'avg_conf': avg_conf,
#                 'lines': lines,
#                 'full_text': ' '.join([t for t, _ in lines])
#             })
        
#         # Sort by confidence and return best result
#         all_results.sort(key=lambda x: x['avg_conf'], reverse=True)
#         return all_results[0] if all_results else None

#     def extract_nid_number(self, text_lines, full_text):
#         """Extract NID number from text"""
#         for pattern in self.nid_patterns:
#             match = re.search(pattern, full_text, re.IGNORECASE)
#             if match:
#                 nid = match.group(1)
#                 # Remove spaces but keep the digits
#                 nid = re.sub(r'\s+', '', nid)
#                 if len(nid) >= 10 and len(nid) <= 17:
#                     return nid
#         return None

#     def extract_date_of_birth(self, text_lines, full_text):
#         """Extract date of birth from text - Handles both '05 Jan 1972' and '05Jan 1972' formats"""
        
#         # Print for debugging
#         print("Searching for DOB in lines:")
#         for i, line in enumerate(text_lines):
#             print(f"  Line {i}: {line}")
        
#         # Method 1: Look for line containing "Date of Birth" 
#         for line in text_lines:
#             if 'Date of Birth' in line or 'Birth' in line or 'DOB' in line:
#                 print(f"Found DOB label in line: {line}")
                
#                 # Try pattern with space: "05 Jan 1972"
#                 date_match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', line)
#                 if date_match:
#                     day = date_match.group(1)
#                     month = date_match.group(2).capitalize()
#                     year = date_match.group(3)
#                     return f"{day} {month} {year}"
                
#                 # Try pattern without space: "05Jan 1972" or "05Jan1972"
#                 date_match = re.search(r'(\d{1,2})([A-Za-z]+)[\s]*(\d{4})', line)
#                 if date_match:
#                     day = date_match.group(1)
#                     month = date_match.group(2).capitalize()
#                     year = date_match.group(3)
#                     return f"{day} {month} {year}"
        
#         # Method 2: Look for date pattern anywhere in text
#         # Pattern with space
#         date_match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', full_text)
#         if date_match:
#             day = date_match.group(1)
#             month = date_match.group(2).capitalize()
#             year = date_match.group(3)
#             return f"{day} {month} {year}"
        
#         # Pattern without space (like "05Jan1972" or "05Jan 1972")
#         date_match = re.search(r'(\d{1,2})([A-Za-z]+)[\s]*(\d{4})', full_text)
#         if date_match:
#             day = date_match.group(1)
#             month = date_match.group(2).capitalize()
#             year = date_match.group(3)
#             return f"{day} {month} {year}"
        
#         # Method 3: Look for any numbers that might be a date (dd mm yyyy)
#         alt_pattern = r'\b(\d{1,2})[-\s](\d{1,2})[-\s](\d{4})\b'
#         date_match = re.search(alt_pattern, full_text)
#         if date_match:
#             return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        
#         return None

#     def extract_name(self, text_lines):
#         """Extract name from text - Works for both MAHMUDUL ISLAM and HASAN MAHMUD"""
        
#         # Method 1: Look for English name after "Name" label
#         for i, line in enumerate(text_lines):
#             if 'Name' in line:
#                 print(f"Found Name label in line {i}: {line}")
                
#                 # Check if name is in the same line after colon or space
#                 if ':' in line:
#                     parts = line.split(':')
#                     if len(parts) > 1 and parts[1].strip():
#                         name = parts[1].strip()
#                         if name.isupper() and len(name) > 3:
#                             return name
                
#                 # Check next line
#                 elif i + 1 < len(text_lines):
#                     next_line = text_lines[i + 1].strip()
#                     if next_line and next_line.isupper() and len(next_line) > 3:
#                         # Skip if it contains common non-name words
#                         skip_words = ['GOVERNMENT', 'PEOPLE', 'REPUBLIC', 'BANGLADESH']
#                         if not any(word in next_line for word in skip_words):
#                             return next_line
        
#         # Method 2: Look for all caps name patterns (HASAN MAHMUD, MAHMUDUL ISLAM)
#         for line in text_lines:
#             line = line.strip()
#             if line.isupper() and len(line.split()) >= 2:
#                 # Skip lines that are likely labels
#                 skip_words = ['GOVERNMENT', 'PEOPLE', 'REPUBLIC', 'BANGLADESH', 
#                              'NATIONAL', 'ID', 'CARD', 'DATE', 'BIRTH', 
#                              'FATHER', 'MOTHER', 'NID', 'NO', 'BLOOD', 'GROUP']
#                 words = line.split()
#                 if not any(word in skip_words for word in words):
#                     # Make sure it's at least two words
#                     if len(words) >= 2:
#                         return line
        
#         return None

#     def extract_information(self, text_lines):
#         """Extract all information from text lines"""
#         full_text = ' '.join(text_lines)
        
#         # Print all text lines for debugging
#         print("\n--- Extracted Text Lines ---")
#         for i, line in enumerate(text_lines):
#             print(f"{i}: {line}")
#         print("---------------------------\n")
        
#         result = {
#             'name': self.extract_name(text_lines),
#             'date_of_birth': self.extract_date_of_birth(text_lines, full_text),
#             'nid_number': self.extract_nid_number(text_lines, full_text)
#             # Blood group extraction REMOVED per requirements
#         }
        
#         return result

#     def process_image(self, image_path):
#         """Main method to process NID image and extract information"""
#         start_time = time.time()
        
#         try:
#             # Read image
#             image = cv2.imread(image_path)
#             if image is None:
#                 raise ValueError(f"Could not read image from {image_path}")
            
#             # Extract text with best rotation
#             best_result = self.extract_text_with_rotation(image)
            
#             if not best_result or not best_result['lines']:
#                 return {
#                     'success': False,
#                     'error': 'No text detected in image',
#                     'processing_time': time.time() - start_time
#                 }
            
#             # Extract text lines
#             text_lines = [text for text, _ in best_result['lines']]
            
#             # Extract specific information
#             extracted_info = self.extract_information(text_lines)
            
#             # Calculate overall confidence
#             high_conf_texts = [conf for _, conf in best_result['lines'] if conf > 0.7]
#             avg_confidence = sum(high_conf_texts) / len(high_conf_texts) if high_conf_texts else 0
            
#             processing_time = time.time() - start_time
            
#             print(f"\n=== FINAL EXTRACTED INFO ===")
#             print(f"Name: {extracted_info['name']}")
#             print(f"DOB: {extracted_info['date_of_birth']}")
#             print(f"NID: {extracted_info['nid_number']}")
#             # Blood group print REMOVED per requirements
#             print(f"Confidence: {avg_confidence}")
#             print(f"Processing Time: {processing_time:.2f}s")
#             print("============================\n")
            
#             return {
#                 'success': True,
#                 'name': extracted_info['name'],
#                 'date_of_birth': extracted_info['date_of_birth'],
#                 'nid_number': extracted_info['nid_number'],
#                 # Keep these for database but they won't be in API response
#                 'filename': os.path.basename(image_path),
#                 'full_text': ' '.join(text_lines),
#                 # 'blood_group' key REMOVED per requirements
#                 'confidence_score': avg_confidence,
#                 'processing_time': processing_time,
#                 'best_angle': best_result['angle']
#             }
            
#         except Exception as e:
#             print(f"Error processing image: {str(e)}")
#             return {
#                 'success': False,
#                 'error': str(e),
#                 'processing_time': time.time() - start_time
#             }










# import cv2
# import numpy as np
# from paddleocr import PaddleOCR
# import re
# import time
# import os

# class NIDOCRService:
#     def __init__(self):
#         """Initialize the OCR service with PaddleOCR"""
#         self.ocr = PaddleOCR(
#             lang="en",
#             use_angle_cls=False,
#             use_gpu=False,
#             show_log=False,
#             det_db_box_thresh=0.3,
#             cpu_threads=4
#         )
        
#         # Patterns for NID information
#         self.nid_patterns = [
#             r'NID No\.?\s*:?\s*([\d\s]+)',
#             r'ID No\.?\s*:?\s*([\d\s]+)',
#             r'National ID\s*:?\s*([\d\s]+)',
#             r'\b(\d{10,17})\b'
#         ]

#     def extract_text_with_rotation(self, image):
#         """Process image at 0 degrees only (optimized)"""
#         angles = [0]  # Only process original orientation
#         all_results = []
        
#         for angle in angles:
#             rotated_img = image.copy()
            
#             # Run OCR
#             result = self.ocr.ocr(rotated_img, cls=False)
            
#             # Collect lines and compute confidence
#             lines = []
#             total_conf = 0
#             total_chars = 0
            
#             if result and result[0] is not None:
#                 for line in result[0]:
#                     text = line[1][0].strip()
#                     conf = line[1][1]
#                     if text and len(text) > 2:
#                         lines.append((text, conf))
#                         total_conf += conf * len(text)
#                         total_chars += len(text)
            
#             avg_conf = total_conf / total_chars if total_chars > 0 else 0
            
#             all_results.append({
#                 'angle': angle,
#                 'avg_conf': avg_conf,
#                 'lines': lines,
#                 'full_text': ' '.join([t for t, _ in lines])
#             })
        
#         return all_results[0] if all_results else None

#     def extract_nid_number(self, full_text):
#         """Extract NID number from text"""
#         for pattern in self.nid_patterns:
#             match = re.search(pattern, full_text, re.IGNORECASE)
#             if match:
#                 nid = re.sub(r'\s+', '', match.group(1))
#                 if 10 <= len(nid) <= 17 and nid.isdigit():
#                     return nid
#         return None

#     def extract_date_of_birth(self, text_lines, full_text):
#         """Extract date of birth with flexible format handling"""
#         # Search in lines first (more accurate)
#         for line in text_lines:
#             if any(kw in line for kw in ['Date of Birth', 'DOB', 'Birth', 'জন্ম']):
#                 # Handle formats: "10Oct 1986", "10 Oct 1986", "10Oct1986"
#                 match = re.search(r'(\d{1,2})\s*([A-Za-z]{3,})\s*(\d{4})', line)
#                 if match:
#                     day, month, year = match.groups()
#                     month_abbr = month[:3].capitalize()
                    
#                     # Validate month
#                     valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
#                                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
#                     if month_abbr in valid_months:
#                         return f"{day} {month_abbr} {year}"
        
#         # Fallback: search entire text
#         match = re.search(r'(\d{1,2})\s*([A-Za-z]{3,})\s*(\d{4})', full_text)
#         if match:
#             day, month, year = match.groups()
#             month_abbr = month[:3].capitalize()
            
#             valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
#                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
#             if month_abbr in valid_months:
#                 return f"{day} {month_abbr} {year}"
        
#         return None

#     def extract_name(self, text_lines, confidence_scores):
#         """Extract name using confidence scores and positional context"""
#         candidates = []
        
#         # Helper function to add spaces in concatenated names (e.g., "MAHBUBALAM" -> "MAHBUB ALAM")
#         def add_spaces_to_name(name):
#             # If already has spaces, return as-is
#             if ' ' in name:
#                 return name
            
#             # Strategy 1: Split at reasonable position (after 5-8 characters for common first names)
#             if len(name) > 8:
#                 # Try splitting after 6-8 characters (common first name length)
#                 split_pos = min(8, max(6, len(name) // 2))
#                 first = name[:split_pos]
#                 second = name[split_pos:]
                
#                 # Ensure both parts are reasonable length
#                 if len(first) >= 4 and len(second) >= 3:
#                     return f"{first} {second}"
            
#             # Strategy 2: If still concatenated, split roughly in middle
#             if len(name) > 6:
#                 mid = len(name) // 2
#                 return f"{name[:mid]} {name[mid:]}"
            
#             # Return original if no good split found
#             return name
        
#         # Skip obvious non-name text
#         def is_valid_candidate(text):
#             text_upper = text.upper()
#             skip_phrases = [
#                 'GOVERNMENT', 'PEOPLE', 'REPUBLIC', 'BANGLADESH', 'NATIONAL', 
#                 'ID', 'CARD', 'DATE', 'BIRTH', 'NID', 'NO', 'FATHER', 'MOTHER',
#                 'BLOOD', 'GROUP', 'R', 'AR', 'MR', 'MRS', 'HOLDER', 'SIGNATURE',
#                 '/NATIONALDCARD', 'IDENTITY', 'CITIZEN', 'ISSUED', 'VALID'
#             ]
#             return (
#                 len(text) >= 4 and 
#                 not any(phrase in text_upper for phrase in skip_phrases) and
#                 text.isupper()  # Names are typically all caps on NID
#             )
        
#         # Collect all valid candidates with scores
#         for i, line in enumerate(text_lines):
#             line = line.strip()
#             if not line or i >= len(confidence_scores):
#                 continue
            
#             if is_valid_candidate(line):
#                 # Add spaces to concatenated names
#                 formatted_name = add_spaces_to_name(line)
                
#                 # Base score = OCR confidence
#                 score = confidence_scores[i]
                
#                 # Positional bonuses (critical for NID layout)
#                 if i > 0:
#                     prev_line = text_lines[i-1].upper()
#                     if 'NAME' in prev_line:
#                         score += 0.5  # High bonus: immediately after "Name" label
#                     elif any(kw in prev_line for kw in ['DATE OF BIRTH', 'DOB', 'BIRTH']):
#                         score += 0.3  # Medium bonus: after DOB (common NID layout)
                
#                 # Length bonus for reasonable name length
#                 if 5 <= len(line) <= 30:
#                     score += 0.1
                
#                 candidates.append({
#                     'name': formatted_name,
#                     'original': line,
#                     'score': score,
#                     'confidence': confidence_scores[i],
#                     'line_index': i
#                 })
        
#         # Debug output
#         if candidates:
#             print(f"\n[Name Selection] Found {len(candidates)} candidates:")
#             for c in candidates:
#                 print(f"  Line {c['line_index']}: '{c['original']}' → '{c['name']}' | Score: {c['score']:.2f} (Conf: {c['confidence']:.2f})")
        
#         # Return highest scoring candidate
#         if candidates:
#             best = max(candidates, key=lambda x: x['score'])
#             print(f"[Name Selection] ✅ SELECTED: '{best['name']}' (Score: {best['score']:.2f})")
#             return best['name']
        
#         return None

#     def extract_information(self, text_lines, confidence_scores):
#         """Extract all information from text lines"""
#         full_text = ' '.join(text_lines)
        
#         # Print all text lines for debugging
#         print("\n--- Extracted Text Lines ---")
#         for i, line in enumerate(text_lines):
#             conf = confidence_scores[i] if i < len(confidence_scores) else 0
#             print(f"{i}: {line} (conf: {conf:.2f})")
#         print("---------------------------\n")
        
#         # Extract fields
#         name = self.extract_name(text_lines, confidence_scores)
#         dob = self.extract_date_of_birth(text_lines, full_text)
#         nid = self.extract_nid_number(full_text)
        
#         return {
#             'name': name,
#             'date_of_birth': dob,
#             'nid_number': nid
#         }

#     def process_image(self, image_path):
#         """Main method to process NID image and extract information"""
#         start_time = time.time()
        
#         try:
#             # Read image (in color format)
#             image = cv2.imread(image_path)
#             if image is None:
#                 raise ValueError(f"Could not read image from {image_path}")
            
#             # ✅ Convert to grayscale for optimal OCR accuracy
#             image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
#             # Extract text
#             best_result = self.extract_text_with_rotation(image)
            
#             if not best_result or not best_result['lines']:
#                 return {
#                     'success': False,
#                     'error': 'No text detected in image',
#                     'processing_time': time.time() - start_time
#                 }
            
#             # Separate text lines and confidence scores
#             text_lines = [text for text, _ in best_result['lines']]
#             confidence_scores = [conf for _, conf in best_result['lines']]
            
#             # Extract information
#             extracted_info = self.extract_information(text_lines, confidence_scores)
            
#             # Calculate metrics
#             processing_time = time.time() - start_time
#             avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
#             # Final output
#             print(f"\n{'='*50}")
#             print("FINAL EXTRACTION RESULTS")
#             print(f"{'='*50}")
#             print(f"Name          : {extracted_info['name']}")
#             print(f"Date of Birth : {extracted_info['date_of_birth']}")
#             print(f"NID Number    : {extracted_info['nid_number']}")
#             print(f"Confidence    : {avg_confidence:.2%}")
#             print(f"Processing    : {processing_time:.2f}s")
#             print(f"Image Mode    : Grayscale")
#             print(f"{'='*50}\n")
            
#             return {
#                 'success': True,
#                 'name': extracted_info['name'],
#                 'date_of_birth': extracted_info['date_of_birth'],
#                 'nid_number': extracted_info['nid_number'],
#                 'filename': os.path.basename(image_path),
#                 'full_text': ' '.join(text_lines),
#                 'confidence_score': avg_confidence,
#                 'processing_time': processing_time
#             }
            
#         except Exception as e:
#             print(f"[ERROR] Processing failed: {str(e)}")
#             return {
#                 'success': False,
#                 'error': str(e),
#                 'processing_time': time.time() - start_time
#             }





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