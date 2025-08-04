# -*- coding: utf-8 -*-
"""
Veo 3 Image-to-Video Performance Comparison
Tests both fast and quality models across 10 different prompts
"""

import time
import json
import os
from datetime import datetime
from google import genai
from google.genai import types
import matplotlib.image as img
import matplotlib.pyplot as plt
import pandas as pd
from tkinter import filedialog, Tk
from PIL import Image
import mimetypes

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = {
        'google.genai': 'google-genai',
        'matplotlib': 'matplotlib',
        'pandas': 'pandas',
        'PIL': 'Pillow',
        'tkinter': 'tkinter (usually comes with Python)'
    }
    
    missing_packages = []
    
    for package, install_name in required_packages.items():
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(install_name)
    
    if missing_packages:
        print(f"\n🔧 To install missing packages, run:")
        for package in missing_packages:
            if package != 'tkinter (usually comes with Python)':
                print(f"   pip install {package}")
        
        if 'tkinter (usually comes with Python)' in missing_packages:
            print("   For tkinter: Usually comes with Python. On Ubuntu/Debian: sudo apt-get install python3-tk")
        
        return False
    
    print("🎉 All required packages are installed!")
    return True

# Initialize client
PROJECT_ID = "veo-testing"  # Your Google Cloud project ID
GCS_BUCKET = "fk-test-veo"  # Your GCS bucket name
LOCATION = "us-central1"

print("🔍 Checking requirements...")
if not check_requirements():
    print("❌ Please install missing packages before running the script.")
    exit(1)

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Model configurations
video_model = "veo-3.0-generate-preview"  # Quality model
video_model_fast = "veo-3.0-fast-generate-preview"  # Fast model
gemini_model = "gemini-2.5-flash"

# Test configuration
starting_image = None  # Will be set by user selection
results = []

def select_image_file():
    """Open file dialog to select an image file"""
    print("📁 Opening file dialog to select image...")
    
    # Hide the main tkinter window
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # Define supported image formats
    filetypes = [
        ("All Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
        ("PNG files", "*.png"),
        ("JPEG files", "*.jpg *.jpeg"),
        ("BMP files", "*.bmp"),
        ("GIF files", "*.gif"),
        ("TIFF files", "*.tiff"),
        ("WebP files", "*.webp"),
        ("All files", "*.*")
    ]
    
    # Open file dialog
    file_path = filedialog.askopenfilename(
        title="Select an image for video generation",
        filetypes=filetypes,
        initialdir=os.getcwd()
    )
    
    root.destroy()
    
    if not file_path:
        print("❌ No file selected. Exiting...")
        return None
    
    # Validate file exists and is an image
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    # Check if it's a valid image file
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type or not mime_type.startswith('image/'):
        print(f"❌ Selected file is not a valid image: {file_path}")
        return None
    
    print(f"✅ Selected image: {os.path.basename(file_path)}")
    print(f"📏 File size: {os.path.getsize(file_path) / 1024:.1f} KB")
    
    return file_path

def validate_and_process_image(image_path):
    """Validate and process the selected image"""
    try:
        # Open and validate image with PIL
        with Image.open(image_path) as pil_image:
            print(f"🖼️  Image format: {pil_image.format}")
            print(f"📐 Image dimensions: {pil_image.size[0]} x {pil_image.size[1]}")
            print(f"🎨 Image mode: {pil_image.mode}")
            
            # Convert to RGB if necessary (for RGBA, etc.)
            if pil_image.mode not in ['RGB', 'L']:
                print(f"🔄 Converting image from {pil_image.mode} to RGB")
                pil_image = pil_image.convert('RGB')
            
            # Check image size (Veo has limits)
            width, height = pil_image.size
            max_dimension = 1920  # Typical max for video generation
            
            if max(width, height) > max_dimension:
                print(f"⚠️  Image is large ({width}x{height}). Consider resizing for better performance.")
                
                # Ask user if they want to resize
                resize_choice = input(f"Resize image to fit within {max_dimension}px? (y/n): ").lower().strip()
                if resize_choice == 'y':
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        new_width = max_dimension
                        new_height = int(height * (max_dimension / width))
                    else:
                        new_height = max_dimension
                        new_width = int(width * (max_dimension / height))
                    
                    pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"✅ Resized to: {new_width} x {new_height}")
                    
                    # Save the resized image
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    resized_path = f"{base_name}_resized.png"
                    pil_image.save(resized_path, "PNG")
                    print(f"💾 Saved resized image as: {resized_path}")
                    return resized_path
            
            # If no processing needed, return original path
            return image_path
            
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return None

