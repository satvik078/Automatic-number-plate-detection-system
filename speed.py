import cv2
import time

class SpeedTracker:
    def __init__(self, scale_factor=0.05, fps=30):
        """
        Initializes speed tracker using frame-time analysis.

        :param scale_factor: Conversion factor (pixels to meters).
        :param fps: Frame rate of the video (default: 30 FPS).
        """
        self.scale_factor = scale_factor  # Convert pixels to meters
        self.fps = fps
        self.vehicle_positions = {}  # Stores vehicle positions with timestamps

    def track_vehicle(self, frame, vehicle_id, bbox):
        """
        Tracks vehicle movement and estimates speed.

        :param frame: Current video frame.
        :param vehicle_id: Unique ID assigned to detected vehicle.
        :param bbox: Bounding box of vehicle (x, y, w, h).
        :return: Speed in km/h (if measurable).
        """
        x, y, w, h = bbox
        center = (x + w // 2, y + h // 2)  # Calculate center of the vehicle

        current_time = time.time()

        if vehicle_id in self.vehicle_positions:
            prev_position, prev_time = self.vehicle_positions[vehicle_id]

            # Calculate pixel displacement
            pixel_distance = ((center[0] - prev_position[0]) ** 2 + (center[1] - prev_position[1]) ** 2) ** 0.5
            real_distance = pixel_distance * self.scale_factor  # Convert to meters

            time_elapsed = current_time - prev_time

            # Compute speed (m/s), then convert to km/h
            speed_mps = real_distance / time_elapsed
            speed_kmph = speed_mps * 3.6  # Convert meters per second to km/h

            # Update vehicle position
            self.vehicle_positions[vehicle_id] = (center, current_time)

            return round(speed_kmph, 2)

        # First detection (initialize tracking)
        self.vehicle_positions[vehicle_id] = (center, current_time)
        return None
