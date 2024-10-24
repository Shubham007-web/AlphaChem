# content_generator.py file for ai_content_generator module
# content_generator.py file for ai_content_generator module

from ai_content_generator.api_handler import APIHandler
from ai_content_generator.prompts import lesson_content_prompt_part1, lesson_content_prompt_part2

class ContentGenerator:
    def __init__(self, api_key, model_name='chatgpt-4o-latest'):
        """
        Initializes the ContentGenerator with the OpenAI API key and model name.
        """
        self.api = APIHandler(api_key, model_name)

    def generate_lesson_section(self, section_prompt):
        """
        Generates content for a specific section using the OpenAI API.

        Parameters:
        - section_prompt (str): The prompt used to generate the content for a section.

        Returns:
        - str: The generated content for the section.
        - None: If there is an error during content generation.
        """
        messages = [
            {"role": "system", "content": "You are a chemistry textbook writer for 13-14-year-old students."},
            {"role": "user", "content": section_prompt}
        ]
        return self.api.generate_content(messages)

    def generate_complete_lesson(self, unit_name, chapter_name, lesson_name, essential_question, lesson_vocabulary, lesson_objectives, phenomenon):
        """
        Generates the complete lesson content by combining Part 1 and Part 2 of the lesson prompts.

        Parameters:
        - unit_name (str): The name of the unit.
        - chapter_name (str): The name of the chapter.
        - lesson_name (str): The name of the lesson.
        - essential_question (str): The essential question for the lesson.
        - lesson_vocabulary (str): Key vocabulary terms used in the lesson.
        - lesson_objectives (str): The objectives of the lesson.
        - phenomenon (str): The phenomenon for the lesson.

        Returns:
        - str: The complete generated lesson content (Part 1 and Part 2 combined).
        - None: If there is an error during content generation.
        """
        # Generate content for part 1 of the lesson
        part1_prompt = lesson_content_prompt_part1(
            unit_name, chapter_name, lesson_name, essential_question, lesson_vocabulary, lesson_objectives, phenomenon
        )
        part1_content = self.generate_lesson_section(part1_prompt)

        if part1_content is None:
            print("Error: Failed to generate content for Part 1.")
            return None

        # Generate content for part 2 of the lesson
        part2_prompt = lesson_content_prompt_part2(
            unit_name, chapter_name, lesson_name, essential_question, lesson_vocabulary, lesson_objectives, phenomenon
        )
        part2_content = self.generate_lesson_section(part2_prompt)

        if part2_content is None:
            print("Error: Failed to generate content for Part 2.")
            return None

        # Combine part 1 and part 2 content
        complete_lesson_content = f"{part1_content}\n\n{part2_content}"

        return complete_lesson_content