def display_selected_image(image_path):
    """Display the selected image"""
    try:
        fig, axis = plt.subplots(1, 1, figsize=(10, 8))
        image_data = img.imread(image_path)
        axis.imshow(image_data)
        axis.set_title(f"Selected Image: {os.path.basename(image_path)}", fontsize=14, fontweight='bold')
        axis.axis("off")
        plt.tight_layout()
        
        # Save the plot instead of showing it directly
        plot_filename = f"selected_image_preview.png"
        plt.savefig(plot_filename, bbox_inches='tight', dpi=150)
        print(f"📊 Image preview saved as: {plot_filename}")
        
        # Try to show the plot
        try:
            plt.show()
        except:
            print("💡 Open the preview file to see your selected image")
        
        plt.close()  # Clean up
        return True
    except Exception as e:
        print(f"❌ Error displaying image: {e}")
        return False

def check_gcs_bucket_access():
    """Check if GCS bucket is accessible"""
    try:
        from google.cloud import storage
        
        # Initialize storage client
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET)
        
        # Test bucket access
        if bucket.exists():
            print(f"✅ GCS bucket '{GCS_BUCKET}' is accessible")
            
            # Create test results folder structure
            test_folder = f"veo3_test_results/"
            print(f"📁 Videos will be stored in: gs://{GCS_BUCKET}/{test_folder}")
            return True
        else:
            print(f"❌ GCS bucket '{GCS_BUCKET}' not found or not accessible")
            return False
            
    except ImportError:
        print("⚠️  google-cloud-storage not installed. Videos will still be generated and stored in GCS.")
        print(f"📁 Videos will be stored in: gs://{GCS_BUCKET}/veo3_test_results/")
        return True
    except Exception as e:
        print(f"⚠️  Could not verify GCS bucket access: {e}")
        print(f"📁 Proceeding anyway. Videos will be stored in: gs://{GCS_BUCKET}/veo3_test_results/")
        return True

