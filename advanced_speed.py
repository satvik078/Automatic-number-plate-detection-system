import cv2
import numpy as np
import time
from collections import defaultdict, deque

class AdvancedSpeedCalculator:
    def __init__(self, fps=30, reference_distance_meters=50, reference_pixels=None):
        """
        Advanced speed calculation using optical flow and reference measurements
        
        :param fps: Frame rate of the video
        :param reference_distance_meters: Known real-world distance for calibration
        :param reference_pixels: Corresponding pixel distance for calibration
        """
        self.fps = fps
        self.reference_distance_meters = reference_distance_meters
        self.reference_pixels = reference_pixels or 300  # Default calibration
        
        # Calculating meters per pixel
        self.meters_per_pixel = self.reference_distance_meters / self.reference_pixels
        
        # Vehicle tracking data
        self.vehicle_tracks = defaultdict(lambda: {
            'positions': deque(maxlen=10),
            'timestamps': deque(maxlen=10),
            'speeds': deque(maxlen=5)
        })
        
        # Optical flow parameters
        self.lk_params = {
            'winSize': (15, 15),
            'maxLevel': 2,
            'criteria': (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        }
        
        # Feature detection parameters
        self.feature_params = {
            'maxCorners': 100,
            'qualityLevel': 0.3,
            'minDistance': 7,
            'blockSize': 7
        }
        
        self.prev_gray = None
        
    def detect_vehicle_features(self, roi):
        """Detect good features to track within vehicle ROI"""
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        corners = cv2.goodFeaturesToTrack(gray_roi, mask=None, **self.feature_params)
        return corners
    
    def calculate_optical_flow_speed(self, current_frame, vehicle_bbox, vehicle_id):
        """Calculate speed using optical flow analysis"""
        current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        current_time = time.time()
        
        x, y, w, h = vehicle_bbox
        
        # Extracting vehicle ROI
        roi = current_frame[y:y+h, x:x+w]
        
        if self.prev_gray is not None:
            # Detecting features in the previous frame's vehicle region
            prev_roi = self.prev_gray[y:y+h, x:x+w]
            p0 = cv2.goodFeaturesToTrack(prev_roi, mask=None, **self.feature_params)
            
            if p0 is not None and len(p0) > 0:
                # Adjusting coordinates to full frame
                p0[:, :, 0] += x
                p0[:, :, 1] += y
                
                # Calculating optical flow
                p1, st, err = cv2.calcOpticalFlowPyrLK(
                    self.prev_gray, current_gray, p0, None, **self.lk_params
                )
                
                # Select good points
                good_new = p1[st == 1]
                good_old = p0[st == 1]
                
                if len(good_new) > 5:  # minimum points for reliable calculation
                    # Calculating displacement
                    displacement = np.mean(np.sqrt(
                        (good_new[:, 0] - good_old[:, 0])**2 + 
                        (good_new[:, 1] - good_old[:, 1])**2
                    ))
                    
                    # Converting to real-world speed
                    distance_meters = displacement * self.meters_per_pixel
                    time_seconds = 1.0 / self.fps
                    speed_mps = distance_meters / time_seconds
                    speed_kmph = speed_mps * 3.6
                    
                    # Storing tracking history
                    track_data = self.vehicle_tracks[vehicle_id]
                    track_data['positions'].append((x + w//2, y + h//2))
                    track_data['timestamps'].append(current_time)
                    track_data['speeds'].append(speed_kmph)
                    
                    # Returning smoothed speed
                    return self.get_smoothed_speed(vehicle_id)
        
        # Storing current frame for next iteration
        self.prev_gray = current_gray.copy()
        
        # Initializing tracking for new vehicle
        track_data = self.vehicle_tracks[vehicle_id]
        track_data['positions'].append((x + w//2, y + h//2))
        track_data['timestamps'].append(current_time)
        
        return None
    
    def calculate_centroid_speed(self, vehicle_bbox, vehicle_id):
        """Alternative method: Calculate speed based on centroid movement"""
        x, y, w, h = vehicle_bbox
        center = (x + w // 2, y + h // 2)
        current_time = time.time()
        
        track_data = self.vehicle_tracks[vehicle_id]
        track_data['positions'].append(center)
        track_data['timestamps'].append(current_time)
        
        if len(track_data['positions']) >= 2:
            # last two positions
            pos1 = track_data['positions'][-2]
            pos2 = track_data['positions'][-1]
            time1 = track_data['timestamps'][-2]
            time2 = track_data['timestamps'][-1]
            
            # Calculating displacement
            pixel_distance = np.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
            time_diff = time2 - time1
            
            if time_diff > 0:
                
                distance_meters = pixel_distance * self.meters_per_pixel
                speed_mps = distance_meters / time_diff
                speed_kmph = speed_mps * 3.6
                
                track_data['speeds'].append(speed_kmph)
                return self.get_smoothed_speed(vehicle_id)
        
        return None
    
    def get_smoothed_speed(self, vehicle_id):
        """Get smoothed speed using moving average"""
        speeds = self.vehicle_tracks[vehicle_id]['speeds']
        
        if len(speeds) == 0:
            return None
        
        # Removing outliers (speeds > 200 km/h or < 0)
        valid_speeds = [s for s in speeds if 0 <= s <= 200]
        
        if not valid_speeds:
            return None
        
        # weighted average (recent speeds have more weight)
        weights = np.linspace(0.5, 1.0, len(valid_speeds))
        weighted_speed = np.average(valid_speeds, weights=weights)
        
        return round(weighted_speed, 1)
    
    def calibrate_with_reference(self, known_distance_meters, measured_pixels):
        """Calibrate the system with a known reference measurement"""
        self.reference_distance_meters = known_distance_meters
        self.reference_pixels = measured_pixels
        self.meters_per_pixel = known_distance_meters / measured_pixels
        print(f"Calibrated: {self.meters_per_pixel:.4f} meters per pixel")
    
    def estimate_speed_hybrid(self, current_frame, vehicle_bbox, vehicle_id):
        """
        Hybrid approach combining optical flow and centroid tracking
        """
        # optical flow first
        optical_flow_speed = self.calculate_optical_flow_speed(
            current_frame, vehicle_bbox, vehicle_id
        )
        
        # calculating centroid-based speed
        centroid_speed = self.calculate_centroid_speed(vehicle_bbox, vehicle_id)
        
        #  optical flow if available and reasonable, otherwise using centroid
        if optical_flow_speed is not None and 5 <= optical_flow_speed <= 150:
            return optical_flow_speed
        elif centroid_speed is not None and 5 <= centroid_speed <= 150:
            return centroid_speed
        else:
            return None
    
    def reset_tracking(self):
        """Reset all tracking data"""
        self.vehicle_tracks.clear()
        self.prev_gray = None
