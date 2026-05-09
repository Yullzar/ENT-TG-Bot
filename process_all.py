"""This script processes the 'prob-ent-questions.json' file to extract all questions and their associated images. It saves the images to a structured directory and creates new JSON files for each subject with references to the saved images."""
import json
import os
import re
import base64

def extract_base64_images(html):
    """Extract all base64 image data from HTML img tags."""
    if not html:
        return []
    
    # Find all img tags
    img_pattern = r'<img[^>]*>'
    img_tags = re.findall(img_pattern, html, re.DOTALL)
    
    base64_list = []
    for img_tag in img_tags:
        # Extract src attribute
        src_match = re.search(r'src="([^"]+)"', img_tag)
        if src_match:
            src = src_match.group(1)
            if src.startswith('data:image/'):
                # Extract base64 data after 'base64,'
                if 'base64,' in src:
                    b64_data = src.split('base64,')[1]
                    # Clean up: remove any whitespace/newlines
                    b64_data = re.sub(r'\s+', '', b64_data)
                    # Fix padding if needed
                    padding = len(b64_data) % 4
                    if padding:
                        b64_data += '=' * (4 - padding)
                    base64_list.append(b64_data)
    
    return base64_list

def save_base64_image(base64_str, filename):
    """Save base64 image to file and return path."""
    try:
        # Decode base64
        image_data = base64.b64decode(base64_str)
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save to file
        with open(filename, 'wb') as f:
            f.write(image_data)
        return filename
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def process_question(question, subject_name, q_id):
    """Process a single question to extract all images."""
    # Process question images
    question_html = question.get('questionHtml', '')
    question_image_srcs = extract_base64_images(question_html)
    question_has_images = len(question_image_srcs) > 0
    
    # Save question images
    question_image_paths = []
    if question_has_images:
        for idx, b64_data in enumerate(question_image_srcs):
            img_path = f"media/{subject_name}/questions/q{q_id}_{idx}.png"
            saved_path = save_base64_image(b64_data, img_path)
            if saved_path:
                question_image_paths.append(saved_path)
    
    # Process answers
    new_answers = []
    for ans in question.get('answers', []):
        ans_text = ans.get('text', '')
        ans_html = ans.get('html', '')
        
        # Extract images from answer HTML
        ans_image_srcs = extract_base64_images(ans_html)
        ans_has_image = len(ans_image_srcs) > 0
        
        # Save answer images
        answer_image_paths = []
        if ans_has_image:
            for idx, b64_data in enumerate(ans_image_srcs):
                img_path = f"media/{subject_name}/answers/q{q_id}_{ans['letter'].replace(')', '')}_{idx}.png"
                saved_path = save_base64_image(b64_data, img_path)
                if saved_path:
                    answer_image_paths.append(saved_path)
        
        new_ans = {
            'index': ans['index'],
            'letter': ans['letter'],
            'text': ans_text,
            'hasImage': ans_has_image,
            'images': answer_image_paths
        }
        new_answers.append(new_ans)
    
    # Create new question object
    new_question = {
        'questionIndex': question['questionIndex'],
        'questionType': question['questionType'],
        'questionText': question['questionText'],
        'questionHasImages': question_has_images,
        'questionImages': question_image_paths,
        'answers': new_answers,
        'correctLetter': question['correctLetter']
    }
    return new_question

def main():
    # Read the main JSON file
    print("Reading prob-ent-questions.json...")
    with open('prob-ent-questions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create output directory
    output_dir = 'questions_json'
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all subjects
    subjects = data['store']['subjects']
    print(f"Found {len(subjects)} subjects")
    
    # Process each subject
    for subject_name, subject_data in subjects.items():
        print(f"\nProcessing {subject_name}...")
        
        # Create a clean filename from subject name
        clean_name = subject_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        clean_name = clean_name.replace(':', '_').replace('?', '_').replace('*', '_')
        clean_name = clean_name.replace('\'', '_').replace('<', '_').replace('>', '_')
        clean_name = clean_name.replace('|', '_')
        
        # Extract all questions from all variants
        all_questions = {}
        question_counter = 1
        total_images = 0
        
        variants = subject_data.get('variants', {})
        for variant_key, variant_data in variants.items():
            questions = variant_data.get('questions', {})
            for q_key, question in questions.items():
                # Process question and extract images
                processed_q = process_question(question, subject_name, question_counter)
                all_questions[str(question_counter)] = processed_q
                
                # Count images
                if processed_q['questionHasImages']:
                    total_images += len(processed_q['questionImages'])
                for ans in processed_q['answers']:
                    if ans['hasImage']:
                        total_images += len(ans['images'])
                
                question_counter += 1
        
        # Create the output structure
        output_data = {
            subject_name: {
                "questions": all_questions
            }
        }
        
        # Write to file
        output_path = os.path.join(output_dir, f'{clean_name}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"Created: {output_path} ({len(all_questions)} questions, {total_images} images)")

if __name__ == '__main__':
    main()