def save_results(results, filename=None):
    """Save results to JSON file and optionally to GCS"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"veo3_comparison_results_{timestamp}.json"
    
    # Save locally
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Results saved locally to {filename}")
    
    # Try to upload to GCS as well
    try:
        from google.cloud import storage
        
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"veo3_test_results/{filename}")
        
        blob.upload_from_filename(filename)
        print(f"☁️  Results also uploaded to: gs://{GCS_BUCKET}/veo3_test_results/{filename}")
        
    except ImportError:
        print("📝 Install google-cloud-storage to automatically upload results to GCS")
    except Exception as e:
        print(f"⚠️  Could not upload results to GCS: {e}")

def setup_image_selection():
    """Handle the complete image selection process"""
    global starting_image
    
    print("🎬 VEO 3 IMAGE-TO-VIDEO COMPARISON TEST")
    print("=" * 50)
    print(f"📋 Project: {PROJECT_ID}")
    print(f"🪣 GCS Bucket: {GCS_BUCKET}")
    print("📋 This script will test 10 different prompts on both Fast and Quality models")
    print("⏱️  Expected total runtime: 20-40 minutes")
    
    # Check GCS bucket access
    print(f"\n🔍 Checking GCS bucket access...")
    check_gcs_bucket_access()
    
    print("\n⚠️  Requirements:")
    print("   - Vertex AI API enabled")
    print("   - Sufficient API quota for video generation")
    print("   - GCS bucket write permissions")
    print("   - Select a high-quality image for best results")
    
    # Image selection options
    print("\n📁 IMAGE SELECTION OPTIONS:")
    print("1. Browse and select image file")
    print("2. Use a specific file path")
    print("3. Exit")
    
    while True:
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            # File dialog selection
            selected_path = select_image_file()
            if selected_path:
                processed_path = validate_and_process_image(selected_path)
                if processed_path:
                    starting_image = processed_path
                    break
            else:
                continue
                
        elif choice == "2":
            # Manual path input
            file_path = input("Enter the full path to your image file: ").strip()
            if os.path.exists(file_path):
                processed_path = validate_and_process_image(file_path)
                if processed_path:
                    starting_image = processed_path
                    break
            else:
                print(f"❌ File not found: {file_path}")
                continue
                
        elif choice == "3":
            print("👋 Exiting...")
            return False
            
        else:
            print("❌ Invalid option. Please select 1, 2, or 3.")
            continue
    
    # Display selected image
    print(f"\n✅ Image ready: {starting_image}")
    if not display_selected_image(starting_image):
        print("⚠️  Could not display image, but will proceed with testing")
    
    # Final confirmation
    confirm = input(f"\n🚀 Proceed with testing using '{os.path.basename(starting_image)}'? (y/n): ").lower().strip()
    return confirm == 'y'

# 10 Different Image-to-Video Prompts
test_prompts = [
    {
        "name": "Dynamic Camera Movement",
        "prompt": "Cinematic dolly zoom into the subject with dramatic lighting changes, creating a vertigo effect",
        "description": "Tests camera motion capabilities"
    },
    {
        "name": "Nature Animation",
        "prompt": "Gentle wind causing natural elements to sway, with birds flying across the scene in slow motion",
        "description": "Tests environmental animation"
    },
    {
        "name": "Character Movement",
        "prompt": "Subject slowly turns head with natural facial expressions, hair flowing in breeze with subtle eye movements",
        "description": "Tests character animation"
    },
    {
        "name": "Weather Effects",
        "prompt": "Light rain begins to fall with puddles forming, mist rolling in creating atmospheric depth",
        "description": "Tests weather and particle effects"
    },
    {
        "name": "Time-lapse Style",
        "prompt": "Fast-paced time-lapse showing shadows moving across the scene with changing light conditions",
        "description": "Tests temporal effects"
    },
    {
        "name": "Cinematic Lighting",
        "prompt": "Golden hour lighting transition with lens flares and volumetric lighting, creating cinematic atmosphere",
        "description": "Tests lighting transitions"
    },
    {
        "name": "Object Interaction",
        "prompt": "Objects in the scene begin to move and interact with each other in a realistic physics simulation",
        "description": "Tests object physics"
    },
    {
        "name": "Emotional Narrative",
        "prompt": "Melancholic mood with soft color grading, creating an emotional storytelling atmosphere with gentle movements",
        "description": "Tests mood and cinematography"
    },
    {
        "name": "Action Sequence",
        "prompt": "High-energy action with quick camera movements, dynamic motion blur and rapid scene transitions",
        "description": "Tests action and motion"
    },
    {
        "name": "Surreal Art Style",
        "prompt": "Surrealist transformation with dreamlike elements, colors shifting and reality bending effects",
        "description": "Tests artistic style generation"
    }
]

def show_video_result(video, title):
    """Display video information and save locally"""
    print(f"\n=== {title} ===")
    
    # Create a safe filename from title
    safe_filename = title.lower().replace(' ', '_').replace('-', '_')
    safe_filename = ''.join(c for c in safe_filename if c.isalnum() or c == '_')
    
    if isinstance(video, str):
        # GCS URI - download and save locally
        filename = f"{safe_filename}.mp4"
        print(f"📹 Video generated and stored at: {video}")
        
        try:
            # Try to download the video for local viewing
            import subprocess
            result = subprocess.run(['gsutil', 'cp', video, filename], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"💾 Downloaded locally as: {filename}")
                print(f"🎬 You can view the video using: open {filename} (macOS) or start {filename} (Windows)")
            else:
                print(f"⚠️  Could not download video locally. View it at: {video}")
        except FileNotFoundError:
            print("⚠️  gsutil not found. Install Google Cloud SDK to download videos locally.")
            print(f"🔗 View video at: {video}")
    else:
        # Video bytes - save directly
        filename = f"{safe_filename}.mp4"
        with open(filename, "wb") as out_file:
            out_file.write(video)
        print(f"💾 Video saved as: {filename}")
        print(f"🎬 You can view the video using: open {filename} (macOS) or start {filename} (Windows)")
    
    return filename

def get_image_mime_type(image_path):
    """Get the correct MIME type for the image"""
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        # Fallback based on extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.gif': 'image/gif',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        mime_type = mime_map.get(ext, 'image/png')  # Default to PNG
    return mime_type

def test_model(model_name, prompt_config, test_id):
    """Test a single model with a prompt configuration"""
    print(f"\n{'='*60}")
    print(f"🎬 TESTING: {model_name}")
    print(f"📝 Prompt: {prompt_config['name']}")
    print(f"📋 Description: {prompt_config['description']}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Get the correct MIME type for the image
        mime_type = get_image_mime_type(starting_image)
        print(f"🖼️  Source image: {os.path.basename(starting_image)} ({mime_type})")
        
        # Generate GCS output path for storing videos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_type = "fast" if "fast" in model_name else "quality"
        video_filename = f"{test_id}_{model_type}_{prompt_config['name'].lower().replace(' ', '_')}_{timestamp}.mp4"
        gcs_output_path = f"gs://{GCS_BUCKET}/veo3_test_results/{video_filename}"
        
        print(f"📁 Target GCS path: {gcs_output_path}")
        print(f"🚀 Submitting generation request...")
        print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S')}")
        
        operation = client.models.generate_videos(
            model=model_name,
            prompt=prompt_config['prompt'],
            image=types.Image.from_file(location=starting_image, mime_type=mime_type),
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                output_gcs_uri=gcs_output_path,  # Store videos in GCS
                number_of_videos=1,
                duration_seconds=8,
                resolution="1080p",
                person_generation="allow_adult",
                enhance_prompt=True,
            ),
        )
        
        print(f"✅ Request submitted successfully!")
        print(f"🆔 Operation ID: {operation.name}")
        print(f"🔄 Status: {operation.operation}")
        print(f"📊 Waiting for video generation to complete...")
        
        # Enhanced progress tracking
        check_count = 0
        last_status = None
        
        # Wait for completion and track time with detailed logging
        while not operation.done:
            check_count += 1
            elapsed = time.time() - start_time
            
            # Get fresh operation status
            try:
                operation = client.operations.get(operation)
                current_status = operation.operation if hasattr(operation, 'operation') else 'PROCESSING'
                
                # Only print status if it changed or every 10 checks
                if current_status != last_status or check_count % 10 == 0:
                    print(f"⏳ [{elapsed:6.1f}s] Check #{check_count:2d} - Status: {current_status}")
                    last_status = current_status
                
                # Print detailed progress every 30 seconds
                if check_count % 6 == 0:  # Every 6th check (30 seconds if checking every 5s)
                    print(f"📈 Progress Update:")
                    print(f"   ⏰ Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
                    print(f"   🔄 Status checks: {check_count}")
                    print(f"   📊 Current operation: {operation.name}")
                    
                    # Estimate remaining time based on typical generation times
                    if model_type == "fast":
                        estimated_total = 120  # ~2 minutes for fast model
                    else:
                        estimated_total = 300  # ~5 minutes for quality model
                    
                    remaining = max(0, estimated_total - elapsed)
                    print(f"   ⏱️  Estimated remaining: {remaining:.0f}s ({remaining/60:.1f} minutes)")
                
            except Exception as status_error:
                print(f"⚠️  Could not get operation status: {status_error}")
            
            # Dynamic sleep interval - shorter at first, longer later
            if elapsed < 60:
                sleep_time = 5   # Check every 5 seconds for first minute
            elif elapsed < 180:
                sleep_time = 10  # Check every 10 seconds for next 2 minutes
            else:
                sleep_time = 15  # Check every 15 seconds after that
            
            print(f"💤 Sleeping for {sleep_time}s before next check...")
            time.sleep(sleep_time)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n🎉 GENERATION COMPLETED!")
        print(f"⏰ Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"🔍 Final operation status: {operation.operation if hasattr(operation, 'operation') else 'COMPLETED'}")
        
        if operation.response:
            video_data = operation.result.generated_videos[0].video
            success = True
            error_msg = None
            
            print(f"✅ Video generation successful!")
            
            # Display result
            model_type_display = "Fast" if "fast" in model_name else "Quality"
            title = f"{prompt_config['name']} - {model_type_display}"
            
            # Since we're using GCS output, we'll get a URI
            if hasattr(video_data, 'uri') and video_data.uri:
                print(f"🎬 Video URI received: {video_data.uri}")
                show_video_result(video_data.uri, title)
                output_type = "gcs_uri"
                gcs_path = video_data.uri
                print(f"📁 Video stored at: {gcs_path}")
            elif hasattr(video_data, 'video_bytes'):
                print(f"📦 Video bytes received: {len(video_data.video_bytes)} bytes")
                show_video_result(video_data.video_bytes, title)
                output_type = "bytes"
                gcs_path = gcs_output_path  # Use intended path
            else:
                print(f"⚠️  Unexpected video data format")
                output_type = "unknown"
                gcs_path = gcs_output_path
                
        else:
            success = False
            error_msg = "No response received from operation"
            output_type = None
            gcs_path = None
            print(f"❌ No response received from operation")
            
    except Exception as e:
        end_time = time.time()
        total_time = end_time - start_time
        success = False
        error_msg = str(e)
        output_type = None
        gcs_path = None
        
        print(f"\n❌ ERROR OCCURRED!")
        print(f"⏰ Time before error: {total_time:.1f}s")
        print(f"🔍 Error details: {error_msg}")
        print(f"📋 Error type: {type(e).__name__}")
    
    # Record results
    result = {
        'test_id': test_id,
        'model': 'Fast' if 'fast' in model_name else 'Quality',
        'model_name': model_name,
        'prompt_name': prompt_config['name'],
        'prompt_description': prompt_config['description'],
        'prompt_text': prompt_config['prompt'],
        'latency_seconds': total_time,
        'success': success,
        'error_message': error_msg,
        'output_type': output_type,
        'gcs_path': gcs_path if success else None,
        'gcs_bucket': GCS_BUCKET,
        'timestamp': datetime.now().isoformat()
    }
    
    results.append(result)
    
    # Summary of this test
    print(f"\n📊 TEST SUMMARY:")
    print(f"   ⏰ Duration: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"   ✅ Status: {'SUCCESS' if success else 'FAILED'}")
    if success and gcs_path:
        print(f"   📁 Location: {gcs_path}")
    if error_msg:
        print(f"   ❌ Error: {error_msg}")
    
    print(f"{'='*60}")
    
    return result

def run_comparison_test():
    """Run the complete comparison test"""
    print("\n" + "="*70)
    print("🎬 STARTING VEO 3 COMPREHENSIVE COMPARISON TEST")
    print("="*70)
    
    overall_start_time = time.time()
    
    # Display starting image info
    if starting_image:
        try:
            file_size = os.path.getsize(starting_image) / 1024
            print(f"📁 Source image: {os.path.basename(starting_image)}")
            print(f"📏 File size: {file_size:.1f} KB")
            
            # Get image dimensions
            with Image.open(starting_image) as img:
                print(f"📐 Dimensions: {img.size[0]} x {img.size[1]} pixels")
                print(f"🎨 Mode: {img.mode}")
            
            # Display image one more time
            fig, axis = plt.subplots(1, 1, figsize=(8, 6))
            axis.imshow(img.imread(starting_image))
            axis.set_title("Source Image for All Tests")
            axis.axis("off")
            
            # Save the plot
            source_plot = "source_image_for_tests.png"
            plt.savefig(source_plot, bbox_inches='tight', dpi=150)
            print(f"📊 Source image preview saved as: {source_plot}")
            
            try:
                plt.show()
            except:
                print("💡 Open the preview file to see the source image")
            
            plt.close()
        except Exception as e:
            print(f"⚠️  Could not display image info: {e}")
    else:
        print("❌ No image selected!")
        return []
    
    print(f"\n🎯 TEST PLAN:")
    print(f"   📝 Total prompts: {len(test_prompts)}")
    print(f"   🤖 Models to test: 2 (Fast + Quality)")
    print(f"   🎬 Total videos: {len(test_prompts) * 2}")
    print(f"   ⏱️  Estimated time: 15-45 minutes")
    print(f"   📁 Storage: gs://{GCS_BUCKET}/veo3_test_results/")
    
    # Run tests for each prompt
    for i, prompt_config in enumerate(test_prompts, 1):
        print(f"\n" + "🔥"*70)
        print(f"🎯 PROMPT {i}/{len(test_prompts)}: {prompt_config['name'].upper()}")
        print(f"📝 {prompt_config['description']}")
        print(f"💭 Prompt text: \"{prompt_config['prompt']}\"")
        print("🔥"*70)
        
        prompt_start_time = time.time()
        
        # Test Fast model first
        print(f"\n🚀 TESTING FAST MODEL (Test {i}A)")
        fast_result = test_model(video_model_fast, prompt_config, f"{i}_fast")
        
        # Brief pause between model tests
        print(f"⏸️  Pausing 3 seconds before Quality model test...")
        time.sleep(3)
        
        # Test Quality model
        print(f"\n🎯 TESTING QUALITY MODEL (Test {i}B)")
        quality_result = test_model(video_model, prompt_config, f"{i}_quality")
        
        # Prompt completion summary
        prompt_end_time = time.time()
        prompt_duration = prompt_end_time - prompt_start_time
        
        print(f"\n📊 PROMPT {i} COMPLETION SUMMARY:")
        print(f"   ⏰ Total time for both models: {prompt_duration:.1f}s ({prompt_duration/60:.1f} minutes)")
        
        if fast_result['success'] and quality_result['success']:
            speed_ratio = quality_result['latency_seconds'] / fast_result['latency_seconds']
            print(f"   🏃 Fast model: {fast_result['latency_seconds']:.1f}s")
            print(f"   🎯 Quality model: {quality_result['latency_seconds']:.1f}s")
            print(f"   📈 Speed difference: {speed_ratio:.1f}x (Quality/Fast ratio)")
        
        print(f"   ✅ Fast model: {'SUCCESS' if fast_result['success'] else 'FAILED'}")
        print(f"   ✅ Quality model: {'SUCCESS' if quality_result['success'] else 'FAILED'}")
        
        # Overall progress
        overall_elapsed = time.time() - overall_start_time
        progress_pct = (i / len(test_prompts)) * 100
        estimated_total = (overall_elapsed / i) * len(test_prompts)
        estimated_remaining = estimated_total - overall_elapsed
        
        print(f"\n🌟 OVERALL PROGRESS:")
        print(f"   📊 Completed: {i}/{len(test_prompts)} prompts ({progress_pct:.1f}%)")
        print(f"   ⏰ Elapsed: {overall_elapsed:.1f}s ({overall_elapsed/60:.1f} minutes)")
        print(f"   ⏱️  Estimated remaining: {estimated_remaining:.1f}s ({estimated_remaining/60:.1f} minutes)")
        print(f"   🎯 Estimated total: {estimated_total:.1f}s ({estimated_total/60:.1f} minutes)")
        
        # Brief pause between prompts (except for the last one)
        if i < len(test_prompts):
            print(f"\n⏸️  Pausing 5 seconds before next prompt...")
            time.sleep(5)
    
    # Final summary
    overall_end_time = time.time()
    total_test_time = overall_end_time - overall_start_time
    
    print(f"\n" + "🎉"*70)
    print(f"🏁 ALL TESTS COMPLETED!")
    print(f"⏰ Total execution time: {total_test_time:.1f}s ({total_test_time/60:.1f} minutes)")
    print(f"🎬 Videos generated: {len([r for r in results if r['success']])}")
    print(f"❌ Failed generations: {len([r for r in results if not r['success']])}")
    print("🎉"*70)
    
    return results

def analyze_results(results):
    """Analyze and display test results"""
    df = pd.DataFrame(results)
    
    print("\n" + "="*70)
    print("📊 VEO 3 PERFORMANCE ANALYSIS REPORT")
    print("="*70)
    print(f"🗂️  Project: {PROJECT_ID}")
    print(f"🪣 GCS Bucket: gs://{GCS_BUCKET}/veo3_test_results/")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary statistics
    fast_results = df[df['model'] == 'Fast']
    quality_results = df[df['model'] == 'Quality']
    
    print("\n📊 LATENCY COMPARISON")
    print("-" * 30)
    print(f"Fast Model Average:    {fast_results['latency_seconds'].mean():.1f}s")
    print(f"Quality Model Average: {quality_results['latency_seconds'].mean():.1f}s")
    
    if len(fast_results) > 0 and len(quality_results) > 0:
        speed_improvement = ((quality_results['latency_seconds'].mean() - fast_results['latency_seconds'].mean()) / quality_results['latency_seconds'].mean() * 100)
        print(f"Speed Improvement:     {speed_improvement:.1f}% faster (Fast vs Quality)")
        
        speedup_factor = quality_results['latency_seconds'].mean() / fast_results['latency_seconds'].mean()
        print(f"Speedup Factor:        {speedup_factor:.1f}x faster")
    
    print(f"\nFast Model Range:      {fast_results['latency_seconds'].min():.1f}s - {fast_results['latency_seconds'].max():.1f}s")
    print(f"Quality Model Range:   {quality_results['latency_seconds'].min():.1f}s - {quality_results['latency_seconds'].max():.1f}s")
    
    # Success rates
    print("\n✅ SUCCESS RATES")
    print("-" * 20)
    print(f"Fast Model:    {fast_results['success'].sum()}/{len(fast_results)} ({fast_results['success'].mean()*100:.1f}%)")
    print(f"Quality Model: {quality_results['success'].sum()}/{len(quality_results)} ({quality_results['success'].mean()*100:.1f}%)")
    
    # GCS storage info
    successful_results = df[df['success'] == True]
    if len(successful_results) > 0:
        print(f"\n🎬 GENERATED VIDEOS")
        print("-" * 20)
        print(f"Total videos created: {len(successful_results)}")
        print(f"Stored in GCS bucket: gs://{GCS_BUCKET}/veo3_test_results/")
        
    # Detailed breakdown by prompt type
    print("\n📋 DETAILED BREAKDOWN BY PROMPT TYPE")
    print("-" * 40)
    
    for prompt_name in df['prompt_name'].unique():
        prompt_data = df[df['prompt_name'] == prompt_name]
        fast_data = prompt_data[prompt_data['model'] == 'Fast']
        quality_data = prompt_data[prompt_data['model'] == 'Quality']
        
        print(f"\n{prompt_name}:")
        if len(fast_data) > 0:
            status = '✅' if fast_data['success'].iloc[0] else '❌'
            print(f"  Fast:    {fast_data['latency_seconds'].iloc[0]:.1f}s - {status}")
            if fast_data['success'].iloc[0] and 'gcs_path' in fast_data.columns:
                gcs_path = fast_data['gcs_path'].iloc[0]
                if gcs_path:
                    print(f"           📁 {gcs_path}")
        
        if len(quality_data) > 0:
            status = '✅' if quality_data['success'].iloc[0] else '❌'
            print(f"  Quality: {quality_data['latency_seconds'].iloc[0]:.1f}s - {status}")
            if quality_data['success'].iloc[0] and 'gcs_path' in quality_data.columns:
                gcs_path = quality_data['gcs_path'].iloc[0]
                if gcs_path:
                    print(f"           📁 {gcs_path}")
        
        if len(fast_data) > 0 and len(quality_data) > 0:
            if fast_data['success'].iloc[0] and quality_data['success'].iloc[0]:
                speedup = quality_data['latency_seconds'].iloc[0] / fast_data['latency_seconds'].iloc[0]
                print(f"  Speedup: {speedup:.1f}x faster (Fast vs Quality)")
    
    # Error analysis
    errors = df[~df['success']]
    if len(errors) > 0:
        print(f"\n❌ ERRORS ENCOUNTERED ({len(errors)} total)")
        print("-" * 25)
        for _, error in errors.iterrows():
            print(f"{error['model']} Model - {error['prompt_name']}: {error['error_message']}")
    
    return df

def save_results(results, filename=None):
    """Save results to JSON file and optionally to GCS"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"veo3_comparison_results_{timestamp}.json"
    
    # Save locally
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Results saved locally to {filename}")
    
    # Try to upload to GCS as well
    try:
        from google.cloud import storage
        
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"veo3_test_results/{filename}")
        
        blob.upload_from_filename(filename)
        print(f"☁️  Results also uploaded to: gs://{GCS_BUCKET}/veo3_test_results/{filename}")
        
    except ImportError:
        print("📝 Install google-cloud-storage to automatically upload results to GCS")
    except Exception as e:
        print(f"⚠️  Could not upload results to GCS: {e}")

