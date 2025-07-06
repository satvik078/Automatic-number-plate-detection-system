#!/usr/bin/env python3
"""
ANPR Results Viewer
View and analyze the results from the ANPR system
"""

import pandas as pd
import json
import os
import glob
from datetime import datetime

def find_latest_results(results_dir="results"):
    """Find the most recent result files"""
    if not os.path.exists(results_dir):
        print(f"Results directory '{results_dir}' not found!")
        return None, None
    
    # Find CSV files
    csv_files = glob.glob(os.path.join(results_dir, "anpr_results_*.csv"))
    json_files = glob.glob(os.path.join(results_dir, "anpr_summary_*.json"))
    
    if not csv_files:
        print("No result files found!")
        return None, None
    
    # Get the latest files
    latest_csv = max(csv_files, key=os.path.getctime)
    latest_json = max(json_files, key=os.path.getctime)
    
    return latest_csv, latest_json

def display_summary(json_file):
    """Display summary statistics"""
    with open(json_file, 'r') as f:
        summary = json.load(f)
    
    print("=" * 70)
    print("🚗 ANPR SYSTEM - ANALYSIS RESULTS")
    print("=" * 70)
    print(f"📅 Session: {summary['session_timestamp']}")
    print(f"🎯 Total Detections: {summary['total_detections']}")
    print(f"🆔 Unique Vehicles: {summary['unique_plates']}")
    print(f"📊 Detection Rate: {summary['detection_rate']}")
    
    print(f"\n🚗 DETECTED VEHICLE PLATES:")
    for i, plate in enumerate(summary['unique_plate_numbers'], 1):
        state_code = plate[:2]
        state_names = {
            'DL': 'Delhi', 'MH': 'Maharashtra', 'UP': 'Uttar Pradesh',
            'KA': 'Karnataka', 'TN': 'Tamil Nadu', 'GJ': 'Gujarat',
            'RJ': 'Rajasthan', 'WB': 'West Bengal', 'AP': 'Andhra Pradesh',
            'TG': 'Telangana', 'KL': 'Kerala', 'PB': 'Punjab',
            'HR': 'Haryana', 'BR': 'Bihar', 'OD': 'Odisha',
            'JH': 'Jharkhand', 'CG': 'Chhattisgarh', 'MP': 'Madhya Pradesh'
        }
        state_name = state_names.get(state_code, 'Unknown State')
        print(f"   {i:2d}. {plate} ({state_name})")

def display_detailed_results(csv_file):
    """Display detailed detection results for unique vehicles"""
    df = pd.read_csv(csv_file)
    
    print(f"\n📋 UNIQUE VEHICLE DETECTION LOG:")
    print("-" * 80)
    print(f"{'ID':>3} | {'Timestamp':^19} | {'Frame':^6} | {'Plate':^12} | {'Speed':^10} | {'Status':^15}")
    print("-" * 80)
    
    for index, row in df.iterrows():
        vehicle_id = row['Vehicle_ID']
        timestamp = row['Timestamp']
        frame = row['Frame_Number']
        plate = row['Plate_Number']
        speed = row['Speed_kmh']
        status = row['Speed_Status'] if 'Speed_Status' in row else 'Unknown'
        
        if speed == 'N/A':
            speed_display = "No data"
        else:
            speed_display = f"{speed} km/h"
        
        # Truncate status if too long
        status_short = status[:13] + '...' if len(str(status)) > 15 else str(status)
        
        print(f"{vehicle_id:3d} | {timestamp:^19} | {frame:^6} | {plate:^12} | {speed_display:^10} | {status_short:^15}")
    
    print()

def analyze_speed_data(csv_file):
    """Analyze speed statistics"""
    df = pd.read_csv(csv_file)
    
    # Filter out N/A speeds and convert to numeric
    speed_data = df[df['Speed_kmh'] != 'N/A']['Speed_kmh'].astype(float)
    
    if len(speed_data) > 0:
        print(f"\n📈 SPEED ANALYSIS:")
        print("-" * 30)
        print(f"🎯 Vehicles with Speed Data: {len(speed_data)}")
        print(f"⚡ Average Speed: {speed_data.mean():.1f} km/h")
        print(f"🏎️  Maximum Speed: {speed_data.max():.1f} km/h")
        print(f"🐌 Minimum Speed: {speed_data.min():.1f} km/h")
        
        # Speed categories
        slow = len(speed_data[speed_data < 30])
        medium = len(speed_data[(speed_data >= 30) & (speed_data < 60)])
        fast = len(speed_data[speed_data >= 60])
        
        print(f"\n🚦 SPEED CATEGORIES:")
        print(f"   🟢 Slow (< 30 km/h): {slow} vehicles")
        print(f"   🟡 Medium (30-60 km/h): {medium} vehicles")
        print(f"   🔴 Fast (> 60 km/h): {fast} vehicles")
    else:
        print(f"\n📈 SPEED ANALYSIS:")
        print("-" * 30)
        print("⚠️  No speed data available in this session")

def main():
    """Main function"""
    print("🔍 ANPR Results Viewer")
    print("=" * 30)
    
    # Find latest results
    csv_file, json_file = find_latest_results()
    
    if not csv_file:
        return
    
    print(f"📂 Loading results from:")
    print(f"   CSV: {os.path.basename(csv_file)}")
    print(f"   JSON: {os.path.basename(json_file)}")
    
    # Display results
    display_summary(json_file)
    display_detailed_results(csv_file)
    analyze_speed_data(csv_file)
    
    print("\n" + "=" * 70)
    print("✅ Results analysis completed!")
    print(f"📁 Full results available in: {os.path.dirname(csv_file)}/")

if __name__ == "__main__":
    main()
