from number_plate import PlateFinder
import cv2
from ocr import recognize_text, validate_indian_plate_pattern
from advanced_speed import AdvancedSpeedCalculator
from unique_vehicle_tracker import UniqueVehicleTracker
import time
import threading
from collections import defaultdict
import csv
import json
from datetime import datetime
import os

def process_frame_optimized(frame, findPlate, speed_calculator, vehicle_tracker, frame_count):
    """Optimized frame processing function with unique vehicle detection"""
    results = []
    
    # Processing every frame for detection
    possible_plates = findPlate.find_possible_plates(frame)
    
    if possible_plates is not None:
        for i, plate_img in enumerate(possible_plates):
            recognized_plate = recognize_text(plate_img)
            
            if recognized_plate and validate_indian_plate_pattern(recognized_plate):
                # plate coordinates
                plate_coords = findPlate.corresponding_area[i]
                if plate_coords:
                    x, y = plate_coords
                    # vehicle bounding box
                    vehicle_bbox = (
                        max(0, x - 80), max(0, y - 120),
                        min(frame.shape[1] - x, 250), min(frame.shape[0] - y, 150)
                    )
                    
                    # Calculating speed 
                    vehicle_id = f"vehicle_{x}_{y}"  # Simple ID based on position
                    speed = speed_calculator.estimate_speed_hybrid(
                        frame, vehicle_bbox, vehicle_id
                    )
                    
                    # Checking if this is a new unique vehicle
                    is_new, unique_id, vehicle_info = vehicle_tracker.detect_vehicle(
                        recognized_plate, vehicle_bbox, frame_count, speed
                    )
                    
                    if is_new:
                        # adding to results if it's a new detection
                        results.append({
                            'plate': recognized_plate,
                            'speed': speed,
                            'bbox': vehicle_bbox,
                            'plate_coords': (x, y),
                            'plate_image': plate_img,
                            'frame_number': frame_count,
                            'vehicle_id': unique_id,
                            'is_new_detection': True,
                            'vehicle_info': vehicle_info
                        })
                    else:
                        results.append({
                            'plate': recognized_plate,
                            'speed': speed,
                            'bbox': vehicle_bbox,
                            'plate_coords': (x, y),
                            'plate_image': plate_img,
                            'frame_number': frame_count,
                            'vehicle_id': unique_id,
                            'is_new_detection': False,
                            'vehicle_info': vehicle_info
                        })
    
    return results