def create_summary_report(results):
    """Create a comprehensive summary report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_filename = f"veo3_test_summary_{timestamp}.txt"
    
    with open(summary_filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("VEO 3 IMAGE-TO-VIDEO PERFORMANCE COMPARISON SUMMARY\n")
        f.write("=" * 70 + "\n")
        f.write(f"Project: {PROJECT_ID}\n")
        f.write(f"GCS Bucket: gs://{GCS_BUCKET}/veo3_test_results/\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source Image: {os.path.basename(starting_image) if starting_image else 'N/A'}\n")
        f.write("\n")
        
        # Success summary
        df = pd.DataFrame(results)
        successful_tests = df[df['success'] == True]
        failed_tests = df[df['success'] == False]
        
        f.write(f"RESULTS SUMMARY:\n")
        f.write(f"- Total tests: {len(results)}\n")
        f.write(f"- Successful: {len(successful_tests)}\n")
        f.write(f"- Failed: {len(failed_tests)}\n")
        f.write(f"- Success rate: {len(successful_tests)/len(results)*100:.1f}%\n")
        f.write("\n")
        
        # Model comparison
        fast_results = df[df['model'] == 'Fast']
        quality_results = df[df['model'] == 'Quality']
        
        if len(fast_results) > 0 and len(quality_results) > 0:
            f.write(f"PERFORMANCE COMPARISON:\n")
            f.write(f"- Fast Model Average: {fast_results['latency_seconds'].mean():.1f}s\n")
            f.write(f"- Quality Model Average: {quality_results['latency_seconds'].mean():.1f}s\n")
            speedup = quality_results['latency_seconds'].mean() / fast_results['latency_seconds'].mean()
            f.write(f"- Speedup Factor: {speedup:.1f}x (Fast vs Quality)\n")
            f.write("\n")
        
        # Generated videos
        f.write("GENERATED VIDEOS:\n")
        for _, result in successful_tests.iterrows():
            if 'gcs_path' in result and result['gcs_path']:
                f.write(f"- {result['prompt_name']} ({result['model']}): {result['gcs_path']}\n")
        
        f.write("\n")
        f.write("=" * 70 + "\n")
    
    print(f"📋 Summary report saved as: {summary_filename}")
    return summary_filename

# Main execution
if __name__ == "__main__":
    try:
        # Setup image selection
        if not setup_image_selection():
            print("❌ Setup cancelled. Exiting...")
            exit()
        
        print(f"\n✅ Ready to test with image: {os.path.basename(starting_image)}")
        
        # Run the comparison test
        print("\n🚀 Starting video generation tests...")
        results = run_comparison_test()
        
        if results:
            print("\n📊 Analyzing results...")
            df = analyze_results(results)
            
            print("\n💾 Saving results...")
            save_results(results)
            
            print("\n📋 Creating summary report...")
            summary_file = create_summary_report(results)
            
            print("\n🎉 Test completed successfully!")
            print(f"📈 Generated {len([r for r in results if r['success']])} successful videos")
            print(f"📁 All files stored in: gs://{GCS_BUCKET}/veo3_test_results/")
            print(f"📋 Summary available in: {summary_file}")
            
            # Final instructions
            print("\n💡 NEXT STEPS:")
            print("1. Check the generated video files in your current directory")
            print("2. Review the JSON results file for detailed metrics")
            print("3. Access all videos in your GCS bucket for sharing")
            print(f"4. View summary report: {summary_file}")
            
        else:
            print("❌ No results to analyze. Check for errors above.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        if results:
            print("💾 Saving partial results...")
            save_results(results)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if results:
            print("💾 Saving partial results...")
            save_results(results)