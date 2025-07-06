import cv2
import easyocr
import numpy as np
import re

# Initialize EasyOCR with English language support
reader = easyocr.Reader(['en'])

# Indian state codes for validation
INDIAN_STATE_CODES = [
    'AP', 'AR', 'AS', 'BR', 'CG', 'GA', 'GJ', 'HR', 'HP', 'JK', 'JH', 'KA', 'KL', 'MP', 'MH', 'MN', 'ML', 'MZ', 'NL', 'OD', 'PB', 'RJ', 'SK', 'TN', 'TG', 'TR', 'UP', 'UK', 'WB',
    'AN', 'CH', 'DH', 'DD', 'DL', 'LD', 'PY'
]

def preprocess_plate_image(image):
    """ Enhanced preprocessing for better OCR accuracy """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Apply histogram equalization to improve contrast
    equalized = cv2.equalizeHist(filtered)
    
    # Apply Gaussian blur to smooth the image
    blurred = cv2.GaussianBlur(equalized, (3, 3), 0)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Apply morphological operations to clean up the image
    kernel = np.ones((2, 2), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
    
    return morph

def validate_indian_plate_pattern(text):
    """ Validate if text matches Indian number plate patterns """
    if not text or len(text) < 8:
        return False
    
    # Indian number plate patterns:
    # Old format: XX ## XX #### (10 chars) - e.g., DL 01 AB 1234
    # New format: XX ## XX #### (10 chars) - e.g., DL 7C A3702 
    # Some variants: XX ## X #### (9 chars)
    
    patterns = [
        r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',  # Standard format: DL01AB1234
        r'^[A-Z]{2}[0-9]{2}[A-Z]{1}[0-9]{4}$',  # Variant: DL01A1234
        r'^[A-Z]{2}[0-9]{1}[A-Z]{2}[0-9]{4}$',  # New format: DL7AB1234
        r'^[A-Z]{2}[0-9]{1}[A-Z]{1}[0-9]{4}$',  # New variant: DL7A1234
    ]
    
    for pattern in patterns:
        if re.match(pattern, text):
            # Check if state code is valid
            state_code = text[:2]
            if state_code in INDIAN_STATE_CODES:
                return True
    
    return False

def format_indian_plate(text):
    """ Format the plate text to match Indian standards """
    if not text:
        return ""
    
    # Clean and format
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    if len(cleaned) >= 8:
        # Try to format as Indian plate
        if len(cleaned) == 10 and validate_indian_plate_pattern(cleaned):
            return cleaned
        elif len(cleaned) == 9:
            # Try to add missing character for standard format
            state = cleaned[:2]
            if state in INDIAN_STATE_CODES:
                return cleaned
    
    return cleaned if len(cleaned) >= 6 else ""

def clean_text(text):
    """ Clean and format the recognized text for Indian plates """
    if not text:
        return ""
    
    # Remove special characters and keep only alphanumeric
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    # Filter out very short results
    if len(cleaned) < 6:
        return ""
    
    # Common OCR corrections for license plates
    corrections = {
        'O': '0', 'I': '1', 'S': '5', 'Z': '2', 'G': '6', 'B': '8', 'Q': '0'
    }
    
    # Apply corrections more intelligently
    corrected = ""
    for i, char in enumerate(cleaned):
        if i < 2:  # State code - should be letters
            if char.isdigit():
                # Convert common digit misreads back to letters
                digit_to_letter = {'0': 'O', '1': 'I', '5': 'S', '2': 'Z', '6': 'G', '8': 'B'}
                corrected += digit_to_letter.get(char, char)
            else:
                corrected += char
        elif i < 4:  # District code - should be numbers
            if char.isalpha() and char in corrections:
                corrected += corrections[char]
            else:
                corrected += char
        elif i < 6:  # Series - should be letters
            if char.isdigit():
                digit_to_letter = {'0': 'O', '1': 'I', '5': 'S', '2': 'Z', '6': 'G', '8': 'B'}
                corrected += digit_to_letter.get(char, char)
            else:
                corrected += char
        else:  # Number - should be digits
            if char.isalpha() and char in corrections:
                corrected += corrections[char]
            else:
                corrected += char
    
    # Format as Indian plate
    formatted = format_indian_plate(corrected)
    
    # Validate the final result
    if validate_indian_plate_pattern(formatted):
        return formatted
    
    # Return cleaned text if pattern doesn't match but is reasonable length
    return corrected if len(corrected) >= 6 else ""

def recognize_text(image):
    """ Enhanced text recognition with better preprocessing """
    try:
        # Apply enhanced preprocessing
        processed_img = preprocess_plate_image(image)
        
        # Resize to optimal size for OCR (maintain aspect ratio)
        height, width = processed_img.shape
        target_height = 100
        target_width = int(width * (target_height / height))
        resized_img = cv2.resize(processed_img, (target_width, target_height))
        
        # Try OCR with different configurations
        results = reader.readtext(resized_img, 
                                 allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                                 width_ths=0.7,
                                 height_ths=0.7)
        
        # Extract text with confidence filtering
        detected_texts = []
        for _, text, confidence in results:
            if confidence > 0.5:  # Only keep high confidence results
                cleaned = clean_text(text)
                if cleaned:
                    detected_texts.append(cleaned)
        
        # Join all detected text
        final_text = "".join(detected_texts)
        
        # If no good result, try with original grayscale image
        if not final_text:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_resized = cv2.resize(gray, (target_width, target_height))
            results = reader.readtext(gray_resized, 
                                     allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            for _, text, confidence in results:
                if confidence > 0.3:
                    cleaned = clean_text(text)
                    if cleaned:
                        final_text = cleaned
                        break
        
        return final_text if final_text else None
        
    except Exception as e:
        print(f"OCR Error: {e}")
        return None
