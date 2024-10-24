# __init__.py file for ai_content_generator module
# __init__.py file for ai_content_generator module

from .content_generator import ContentGenerator
from .document_handler import DocumentHandler
from .file_utils import create_folder_if_not_exists, find_next_version_file_name
from .prompts import lesson_content_prompt_part1, lesson_content_prompt_part2
from .validation import validate_reading_score

def generate_and_save_lesson(api_key, unit_name, chapter_name, lesson_name, essential_question, lesson_vocabulary, lesson_objectives, phenomenon):
    # Initialize ContentGenerator to generate lesson content
    generator = ContentGenerator(api_key)
    
    # Generate complete lesson content using part 1 and part 2 prompts
    lesson_content = generator.generate_complete_lesson(
        unit_name, chapter_name, lesson_name, essential_question, lesson_vocabulary, lesson_objectives, phenomenon
    )

    if lesson_content:
        # Initialize DocumentHandler to create and format the lesson document
        doc_handler = DocumentHandler(unit_name, chapter_name, lesson_name)
        doc_handler.add_metadata()  # Add metadata to the document
        doc_handler.format_content(lesson_content)  # Format the generated content

        # Create folder structure
        base_folder = "AI_generated_content"
        unit_folder = f"unit{unit_name}"
        chapter_folder = f"chapter{chapter_name}"
        lesson_folder = f"lesson{lesson_name}"

        # Ensure folder exists
        create_folder_if_not_exists(base_folder)

        # Create file path with versioning
        file_path = find_next_version_file_name(
            os.path.join(base_folder, unit_folder, chapter_folder, lesson_folder),
            f'U{unit_name}Ch{chapter_name}L{lesson_name}'
        )

        # Save the document
        doc_handler.save_document(file_path)
