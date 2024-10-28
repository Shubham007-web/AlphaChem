# streamlit_app.py - Streamlit app for lesson generation

import streamlit as st
from ai_content_generator.content_generator import ContentGenerator
from ai_content_generator.document_handler import DocumentHandler
from ai_content_generator.file_utils import create_folder_if_not_exists, find_next_version_file_name

# Set your OpenAI API key here
api_key = "your_openai_api_key"

# Main function for Streamlit app
def main():
    st.title("Alpha Chemistry | Lesson Generator App | DeveSh Kalu")

    # Collecting inputs using Streamlit widgets
    unit_name = st.text_input("Enter the Unit Name")
    chapter_name = st.text_input("Enter the Chapter Name")
    lesson_name = st.text_input("Enter the Lesson Name")
    essential_question = st.text_area("Enter the Essential Question")
    lesson_vocabulary = st.text_area("Enter the Lesson Vocabulary (comma-separated)")
    lesson_objectives = st.text_area("Enter the Lesson Objectives")
    phenomenon = st.text_area("Enter the Phenomenon or Storyline for the Lesson")

    # Button to trigger lesson generation
    if st.button("Generate Lesson Content"):
        if unit_name and chapter_name and lesson_name and essential_question and lesson_vocabulary and lesson_objectives and phenomenon:
            st.info("Generating lesson content... Please wait.")
            
            # Initialize the Content Generator
            generator = ContentGenerator(api_key)
            
            # Generate lesson content
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
                st.success("Lesson content generated successfully!")

                # Display the generated lesson content in the app
                st.text_area("Generated Lesson Content", value=lesson_content, height=300)

                # Option to save the content as a .docx file
                if st.button("Download Lesson as .docx"):
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
                    st.success(f"Lesson content saved at: {file_path}")
                    st.download_button(
                        label="Download .docx",
                        data=open(file_path, "rb").read(),
                        file_name=f"{file_path}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            else:
                st.error("Failed to generate lesson content. Please try again.")
        else:
            st.error("Please fill in all the required fields!")

if __name__ == "__main__":
    main()
