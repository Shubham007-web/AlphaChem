# app.py file for lesson generation

from ai_content_generator.content_generator import ContentGenerator
from ai_content_generator.document_handler import DocumentHandler
from ai_content_generator.file_utils import create_folder_if_not_exists, find_next_version_file_name

# Set your OpenAI API key here
api_key = "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"  # Replace with your actual API key

# openai.api_key  = api_key

def main():
    print("Welcome to the Lesson Generator App")

    # Collect input from the user
    unit_name = input("Enter the unit name: ")
    chapter_name = input("Enter the chapter name: ")
    lesson_name = input("Enter the lesson name: ")
    essential_question = input("Enter the essential question: ")
    lesson_vocabulary = input("Enter the lesson vocabulary (comma-separated): ")
    lesson_objectives = input("Enter the lesson objectives: ")
    phenomenon = input("Enter the phenomenon or storyline for the lesson: ")

    # Initialize the Content Generator with the API key
    generator = ContentGenerator(api_key)

    # Generate the lesson content
    print("Generating lesson content...")
    lesson_content = generator.generate_complete_lesson(
        unit_name=unit_name,
        chapter_name=chapter_name,
        lesson_name=lesson_name,
        essential_question=essential_question,
        lesson_vocabulary=lesson_vocabulary,
        lesson_objectives=lesson_objectives,
        phenomenon=phenomenon
    )

    if lesson_content:
        print("Lesson content generated successfully.")
        
        # Create a document for the lesson content
        doc_handler = DocumentHandler(unit_name, chapter_name, lesson_name)
        doc_handler.add_metadata()
        doc_handler.format_content(lesson_content)

        # Save the lesson content to a .docx file
        base_folder = "AI_generated_content"
        create_folder_if_not_exists(base_folder)
        
        # Define file path and manage file versioning
        file_path = find_next_version_file_name(
            base_folder, f"U{unit_name}_Ch{chapter_name}_L{lesson_name}"
        )
        
        doc_handler.save_document(file_path)
        print(f"Lesson content saved at: {file_path}")
    else:
        print("Error: Failed to generate the lesson content.")

if __name__ == "__main__":
    main()
