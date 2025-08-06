from flask import Blueprint, render_template, request, jsonify
from services import AppService

main = Blueprint('main', __name__)

def initialize_routes(app, service):
    @main.route('/')
    def index():
        return render_template('index.html')

    @main.route('/generate-prompt', methods=['POST'])
    def generate_prompt():
        data = request.json
        user_prompt = data.get('user_prompt', '')
        system_instructions = data.get('system_instructions', '')
        image_data = data.get('image_data')
        result = service.generate_prompt(user_prompt, system_instructions, image_data)
        return jsonify(result)

    @main.route('/refine-prompt', methods=['POST'])
    def refine_prompt():
        data = request.json
        current_prompt = data.get('current_prompt', '')
        refine_instruction = data.get('refine_instruction', '')
        result = service.refine_prompt(current_prompt, refine_instruction)
        return jsonify(result)

    @main.route('/generate-videos', methods=['POST'])
    def generate_videos():
        data = request.json
        prompts = data.get('prompts', [])
        model_name = data.get('model', 'veo-3.0-fast-generate-001')
        seed = data.get('seed', 42)
        aspect_ratio = data.get('aspect_ratio', '16:9')
        negative_prompt = data.get('negative_prompt', '')
        result = service.generate_videos(prompts, model_name, seed, aspect_ratio, negative_prompt)
        return jsonify(result)

    @main.route('/generate-image-video', methods=['POST'])
    def generate_image_video():
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided.'}), 400
        file = request.files['image']
        prompt = request.form.get('prompt', '')
        model_name = request.form.get('model', 'veo-3.0-fast-generate-preview')
        seed = int(request.form.get('seed', 42))
        aspect_ratio = request.form.get('aspect_ratio', '16:9')
        negative_prompt = request.form.get('negative_prompt', '')
        result = service.generate_image_video(file, prompt, model_name, seed, aspect_ratio, negative_prompt)
        return jsonify(result)

    @main.route('/video-status/<operation_id>', methods=['GET'])
    def video_status(operation_id):
        result = service.get_video_status(operation_id)
        return jsonify(result)

    @main.route('/get-generation-history', methods=['GET'])
    def get_generation_history():
        result = service.get_generation_history()
        return jsonify(result)

    @main.route('/get-system-instructions', methods=['GET'])
    def get_system_instructions():
        result = service.get_system_instructions()
        return jsonify(result)

    @main.route('/save-system-instruction', methods=['POST'])
    def save_system_instruction():
        data = request.json
        name = data.get('name')
        content = data.get('content')
        result = service.save_system_instruction(name, content)
        return jsonify(result)

    @main.route('/delete-system-instruction/<int:instruction_id>', methods=['DELETE'])
    def delete_system_instruction(instruction_id):
        result = service.delete_system_instruction(instruction_id)
        return jsonify(result)

    @main.route('/generate-editor-image', methods=['POST'])
    def generate_editor_image():
        data = request.json
        prompt = data.get('prompt')
        negative_prompt = data.get('negative_prompt')
        seed = data.get('seed')
        aspect_ratio = data.get('aspect_ratio', '16:9')
        result = service.generate_editor_image(prompt, negative_prompt, seed, aspect_ratio)
        return jsonify(result)

    @main.route('/get-settings', methods=['GET'])
    def get_settings():
        result = service.get_settings()
        return jsonify(result)

    @main.route('/save-settings', methods=['POST'])
    def save_settings():
        data = request.json
        project_id = data.get('project_id')
        gcs_bucket = data.get('gcs_bucket')
        result = service.save_settings(project_id, gcs_bucket)
        return jsonify(result)

    @main.route('/segment-image', methods=['POST'])
    def segment_image_route():
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided.'}), 400
        file = request.files['image']
        mode = request.form.get('mode', 'foreground')
        prompt = request.form.get('prompt', None)
        result = service.segment_image(file, mode, prompt)
        return jsonify(result)

    @main.route('/vto', methods=['POST'])
    def vto_route():
        person_image_file = request.files.get('person_image')
        product_image_file = request.files.get('product_image')
        mask_image_file = request.files.get('mask_image')
        person_image_uri = request.form.get('person_image_uri')
        product_image_uri = request.form.get('product_image_uri')
        prompt = request.form.get('prompt')
        person_description = request.form.get('person_description')
        product_description = request.form.get('product_description')
        model_endpoint_name = request.form.get('model_endpoint_name', 'virtual-try-on-exp-05-31')
        sample_count = request.form.get('sample_count', type=int)
        base_steps = request.form.get('base_steps', type=int)
        seed = request.form.get('seed', type=int)
        result = service.vto(
            person_image_file, product_image_file, mask_image_file,
            person_image_uri, product_image_uri, prompt, person_description,
            product_description, model_endpoint_name, sample_count, base_steps, seed
        )
        return jsonify(result)

    @main.route('/product-recontext', methods=['POST'])
    def product_recontext():
        image_files = request.files.getlist('images')
        image_uris = request.form.getlist('image_uris')
        prompt = request.form.get('prompt')
        product_description = request.form.get('product_description')
        disable_prompt_enhancement = request.form.get('disable_prompt_enhancement', 'false').lower() == 'true'
        sample_count = request.form.get('sample_count', 1, type=int)
        base_steps = request.form.get('base_steps', type=int)
        safety_setting = request.form.get('safety_setting')
        person_generation = request.form.get('person_generation')
        aspect_ratio = request.form.get('aspect_ratio')
        resolution = request.form.get('resolution')
        seed = request.form.get('seed', type=int)
        result = service.product_recontext(
            image_files, image_uris, prompt, product_description,
            disable_prompt_enhancement, sample_count, base_steps, safety_setting,
            person_generation, aspect_ratio, resolution, seed
        )
        return jsonify(result)

    @main.route('/get-usage-report', methods=['GET'])
    def get_usage_report():
        range_param = request.args.get('range', '7d')
        result = service.get_usage_report(range_param)
        return jsonify(result)

    @main.route('/veo-edit', methods=['POST'])
    def veo_edit_route():
        prompt = request.form.get('prompt', '')
        video_gcs = request.form.get('video_gcs')
        mask_gcs = request.form.get('mask_gcs')
        mask_mime_type = request.form.get('mask_mime_type')
        mask_mode = request.form.get('mask_mode')
        aspect_ratio = request.form.get('aspect_ratio', '16:9')
        enhance_prompt = request.form.get('enhance_prompt', 'false').lower() == 'true'
        sample_count = request.form.get('sample_count', 1, type=int)
        duration = request.form.get('duration', 8, type=int)
        video_file = request.files.get('video_file')
        mask_file = request.files.get('mask_file')
        result = service.veo_edit(
            prompt, video_gcs, mask_gcs, mask_mime_type, mask_mode,
            aspect_ratio, enhance_prompt, sample_count, duration, video_file, mask_file
        )
        return jsonify(result)

    @main.route('/veo-advanced-edit', methods=['POST'])
    def veo_advanced_edit_route():
        prompt = request.form.get('prompt', '')
        aspect_ratio = request.form.get('aspect_ratio', '16:9')
        enhance_prompt = request.form.get('enhance_prompt', 'false').lower() == 'true'
        duration = request.form.get('duration', 8, type=int)
        camera_control = request.form.get('camera_control')
        image_gcs = request.form.get('image_gcs')
        video_gcs = request.form.get('video_gcs')
        last_frame_gcs = request.form.get('last_frame_gcs')
        image_file = request.files.get('image_file')
        video_file = request.files.get('video_file')
        last_frame_file = request.files.get('last_frame_file')
        result = service.veo_advanced_edit(
            prompt, aspect_ratio, enhance_prompt, duration, camera_control,
            image_gcs, video_gcs, last_frame_gcs, image_file, video_file, last_frame_file
        )
        return jsonify(result)

    @main.route('/imagen-edit', methods=['POST'])
    def imagen_edit_route():
        edit_prompt = request.form.get('prompt')
        edit_mode = request.form.get('edit_mode')
        mask_mode = request.form.get('mask_mode')
        original_image_file = request.files.get('original_image')
        mask_image_file = request.files.get('mask_image')
        result = service.imagen_edit(
            edit_prompt, edit_mode, mask_mode, original_image_file, mask_image_file
        )
        return jsonify(result)

    app.register_blueprint(main)
