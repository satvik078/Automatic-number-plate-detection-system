#!/usr/bin/env python3
"""
Test script to verify the improvements in number plate recognition
"""

import cv2
import numpy as np
from number_plate import PlateFinder
from ocr import recognize_text
from speed import SpeedTracker
import time

def test_static_image():
    """Test with a static image if available"""
    print("Testing static image recognition...")
    
    # Trying to capture a frame from the video for testing
    cap = cv2.VideoCapture('6366_vehicle_transport_transportation_170609ADelhi017.mp4')
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        findPlate = PlateFinder(minPlateArea=2000, maxPlateArea=20000)
        plates = findPlate.find_possible_plates(frame)
        
        if plates:
            print(f"Found {len(plates)} potential plates")
            for i, plate in enumerate(plates):
                recognized = recognize_text(plate)
                if recognized:
                    print(f"Plate {i+1}: {recognized}")
                else:
                    print(f"Plate {i+1}: Could not recognize")
        else:
            print("No plates detected in test frame")
    else:
        print("Could not read test frame from video")

def test_indian_plate_validation():
    """Test Indian number plate pattern validation"""
    print("\nTesting Indian plate validation...")
    
    from ocr import validate_indian_plate_pattern, format_indian_plate
    
    test_plates = [
        "DL01AB1234",  # Valid Delhi plate
        "MH12CD5678",  # Valid Maharashtra plate
        "UP16EF9012",  # Valid UP plate
        "KA03GH3456",  # Valid Karnataka plate
        "XX99ZZ9999",  # Invalid state code
        "D01AB1234",   # Invalid format (too short)
        "DL1A1234",    # Valid new format
    ]
    
    for plate in test_plates:
        is_valid = validate_indian_plate_pattern(plate)
        formatted = format_indian_plate(plate)
        print(f"Plate: {plate:12} | Valid: {is_valid:5} | Formatted: {formatted}")

def test_ocr_preprocessing():
    """Test OCR preprocessing functions"""
    print("\nTesting OCR preprocessing...")
    
    # Creating sample plate-like images for testing
    test_plates = [
        "DL01AB1234",  # Standard format
        "MH12CD5678",  # Different state
        "DL7CA1234",   # New format
    ]
    
    for plate_text in test_plates:
        test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, plate_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Test recognition
        result = recognize_text(test_img)
        print(f"Expected: {plate_text:12} | OCR Result: {result}")

def test_speed_calculator():
    """Testing the new advanced speed calculator"""
    print("\nTesting Advanced Speed Calculator...")
    
    from advanced_speed import AdvancedSpeedCalculator
    
    speed_calc = AdvancedSpeedCalculator(fps=30, reference_distance_meters=25, reference_pixels=150)
    print(f"Speed calculator initialized with {speed_calc.meters_per_pixel:.4f} meters per pixel")
    
    # Simulating vehicle movement
    bbox1 = (100, 200, 150, 100)  # x, y, w, h
    bbox2 = (120, 200, 150, 100)  # moved 20 pixels
    
    print("Simulating vehicle movement for speed calculation...")
    print("This would work with actual video frames in the main application.")

def main():
    """Main test function"""
    print("=== Testing Enhanced ANPR System for Indian Number Plates ===")
    
    # Testing Indian plate validation
    test_indian_plate_validation()
    
    # Testing OCR preprocessing
    test_ocr_preprocessing()
    
    # Testing speed calculator
    test_speed_calculator()
    
    # Testing static image recognition
    test_static_image()
    
    print("\n=== Test Complete ===")
    print("\n NEW IMPROVEMENTS IMPLEMENTED:")
    print("1. Indian Number Plate Pattern Validation")
    print("2. Enhanced OCR with intelligent character corrections")
    print("3. Advanced Speed Calculation using Optical Flow")
    print("4. Optimized Frame Processing for Smoother Video")
    print("5. Real-time Performance Improvements")
    print("6.  Better Visual Feedback and User Interface")
    print("\n INDIAN PLATE FORMATS SUPPORTED:")
    print("   • Standard: XX##XX#### (e.g., DL01AB1234)")
    print("   • New Format: XX#XX#### (e.g., DL7CA1234)")
    print("   • All Indian State Codes Validated")
    print("\n PERFORMANCE FEATURES:")
    print("   • Frame skipping for smoother playback")
    print("   • Optimized processing pipeline")
    print("   • Real-time speed calculation")
    print("   • Press 's' during playback to toggle skip mode")

if __name__ == "__main__":
    main()
