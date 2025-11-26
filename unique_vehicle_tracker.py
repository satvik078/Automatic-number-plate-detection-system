import time
import cv2
import numpy as np
from collections import defaultdict
from datetime import datetime

class UniqueVehicleTracker:
    def __init__(self, similarity_threshold=0.8, min_speed_samples=3):
        """
        Tracking unique vehicles and detect each plate only once
        
        :param similarity_threshold: Threshold for considering plates as same vehicle
        :param min_speed_samples: Minimum speed samples before finalizing speed
        """
        self.detected_plates = {}  # plate_number -> vehicle_info
        self.vehicle_counter = 0
        self.similarity_threshold = similarity_threshold
        self.min_speed_samples = min_speed_samples
        
        # Speed tracking for each plate
        self.speed_data = defaultdict(list)
        self.position_history = defaultdict(list)
        
    def is_similar_plate(self, new_plate, existing_plates):
        """Checking if new plate is similar to any existing plate"""
        for existing_plate in existing_plates:
            # Calculating similarity ratio
            similarity = self.calculate_similarity(new_plate, existing_plate)
            if similarity >= self.similarity_threshold:
                return existing_plate
        return None
    
    def calculate_similarity(self, plate1, plate2):
        """Calculating similarity between two plates using character matching"""
        if len(plate1) != len(plate2):
            return 0.0
        
        matches = sum(1 for a, b in zip(plate1, plate2) if a == b)
        return matches / len(plate1)
    
    def add_speed_sample(self, plate_number, speed):
        """Adding speed sample for a plate"""
        if speed is not None and 5 <= speed <= 150:  # Valid speed range
            self.speed_data[plate_number].append(speed)
    
    def get_final_speed(self, plate_number):
        """Getting final averaged speed for a plate"""
        speeds = self.speed_data[plate_number]
        if len(speeds) >= self.min_speed_samples:
            # Removing outliers and calculating average
            speeds_array = np.array(speeds)
            q75, q25 = np.percentile(speeds_array, [75, 25])
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            
            filtered_speeds = speeds_array[
                (speeds_array >= lower_bound) & (speeds_array <= upper_bound)
            ]
            
            if len(filtered_speeds) > 0:
                return round(np.mean(filtered_speeds), 1)
        
        return None
    
    def detect_vehicle(self, plate_number, bbox, frame_number, speed=None):
        """
        Detecting and track a unique vehicle
        
        Returns: (is_new_detection, vehicle_id, vehicle_info)
        """
        # Checking if this plate is similar to any existing plate
        similar_plate = self.is_similar_plate(plate_number, self.detected_plates.keys())
        
        if similar_plate:
            # Updating existing vehicle with speed data
            vehicle_info = self.detected_plates[similar_plate]
            if speed is not None:
                self.add_speed_sample(similar_plate, speed)
                # Updating speed if we have enough samples
                final_speed = self.get_final_speed(similar_plate)
                if final_speed is not None:
                    vehicle_info['final_speed'] = final_speed
                    vehicle_info['speed_status'] = 'Finalized'
                else:
                    vehicle_info['speed_status'] = f'Calculating... ({len(self.speed_data[similar_plate])}/{self.min_speed_samples})'
            
            return False, vehicle_info['vehicle_id'], vehicle_info
        
        else:
            # New unique vehicle detected
            self.vehicle_counter += 1
            vehicle_info = {
                'vehicle_id': self.vehicle_counter,
                'plate_number': plate_number,
                'first_detected_frame': frame_number,
                'detection_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'bbox': bbox,
                'final_speed': None,
                'speed_status': 'Not calculated yet',
                'total_speed_samples': 0
            }
            
            # Adding initial speed sample if available
            if speed is not None:
                self.add_speed_sample(plate_number, speed)
                vehicle_info['speed_status'] = f'Calculating... ({len(self.speed_data[plate_number])}/{self.min_speed_samples})'
            
            self.detected_plates[plate_number] = vehicle_info
            
            return True, self.vehicle_counter, vehicle_info
    
    def finalize_all_speeds(self):
        """Finalizing speeds for all detected vehicles"""
        for plate_number, vehicle_info in self.detected_plates.items():
            if vehicle_info['final_speed'] is None:
                final_speed = self.get_final_speed(plate_number)
                if final_speed is not None:
                    vehicle_info['final_speed'] = final_speed
                    vehicle_info['speed_status'] = 'Finalized'
                else:
                    speed_samples = len(self.speed_data[plate_number])
                    if speed_samples > 0:
                        # Using average of available samples even if less than minimum
                        vehicle_info['final_speed'] = round(np.mean(self.speed_data[plate_number]), 1)
                        vehicle_info['speed_status'] = f'Estimated from {speed_samples} samples'
                    else:
                        vehicle_info['speed_status'] = 'No speed data available'
            
            vehicle_info['total_speed_samples'] = len(self.speed_data[plate_number])
    
    def get_summary(self):
        """Getting summary of all detected vehicles"""
        self.finalize_all_speeds()
        
        summary = {
            'total_unique_vehicles': self.vehicle_counter,
            'vehicles_with_speed': len([v for v in self.detected_plates.values() if v['final_speed'] is not None]),
            'vehicles': []
        }
        
        # Sorting vehicles by detection order
        sorted_vehicles = sorted(
            self.detected_plates.values(),
            key=lambda x: x['vehicle_id']
        )
        
        for vehicle in sorted_vehicles:
            summary['vehicles'].append({
                'id': vehicle['vehicle_id'],
                'plate': vehicle['plate_number'],
                'speed': vehicle['final_speed'],
                'speed_status': vehicle['speed_status'],
                'detection_time': vehicle['detection_time'],
                'frame': vehicle['first_detected_frame'],
                'speed_samples': vehicle['total_speed_samples']
            })
        
        return summary
    
    def is_already_detected(self, plate_number):
        """Checking if a plate has already been detected"""
        return self.is_similar_plate(plate_number, self.detected_plates.keys()) is not None
