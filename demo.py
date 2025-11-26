#!/usr/bin/env python3
"""
Quick Demo of Enhanced ANPR System
Shows all the new features and improvements
"""

import cv2
import time
from number_plate import PlateFinder
from ocr import recognize_text, validate_indian_plate_pattern
from advanced_speed import AdvancedSpeedCalculator

def demo_indian_plate_validation():
    """Demo the Indian plate validation system"""
    print("🇮🇳 INDIAN NUMBER PLATE VALIDATION DEMO")
    print("=" * 50)
    
    test_plates = [
        "DL01AB1234",  # Delhi - Valid
        "MH12CD5678",  # Maharashtra - Valid  
        "UP16EF9012",  # Uttar Pradesh - Valid
        "KA03GH3456",  # Karnataka - Valid
        "DL7CA1234",   # Delhi New Format - Valid
        "XX99ZZ9999",  # Invalid state code
        "ABC123",      # Too short
    ]
    
    for plate in test_plates:
        is_valid = validate_indian_plate_pattern(plate)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{plate:12} | {status}")
    
    print()

def demo_speed_calculation():
    """Demo the advanced speed calculation"""
    print("⚡ ADVANCED SPEED CALCULATION DEMO")
    print("=" * 50)
    
    speed_calc = AdvancedSpeedCalculator(
        fps=30, 
        reference_distance_meters=25, 
        reference_pixels=150
    )
    
    print(f"🎯 Calibration: {speed_calc.meters_per_pixel:.4f} meters per pixel")
    print(f"📹 Frame Rate: {speed_calc.fps} FPS")
    print(f"🔧 Reference: {speed_calc.reference_distance_meters}m = {speed_calc.reference_pixels} pixels")
    print()

def demo_video_processing():
    """Demo video processing with a few frames"""
    print("🎥 VIDEO PROCESSING DEMO")
    print("=" * 50)
    
    cap = cv2.VideoCapture('6366_vehicle_transport_transportation_170609ADelhi017.mp4')
    
    if not cap.isOpened():
        print("❌ Could not open video file")
        return
    
    # Initializing components
    findPlate = PlateFinder(minPlateArea=1500, maxPlateArea=25000)
    speed_calculator = AdvancedSpeedCalculator(fps=30)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Video Info: {fps} FPS, {total_frames} total frames")
    print("🔍 Processing first few frames for demo...")
    
    processed_frames = 0
    detections = 0
    
    for frame_num in range(min(100, total_frames)):  # Processing first 100 frames
        ret, frame = cap.read()
        
        if not ret:
            break
            
        processed_frames += 1
        
        # Processing frame
        possible_plates = findPlate.find_possible_plates(frame)
        
        if possible_plates is not None:
            for i, plate_img in enumerate(possible_plates):
                recognized_plate = recognize_text(plate_img)
                
                if recognized_plate and validate_indian_plate_pattern(recognized_plate):
                    detections += 1
                    print(f"   ✅ Frame {frame_num:3d}: Detected {recognized_plate}")
        
        # Showing progress every 20 frames
        if frame_num % 20 == 0:
            print(f"   📊 Processed {frame_num} frames...")
    
    cap.release()
    
    print(f"✅ Demo completed: {detections} valid plates detected in {processed_frames} frames")
    print()

def main():
    """Main demo function"""
    print("🚀 ENHANCED ANPR SYSTEM - LIVE DEMO")
    print("=" * 60)
    print()
    
    # Demo 1: Indian plate validation
    demo_indian_plate_validation()
    
    # Demo 2: Speed calculation setup
    demo_speed_calculation()
    
    # Demo 3: Quick video processing
    demo_video_processing()
    
    print("🎉 DEMO FEATURES SUMMARY:")
    print("=" * 30)
    print("✅ Indian Number Plate Pattern Validation")
    print("✅ Enhanced OCR with Smart Corrections")  
    print("✅ Advanced Speed Calculation (Optical Flow)")
    print("✅ Optimized Video Processing")
    print("✅ Real-time Result Logging")
    print("✅ Visual Output with Bounding Boxes")
    print("✅ Comprehensive Result Analysis")
    print()
    print("🎮 TO RUN FULL SYSTEM:")
    print("   python main.py          # Run full ANPR system")
    print("   python view_results.py  # View saved results")
    print("   python test_improvements.py  # Test all features")

if __name__ == "__main__":
    main()
