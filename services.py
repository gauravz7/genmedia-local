import base64
import io
import json
import os
import time
import threading
import datetime
from PIL import Image
import requests
from google.cloud import storage
from vertexai.preview.vision_models import ImageGenerationModel
from segmentation import segment_image as segment_image_internal
from vto import call_virtual_try_on, prediction_to_pil_image
from prism import call_product_recontext, prediction_to_pil_image as prism_prediction_to_pil_image
from veo_editing import generate_video as generate_veo_video, upload_to_gcs as upload_veo_to_gcs
import imagenedit
from extensions import db
from models import GenerationHistory, SystemInstruction
from utils import (
    generate_veo_prompt_internal,
    generate_video_internal,
    generate_image_video_internal,
    upload_to_gcs,
    download_from_gcs,
)

class AppService:
    def __init__(self, app):
        self.app = app
        self.client = None
        self.segmentation_model = None
        self.vto_client = None
        self.imagen_client = None

    def init_clients(self, project_id, location):
        try:
            import vertexai
            from google import genai
            from segmentation import initialize_segmentation_model
            from vto import get_vto_client
            import imagenedit

            vertexai.init(project=project_id, location=location)
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.segmentation_model = initialize_segmentation_model()
            if not self.segmentation_model:
                print("Warning: Segmentation model failed to initialize.")
            self.vto_client = get_vto_client()
            self.imagen_client = imagenedit.initialize_imagen_client(project_id, location)
            return True
        except Exception as e:
            print(f"Error during Google GenAI client initialization: {e}")
            self.client = None
            self.segmentation_model = None
            self.vto_client = None
            self.imagen_client = None
            return False

    def generate_prompt(self, user_prompt, system_instructions, image_data):
        if not user_prompt or not system_instructions:
            return {'error': 'User prompt and system instructions are required.'}, 400
        final_prompt = generate_veo_prompt_internal(self.client, user_prompt, system_instructions, image_data)
        return {'final_prompt': final_prompt}

    def refine_prompt(self, current_prompt, refine_instruction):
        if not current_prompt or not refine_instruction:
            return {'error': 'Current prompt and refinement instruction are required.'}, 400
        system_instruction = f"Refine the following video prompt based on the instruction. Output only the new prompt.\n\nInstruction: {refine_instruction}"
        refined_prompt = generate_veo_prompt_internal(self.client, current_prompt, system_instruction)
        return {'refined_prompt': refined_prompt}

    def generate_videos(self, prompts, model_name, seed, aspect_ratio, negative_prompt):
        if not prompts:
            return {'error': 'No prompts provided.'}, 400
        operation_ids = []
        for i, prompt in enumerate(prompts):
            operation_id = f"op_{int(time.time() * 1000)}_{i}"
            new_history = GenerationHistory(operation_id=operation_id, prompt=prompt, status='queued')
            db.session.add(new_history)
            db.session.commit()
            operation_ids.append(operation_id)
            thread = threading.Thread(
                target=generate_video_internal,
                args=(self.app.app_context(), self.client, prompt, operation_id, model_name, seed, aspect_ratio, negative_prompt),
            )
            thread.start()
        return {'operation_ids': operation_ids}

    def generate_image_video(self, file, prompt, model_name, seed, aspect_ratio, negative_prompt):
        if file.filename == '' or not prompt:
            return {'error': 'Image and prompt are required.'}, 400
        
        image_bytes = file.read()
        operation_id = f"img_op_{int(time.time() * 1000)}"
        
        _, f_ext = os.path.splitext(file.filename)
        image_filename = f"{operation_id}{f_ext}"
        image_save_path = os.path.join('static', 'uploads', image_filename)
        with open(image_save_path, 'wb') as f:
            f.write(image_bytes)
        
        relative_image_path = f"/{image_save_path}"

        new_history = GenerationHistory(operation_id=operation_id, prompt=prompt, status='queued', image_path=relative_image_path)
        db.session.add(new_history)
        db.session.commit()
        
        thread = threading.Thread(
            target=generate_image_video_internal,
            args=(self.app.app_context(), prompt, operation_id, image_bytes, model_name, seed, aspect_ratio, negative_prompt),
        )
        thread.start()
        return {'operation_id': operation_id}

    def get_video_status(self, operation_id):
        history_item = GenerationHistory.query.filter_by(operation_id=operation_id).first_or_404()
        return history_item.to_dict()

    def get_generation_history(self):
        history = GenerationHistory.query.order_by(GenerationHistory.timestamp.desc()).all()
        return {'history': [item.to_dict() for item in history]}

    def get_system_instructions(self):
        instructions = SystemInstruction.query.all()
        return {'instructions': [item.to_dict() for item in instructions]}

    def save_system_instruction(self, name, content):
        if not name or not content:
            return {'error': 'Name and content are required.'}, 400
        
        instruction = SystemInstruction.query.filter_by(name=name).first()
        
        if instruction:
            instruction.content = content
        else:
            instruction = SystemInstruction(name=name, content=content)
            db.session.add(instruction)
            
        db.session.commit()
        return {'success': True, 'instruction': instruction.to_dict()}

    def delete_system_instruction(self, instruction_id):
        instruction = SystemInstruction.query.get(instruction_id)
        if instruction:
            db.session.delete(instruction)
            db.session.commit()
            return {'success': True}
        return {'error': 'Instruction not found.'}, 404

    def generate_editor_image(self, prompt, negative_prompt, seed, aspect_ratio):
        operation_id = f"img_op_{int(time.time() * 1000)}"
        new_history = GenerationHistory(operation_id=operation_id, prompt=prompt, status='running')
        db.session.add(new_history)
        db.session.commit()

        try:
            generation_model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-preview-06-06")
            generation_params = {
                "prompt": prompt,
                "number_of_images": 1,
                "aspect_ratio": aspect_ratio,
                "negative_prompt": negative_prompt,
                "person_generation": "allow_all",
                "safety_filter_level": "block_few",
                "add_watermark": False,
                "seed": seed
            }
            images = generation_model.generate_images(**generation_params)
            image_bytes = images[0]._image_bytes
            
            image_filename = f"{operation_id}.png"
            image_save_path = os.path.join('static', 'uploads', image_filename)
            with open(image_save_path, 'wb') as f:
                f.write(image_bytes)
            
            relative_image_path = f"/{image_save_path}"
            
            new_history.status = 'completed'
            new_history.image_path = relative_image_path
            db.session.commit()

            return {'image_data': base64.b64encode(image_bytes).decode('utf-8')}

        except Exception as e:
            new_history.status = 'failed'
            new_history.error_message = str(e)
            db.session.commit()
            return {'error': str(e)}, 500

    def get_settings(self):
        return {'project_id': self.app.config['PROJECT_ID'], 'gcs_bucket': self.app.config['GCS_BUCKET_NAME']}

    def save_settings(self, project_id, gcs_bucket):
        self.app.config['PROJECT_ID'] = project_id
        self.app.config['GCS_BUCKET_NAME'] = gcs_bucket

        if self.init_clients(project_id, self.app.config['LOCATION']):
            try:
                storage.Client(project=project_id).get_bucket(gcs_bucket)
                return {'success': True, 'message': 'Settings saved and validated successfully.'}
            except Exception as e:
                return {'success': False, 'message': f'GCS Bucket validation failed: {e}'}
        else:
            return {'success': False, 'message': 'Vertex AI client initialization failed.'}

    def segment_image(self, file, mode, prompt):
        if not self.segmentation_model:
            return {'error': 'Segmentation model not initialized.'}, 500

        if file.filename == '':
            return {'error': 'No selected file.'}, 400

        temp_path = os.path.join('static', 'uploads', file.filename)
        file.save(temp_path)

        result = segment_image_internal(
            model=self.segmentation_model,
            input_file=temp_path,
            segmentation_mode=mode,
            prompt=prompt
        )

        os.remove(temp_path)

        if 'error' in result:
            return result, 500
        
        mask_urls = []
        for i, mask_data in enumerate(result.get('masks', [])):
            mask_bytes = base64.b64decode(mask_data)
            mask_filename = f"mask_{int(time.time() * 1000)}_{i}.png"
            mask_save_path = os.path.join('static', 'uploads', mask_filename)
            with open(mask_save_path, 'wb') as f:
                f.write(mask_bytes)
            mask_urls.append(f"/{mask_save_path}")

        operation_id = f"seg_op_{int(time.time() * 1000)}"
        input_payload = {'mode': mode, 'prompt': prompt, 'image': file.filename}
        output_payload = {'masks': mask_urls}
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=f"Segmentation: {prompt or mode}",
            status='completed',
            input_payload=json.dumps(input_payload),
            output_payload=json.dumps(output_payload),
            operation_type='segmentation'
        )
        db.session.add(new_history)
        db.session.commit()

        return {'masks': mask_urls}

    def vto(self, person_image_file, product_image_file, mask_image_file, person_image_uri, product_image_uri, prompt, person_description, product_description, model_endpoint_name, sample_count, base_steps, seed):
        operation_id = f"vto_op_{int(time.time() * 1000)}"
        if not (person_image_file or person_image_uri) or not (product_image_file or product_image_uri):
            return {'error': 'Person and product images (either file or URI) are required.'}, 400

        person_image_bytes = person_image_file.read() if person_image_file else None
        product_image_bytes = product_image_file.read() if product_image_file else None
        mask_image_bytes = mask_image_file.read() if mask_image_file else None

        try:
            vto_project_id = "cloud-lvm-training-nonprod"
            response = call_virtual_try_on(
                client=self.vto_client,
                project_id=vto_project_id,
                location=self.app.config['LOCATION'],
                model_endpoint_name=model_endpoint_name,
                person_image_bytes=person_image_bytes,
                product_image_bytes=product_image_bytes,
                mask_image_bytes=mask_image_bytes,
                person_image_uri=person_image_uri,
                product_image_uri=product_image_uri,
                prompt=prompt,
                person_description=person_description,
                product_description=product_description,
                sample_count=sample_count,
                base_steps=base_steps,
                seed=seed,
            )

            generated_image_pil = prediction_to_pil_image(response.predictions[0])
            
            image_filename = f"{operation_id}.png"
            image_save_path = os.path.join('static', 'uploads', image_filename)
            generated_image_pil.save(image_save_path)
            
            relative_image_path = f"/{image_save_path}"

            buf = io.BytesIO()
            generated_image_pil.save(buf, format='PNG')
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')

            input_payload = {
                'prompt': prompt,
                'person_description': person_description,
                'product_description': product_description,
                'model_endpoint_name': model_endpoint_name,
                'sample_count': sample_count,
                'base_steps': base_steps,
                'person_image_uri': person_image_uri,
                'product_image_uri': product_image_uri,
            }
            output_payload = {'generated_image': '...'}
            new_history = GenerationHistory(
                operation_id=operation_id,
                prompt=prompt or "VTO Generation",
                status='completed',
                input_payload=json.dumps(input_payload),
                output_payload=json.dumps(output_payload),
                operation_type='vto',
                image_path=relative_image_path
            )
            db.session.add(new_history)
            db.session.commit()

            return {'generated_image': img_str}

        except Exception as e:
            new_history = GenerationHistory(
                operation_id=operation_id,
                prompt=prompt or "VTO Generation",
                status='failed',
                error_message=str(e),
                operation_type='vto'
            )
            db.session.add(new_history)
            db.session.commit()
            return {'error': str(e)}, 500

    def product_recontext(self, image_files, image_uris, prompt, product_description, disable_prompt_enhancement, sample_count, base_steps, safety_setting, person_generation, aspect_ratio, resolution, seed):
        operation_id = f"recontext_op_{int(time.time() * 1000)}"
        image_bytes_list = [base64.b64encode(file.read()).decode('utf-8') for file in image_files]

        try:
            response = call_product_recontext(
                image_bytes_list=image_bytes_list,
                image_uris_list=image_uris,
                prompt=prompt,
                product_description=product_description,
                disable_prompt_enhancement=disable_prompt_enhancement,
                sample_count=sample_count,
                base_steps=base_steps,
                safety_setting=safety_setting,
                person_generation=person_generation,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                seed=seed,
            )

            predictions = []
            saved_image_path = None
            for i, prediction in enumerate(response.predictions):
                pil_image = prism_prediction_to_pil_image(prediction)
                
                if i == 0:
                    image_filename = f"{operation_id}.png"
                    image_save_path = os.path.join('static', 'uploads', image_filename)
                    pil_image.save(image_save_path)
                    saved_image_path = f"/{image_save_path}"

                buf = io.BytesIO()
                pil_image.save(buf, format='PNG')
                img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
                predictions.append(img_str)

            input_payload = {
                'prompt': prompt,
                'product_description': product_description,
                'disable_prompt_enhancement': disable_prompt_enhancement,
                'sample_count': sample_count,
                'base_steps': base_steps,
                'safety_setting': safety_setting,
                'person_generation': person_generation,
                'aspect_ratio': aspect_ratio,
                'resolution': resolution,
                'image_uris': image_uris,
            }
            output_payload = {'predictions': '...'}
            new_history = GenerationHistory(
                operation_id=operation_id,
                prompt=prompt or "Product Recontext",
                status='completed',
                input_payload=json.dumps(input_payload),
                output_payload=json.dumps(output_payload),
                operation_type='recontext',
                image_path=saved_image_path
            )
            db.session.add(new_history)
            db.session.commit()

            return {'predictions': predictions}

        except Exception as e:
            new_history = GenerationHistory(
                operation_id=operation_id,
                prompt=prompt or "Product Recontext",
                status='failed',
                error_message=str(e),
                operation_type='recontext'
            )
            db.session.add(new_history)
            db.session.commit()
            return {'error': str(e)}, 500

    def get_usage_report(self, range_param):
        try:
            if range_param == '7d':
                seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
                history_items = GenerationHistory.query.filter(
                    GenerationHistory.timestamp >= seven_days_ago
                ).all()
                
                daily_data = {}
                for item in history_items:
                    date_key = item.timestamp.date().isoformat()
                    if date_key not in daily_data:
                        daily_data[date_key] = {'completed': 0, 'failed': 0, 'queued': 0, 'running': 0}
                    daily_data[date_key][item.status] += 1
                
                report_text = "📊 Daily Usage Report (Last 7 days) - Local Database\n\n"
                
                total_requests = len(history_items)
                completed_requests = len([h for h in history_items if h.status == 'completed'])
                failed_requests = len([h for h in history_items if h.status == 'failed'])
                
                report_text += "🔢 Overall Summary:\n"
                report_text += f"  • Total requests: {total_requests:,}\n"
                report_text += f"  • Completed requests: {completed_requests:,}\n"
                report_text += f"  • Failed requests: {failed_requests:,}\n"
                
                if total_requests > 0:
                    success_rate = (completed_requests / total_requests) * 100
                    report_text += f"  • Success rate: {success_rate:.2f}%\n"
                    report_text += f"  • Failure rate: {100 - success_rate:.2f}%\n"
                
                report_text += "\n📅 Daily Breakdown:\n"
                for date, counts in sorted(daily_data.items()):
                    day_total = sum(counts.values())
                    day_success_rate = (counts['completed'] / day_total * 100) if day_total > 0 else 0
                    report_text += f"  • {date}: {day_total} requests ({day_success_rate:.1f}% success)\n"
                    report_text += f"    - Completed: {counts['completed']}, Failed: {counts['failed']}\n"
                
                failed_items = [h for h in history_items if h.status == 'failed' and h.error_message]
                if failed_items:
                    report_text += "\n❌ Common Failure Reasons:\n"
                    error_counts = {}
                    for item in failed_items:
                        error_msg = item.error_message[:50] + "..." if len(item.error_message) > 50 else item.error_message
                        error_counts[error_msg] = error_counts.get(error_msg, 0) + 1
                    
                    for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                        percentage = (count / len(failed_items)) * 100
                        report_text += f"  • {error}: {count} ({percentage:.1f}%)\n"
                
            elif range_param == '4w':
                four_weeks_ago = datetime.datetime.utcnow() - datetime.timedelta(weeks=4)
                history_items = GenerationHistory.query.filter(
                    GenerationHistory.timestamp >= four_weeks_ago
                ).all()
                
                weekly_data = {}
                for item in history_items:
                    week_start = item.timestamp.date() - datetime.timedelta(days=item.timestamp.weekday())
                    week_key = week_start.isoformat()
                    if week_key not in weekly_data:
                        weekly_data[week_key] = {'completed': 0, 'failed': 0, 'queued': 0, 'running': 0}
                    weekly_data[week_key][item.status] += 1
                
                report_text = "📊 Weekly Usage Report (Last 4 weeks) - Local Database\n\n"
                
                total_requests = len(history_items)
                completed_requests = len([h for h in history_items if h.status == 'completed'])
                failed_requests = len([h for h in history_items if h.status == 'failed'])
                
                report_text += "🔢 Overall Summary:\n"
                report_text += f"  • Total requests: {total_requests:,}\n"
                report_text += f"  • Completed requests: {completed_requests:,}\n"
                report_text += f"  • Failed requests: {failed_requests:,}\n"
                
                if total_requests > 0:
                    success_rate = (completed_requests / total_requests) * 100
                    report_text += f"  • Success rate: {success_rate:.2f}%\n"
                
                report_text += "\n📅 Weekly Breakdown:\n"
                for week_start, counts in sorted(weekly_data.items()):
                    week_end = datetime.datetime.fromisoformat(week_start) + datetime.timedelta(days=6)
                    week_total = sum(counts.values())
                    week_success_rate = (counts['completed'] / week_total * 100) if week_total > 0 else 0
                    report_text += f"  • Week {week_start} to {week_end.date()}: {week_total} requests ({week_success_rate:.1f}% success)\n"
            
            else:
                total_items = GenerationHistory.query.count()
                completed_items = GenerationHistory.query.filter_by(status='completed').count()
                failed_items = GenerationHistory.query.filter_by(status='failed').count()
                
                report_text = f"📊 Simple Usage Report:\n\n"
                report_text += f"  • Total requests in database: {total_items}\n"
                report_text += f"  • Completed: {completed_items}\n"
                report_text += f"  • Failed: {failed_items}\n"
                
                if total_items > 0:
                    success_rate = (completed_items / total_items) * 100
                    report_text += f"  • Success rate: {success_rate:.2f}%\n"
            
            report_text += "\n💡 Note:\n"
            report_text += "  • This report is based on local database records\n"
            report_text += "  • For real-time Cloud Monitoring metrics, install: pip install google-cloud-monitoring\n"
            
            return {
                'report': report_text,
                'data': {
                    'source': 'local_database',
                    'total_requests': total_requests if 'total_requests' in locals() else 0,
                    'completed_requests': completed_requests if 'completed_requests' in locals() else 0,
                    'failed_requests': failed_requests if 'failed_requests' in locals() else 0
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to generate usage report: {str(e)}'}

    def veo_edit(self, prompt, video_gcs, mask_gcs, mask_mime_type, mask_mode, aspect_ratio, enhance_prompt, sample_count, duration, video_file, mask_file):
        operation_id = f"veo_edit_op_{int(time.time() * 1000)}"
        
        if not (video_gcs or video_file):
            return {'error': 'Video GCS URI or file is required.'}, 400
        if not (mask_gcs or mask_file):
            return {'error': 'Mask GCS URI or file is required.'}, 400

        try:
            if video_file:
                temp_video_path = os.path.join('static', 'uploads', f"{operation_id}_{video_file.filename}")
                video_file.save(temp_video_path)
                video_gcs = upload_veo_to_gcs(self.app.config['PROJECT_ID'], self.app.config['GCS_BUCKET_NAME'], temp_video_path, f"veo-edit-inputs/{operation_id}_{video_file.filename}")
                os.remove(temp_video_path)
                if not video_gcs:
                    return {'error': 'Failed to upload video to GCS.'}, 500

            if mask_file:
                temp_mask_path = os.path.join('static', 'uploads', f"{operation_id}_{mask_file.filename}")
                mask_file.save(temp_mask_path)
                mask_gcs = upload_veo_to_gcs(self.app.config['PROJECT_ID'], self.app.config['GCS_BUCKET_NAME'], temp_mask_path, f"veo-edit-inputs/{operation_id}_{mask_file.filename}")
                os.remove(temp_mask_path)
                if not mask_gcs:
                    return {'error': 'Failed to upload mask to GCS.'}, 500

            output_gcs_path = f"gs://{self.app.config['GCS_BUCKET_NAME']}/veo-edit-outputs/"
            parameters = {
                "storageUri": output_gcs_path,
                "aspectRatio": aspect_ratio,
                "enhancePrompt": enhance_prompt,
                "sampleCount": sample_count,
                "durationSeconds": duration,
            }

            input_payload = {
                'prompt': prompt, 'video_gcs': video_gcs, 'mask_gcs': mask_gcs,
                'mask_mime_type': mask_mime_type, 'mask_mode': mask_mode, 'parameters': parameters
            }
            new_history = GenerationHistory(
                operation_id=operation_id,
                prompt=prompt or f"VEO Edit: {mask_mode}",
                status='queued',
                input_payload=json.dumps(input_payload),
                operation_type='veo_edit'
            )
            db.session.add(new_history)
            db.session.commit()

            thread = threading.Thread(target=self.veo_edit_internal, args=(
                self.app.app_context(), operation_id, prompt, parameters, mask_gcs, mask_mime_type, mask_mode, video_gcs, None, None, None
            ))
            thread.start()

            return {'operation_id': operation_id}

        except Exception as e:
            return {'error': str(e)}, 500

    def veo_advanced_edit(self, prompt, aspect_ratio, enhance_prompt, duration, camera_control, image_gcs, video_gcs, last_frame_gcs, image_file, video_file, last_frame_file):
        operation_id = f"veo_advanced_op_{int(time.time() * 1000)}"
        
        try:
            if image_file:
                temp_image_path = os.path.join('static', 'uploads', f"{operation_id}_{image_file.filename}")
                image_file.save(temp_image_path)
                image_gcs = upload_veo_to_gcs(self.app.config['PROJECT_ID'], self.app.config['GCS_BUCKET_NAME'], temp_image_path, f"veo-advanced-inputs/{operation_id}_{image_file.filename}")
                os.remove(temp_image_path)
                if not image_gcs:
                    return {'error': 'Failed to upload image to GCS.'}, 500

            if video_file:
                temp_video_path = os.path.join('static', 'uploads', f"{operation_id}_{video_file.filename}")
                video_file.save(temp_video_path)
                video_gcs = upload_veo_to_gcs(self.app.config['PROJECT_ID'], self.app.config['GCS_BUCKET_NAME'], temp_video_path, f"veo-advanced-inputs/{operation_id}_{video_file.filename}")
                os.remove(temp_video_path)
                if not video_gcs:
                    return {'error': 'Failed to upload video to GCS.'}, 500

            if last_frame_file:
                temp_last_frame_path = os.path.join('static', 'uploads', f"{operation_id}_{last_frame_file.filename}")
                last_frame_file.save(temp_last_frame_path)
                last_frame_gcs = upload_veo_to_gcs(self.app.config['PROJECT_ID'], self.app.config['GCS_BUCKET_NAME'], temp_last_frame_path, f"veo-advanced-inputs/{operation_id}_{last_frame_file.filename}")
                os.remove(temp_last_frame_path)
                if not last_frame_gcs:
                    return {'error': 'Failed to upload last frame to GCS.'}, 500

            output_gcs_path = f"gs://{self.app.config['GCS_BUCKET_NAME']}/veo-advanced-outputs/"
            parameters = {
                "storageUri": output_gcs_path,
                "aspectRatio": aspect_ratio,
                "enhancePrompt": enhance_prompt,
                "durationSeconds": duration,
            }

            input_payload = {
                'prompt': prompt, 'video_gcs': video_gcs, 'image_gcs': image_gcs,
                'last_frame_gcs': last_frame_gcs, 'camera_control': camera_control, 'parameters': parameters
            }
            new_history = GenerationHistory(
                operation_id=operation_id,
                prompt=prompt or f"VEO Advanced Edit",
                status='queued',
                input_payload=json.dumps(input_payload),
                operation_type='veo_advanced_edit'
            )
            db.session.add(new_history)
            db.session.commit()

            thread = threading.Thread(target=self.veo_edit_internal, args=(
                self.app.app_context(), operation_id, prompt, parameters, None, None, None, video_gcs, image_gcs, last_frame_gcs, camera_control
            ))
            thread.start()

            return {'operation_id': operation_id}

        except Exception as e:
            return {'error': str(e)}, 500

    def imagen_edit(self, edit_prompt, edit_mode, mask_mode, original_image_file, mask_image_file):
        if not self.imagen_client:
            return {'error': 'Imagen client not initialized.'}, 500

        operation_id = f"imagen_edit_op_{int(time.time() * 1000)}"
        
        if not original_image_file:
            return {'error': 'Original image is required.'}, 400

        original_image_bytes = original_image_file.read()
        mask_image_bytes = mask_image_file.read() if mask_image_file else None

        try:
            if edit_mode == "EDIT_MODE_DEFAULT": # Mask-free
                result = imagenedit.edit_image_mask_free(self.imagen_client, edit_prompt, original_image_bytes)
            else:
                result = imagenedit.edit_image_with_mask(
                    client=self.imagen_client,
                    edit_prompt=edit_prompt,
                    original_image_bytes=original_image_bytes,
                    mask_image_bytes=mask_image_bytes,
                    mask_mode=mask_mode,
                    edit_mode=edit_mode
                )

            edited_image_bytes = imagenedit.get_bytes_from_pil(result.generated_images[0].image._pil_image)
            
            original_image_filename = f"{operation_id}_original.png"
            original_image_save_path = os.path.join('static', 'uploads', original_image_filename)
            with open(original_image_save_path, 'wb') as f:
                f.write(original_image_bytes)
            
            edited_image_filename = f"{operation_id}_edited.png"
            edited_image_save_path = os.path.join('static', 'uploads', edited_image_filename)
            with open(edited_image_save_path, 'wb') as f:
                f.write(edited_image_bytes)

            new_history = GenerationHistory(
                operation_id=operation_id,
                prompt=edit_prompt,
                status='completed',
                image_path=f"/{original_image_save_path}",
                output_payload=json.dumps({'edited_image_path': f"/{edited_image_save_path}"}),
                operation_type='imagen_edit'
            )
            db.session.add(new_history)
            db.session.commit()

            return {
                'original_image_url': f"/{original_image_save_path}",
                'edited_image_url': f"/{edited_image_save_path}"
            }

        except Exception as e:
            print(f"Error during Imagen edit: {e}")
            return {'error': str(e)}, 500

    def veo_edit_internal(self, app_context, operation_id, prompt, parameters, mask_gcs, mask_mime_type, mask_mode, video_gcs, image_uri, last_frame_uri, camera_control):
        with app_context:
            history_item = GenerationHistory.query.filter_by(operation_id=operation_id).first()
            try:
                history_item.status = 'running'
                db.session.commit()

                op = generate_veo_video(
                    project_id=self.app.config['PROJECT_ID'],
                    location=self.app.config['LOCATION'],
                    prompt=prompt,
                    parameters=parameters,
                    mask_gcs=mask_gcs,
                    mask_mime_type=mask_mime_type,
                    mask_mode=mask_mode,
                    video_uri=video_gcs,
                    image_uri=image_uri,
                    last_frame_uri=last_frame_uri,
                    camera_control=camera_control,
                )

                if "error" in op:
                    history_item.status = 'failed'
                    history_item.error_message = op["error"]["message"]
                elif "response" in op and "videos" in op["response"]:
                    video_info = op["response"]["videos"][0]
                    gcs_uri = video_info["gcsUri"]
                    
                    gcs_bucket = gcs_uri.split('/')[2]
                    gcs_blob = '/'.join(gcs_uri.split('/')[3:])
                    local_path = os.path.join(self.app.config['VIDEO_DIR'], f"{operation_id}.mp4")
                    download_from_gcs(gcs_bucket, gcs_blob, local_path)

                    history_item.status = 'completed'
                    history_item.video_path = f"/{local_path}"
                    history_item.output_payload = json.dumps(op['response'])
                else:
                    history_item.status = 'failed'
                    history_item.error_message = "Operation finished with no error but no video was generated."
            except Exception as e:
                history_item.status = 'failed'
                history_item.error_message = str(e)
            db.session.commit()