class ResultLogger:
    def __init__(self, output_dir="results"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        #  timestamp for this session
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        #  result storage
        self.detected_plates = []
        self.unique_plates = set()
        self.total_detections = 0
        
        #  CSV file for detailed results
        self.csv_filename = os.path.join(output_dir, f"anpr_results_{self.timestamp}.csv")
        self.init_csv()
        
        #  summary file
        self.summary_filename = os.path.join(output_dir, f"anpr_summary_{self.timestamp}.json")
        
    def init_csv(self):
        """Initialize CSV file with headers"""
        with open(self.csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Timestamp', 'Frame_Number', 'Vehicle_ID', 'Plate_Number', 'Speed_kmh', 
                'Vehicle_X', 'Vehicle_Y', 'Speed_Status'
            ])
    
    def log_unique_detection(self, result, frame_number):
        """Log a unique vehicle detection"""
        plate = result['plate']
        speed = result['speed'] if result['speed'] is not None else 'N/A'
        bbox = result['bbox']
        vehicle_id = result['vehicle_id']
        vehicle_info = result['vehicle_info']
        
        # logging for new detection
        if result['is_new_detection']:
            # Adding to unique plates set
            self.unique_plates.add(plate)
            self.total_detections += 1
            
            #  detection record
            detection_record = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'frame_number': frame_number,
                'vehicle_id': vehicle_id,
                'plate': plate,
                'speed': speed,
                'bbox': bbox,
                'speed_status': vehicle_info['speed_status']
            }
            
            self.detected_plates.append(detection_record)
            
            
            with open(self.csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    detection_record['timestamp'],
                    frame_number,
                    vehicle_id,
                    plate,
                    speed,
                    bbox[0],  # Vehicle X
                    bbox[1],  # Vehicle Y
                    vehicle_info['speed_status']
                ])
    
    def save_summary(self):
        """Save summary statistics"""
        summary = {
            'session_timestamp': self.timestamp,
            'total_detections': self.total_detections,
            'unique_plates': len(self.unique_plates),
            'unique_plate_numbers': list(self.unique_plates),
            'detection_rate': f"{self.total_detections} detections",
            'files_created': {
                'detailed_results': self.csv_filename,
                'summary': self.summary_filename
            }
        }
        
        with open(self.summary_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

if __name__ == "__main__":
    # Initializing components
    findPlate = PlateFinder(minPlateArea=1500, maxPlateArea=25000)
    speed_calculator = AdvancedSpeedCalculator(
        fps=30, 
        reference_distance_meters=30,  # Assuming 30 meters reference
        reference_pixels=200 
    )
    
    # Initializing unique vehicle tracker
    vehicle_tracker = UniqueVehicleTracker(
        similarity_threshold=0.8,  # 80% similarity to consider same vehicle
        min_speed_samples=3        #speed samples for final speed calculation
    )
    
    cap = cv2.VideoCapture('Automatic Number Plate Recognition (ANPR) _ Vehicle Number Plate Recognition (1).mp4')
    
    # result logger
    logger = ResultLogger("results")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_delay = int(1000 / fps) if fps > 0 else 33 
    
    print(f"Video FPS: {fps}, Frame delay: {frame_delay}ms")
    print(f"Results will be saved to: {logger.output_dir}/")
    print("Starting ANPR processing...")
    print("Controls: 'q' to quit, 's' to skip frames faster")
    print("=" * 60)

    frame_count = 0
    skip_frames = False
    
    while cap.isOpened():
        ret, img = cap.read()
        
        if not ret:
            break
            
        frame_count += 1
        
        #  frame
        results = process_frame_optimized(img, findPlate, speed_calculator, vehicle_tracker, frame_count)
        
        # results on frame
        display_img = img.copy()
        
        for result in results:
            plate = result['plate']
            speed = result['speed']
            bbox = result['bbox']
            plate_coords = result['plate_coords']
            plate_img = result['plate_image']
            vehicle_id = result['vehicle_id']
            is_new = result['is_new_detection']
            vehicle_info = result['vehicle_info']
            
            # Logging the detection (only new ones will be logged)
            logger.log_unique_detection(result, frame_count)
            
            vx, vy, vw, vh = bbox
            vx2, vy2 = vx + vw, vy + vh
            
            #  visual output for new detections to avoid clutter
            if is_new:
                # vehicle bounding box for new detections
                cv2.rectangle(display_img, (vx, vy), (vx2, vy2), (0, 255, 0), 3)
                
                # vehicle ID and plate text
                cv2.putText(display_img, f"Vehicle #{vehicle_id}: {plate}", 
                           (vx, vy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # speed status
                cv2.putText(display_img, f"{vehicle_info['speed_status']}", 
                           (vx, vy - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Printing new detection
                print(f" NEW VEHICLE #{vehicle_id:2d} | {plate:12} | Frame {frame_count:4d} | {vehicle_info['speed_status']}")
                
                # individual plate image for new detections
                cv2.imshow(f'Vehicle #{vehicle_id} - {plate}', plate_img)
            
            #  speed for existing vehicles
            elif speed is not None:
                final_speed = vehicle_info.get('final_speed')
                if final_speed:
                    print(f" Vehicle #{vehicle_id:2d} | {plate:12} | Final Speed: {final_speed} km/h")
        
        # frame info to display
        cv2.putText(display_img, f"Frame: {frame_count}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_img, f"Unique Plates: {len(logger.unique_plates)}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_img, f"Total Detections: {logger.total_detections}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # displaying main frame
        cv2.imshow('ANPR System - Indian Number Plates', display_img)
        cv2.imshow('Original Video', img)
        
        
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            skip_frames = not skip_frames
            print(f"⚡ Skip frames mode: {'ON' if skip_frames else 'OFF'}")
        
        # Adjusting delay for smoother playback
        if not skip_frames:
            time.sleep(0.02)  # Small delay for smoother playback
        
        # Printing progress every 50 frames
        if frame_count % 50 == 0:
            print(f"📊 Processed {frame_count} frames | Detected {len(logger.unique_plates)} unique plates")
    
    # final vehicle summary
    vehicle_summary = vehicle_tracker.get_summary()
    
    #  final results
    summary = logger.save_summary()
    
    print("\n" + "=" * 70)
    print(" VIDEO PROCESSING COMPLETED!")
    print("=" * 70)
    print(f" FINAL STATISTICS:")
    print(f"   • Total Frames Processed: {frame_count}")
    print(f"   • Unique Vehicles Detected: {vehicle_summary['total_unique_vehicles']}")
    print(f"   • Vehicles with Speed Data: {vehicle_summary['vehicles_with_speed']}")
    print(f"   • Detection Rate: {vehicle_summary['total_unique_vehicles']/frame_count*100:.2f}% efficiency")
    
    print(f"\n RESULTS SAVED TO:")
    print(f"   • Detailed CSV: {summary['files_created']['detailed_results']}")
    print(f"   • Summary JSON: {summary['files_created']['summary']}")
    
    print(f"\n DETECTED VEHICLES:")
    print("-" * 70)
    print(f"{'ID':>3} | {'Plate Number':^12} | {'Speed (km/h)':^12} | {'Status':^20}")
    print("-" * 70)
    
    for vehicle in vehicle_summary['vehicles']:
        vehicle_id = vehicle['id']
        plate = vehicle['plate']
        speed = vehicle['speed'] if vehicle['speed'] else 'N/A'
        status = vehicle['speed_status'][:18] + '...' if len(vehicle['speed_status']) > 18 else vehicle['speed_status']
        
        print(f"{vehicle_id:3d} | {plate:^12} | {str(speed):^12} | {status:^20}")
    
    cap.release()
    cv2.destroyAllWindows()
