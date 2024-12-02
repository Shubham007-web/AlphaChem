# AlphaChemistry Manuscripts Content Generator

## Overview

This project is a Python-based system designed to generate structured chemistry lesson content for students in grades 9-10 (age 14-15) of US students based on eduactional framework NGSS (Next Generation Science Standards), content outline, variuous eduactional conginiative levels like DOK levels, bloom's taxnomny. The Next Generation Science Standards (NGSS) are based on the **"Framework K–12 Science Education"** that was created by the National Research Council. The system uses OpenAI's GPT models to produce easy-to-read educational content aligned with modern instructional strategies such as SMART objectives and phenomenon-based learning while maintaing readibiity score(Flesch Reading Ease Score) and Flesch-Kincaid Grade Level. The generated content is saved in `.docx` format, following a well-organized folder structure.

## Key Features

- **Two-Part Content Generation**: Divides content creation into two parts:
  - **Part 1**: Focuses on the structure and an extended "Explain" section (up to 3000 words).
  - **Part 2**: Covers the remaining lesson sections (Engage, Evaluate, Elaborate).
- **Chain-of-Thought Prompting**: Ensures detailed, logical explanations that are appropriate for high school students.
- **Automated Document Organization**: Generated lessons are saved with automatic folder structure and version control (`V1`, `V2`, etc.).
- **Flesch Reading Ease Score**: Ensures content has a reading ease score above 90, making it suitable for a target audience of U.S. grade 9 students.

## File and Folder Structure

The system organizes the generated content into a structured folder hierarchy:
AI_generated_content/
└── unitX/
└── chapterY/
└── lessonZ/
└── U{X}Ch{Y}L{Z}.docx

Where `X`, `Y`, and `Z` correspond to unit, chapter, and lesson numbers.

## Requirements

- Python 3.x
- `python-docx` for handling `.docx` files
- OpenAI API for GPT-based content generation
- `os` and `re` for file management

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/ai-lesson-generator.git
    cd ai-lesson-generator
    ```

2. **Install the required Python packages**:
    ```bash
    pip install python-docx openai
    ```

3. **Set up your OpenAI API key**:
    ```python
    import openai
    openai.api_key = 'your-api-key-here'
    ```

## Usage

1. **Generate Lesson Content**:
    Use the `generate_lesson_content()` function to create chemistry lessons by passing relevant parameters such as unit name, chapter name, lesson name, and objectives:
    ```python
    lesson_content = generate_lesson_content(
        unit_name="Unit 2: Atomic Structure and Bonding",
        chapter_name="Chapter 3: Unlocking the Atom",
        lesson_name="Lesson 2: Atomic Number and Mass",
        lesson_objective="""Identify the subatomic particles (protons, neutrons, electrons) and their charges..."""
    )
    ```

2. **Save Generated Content**:
    Once the content is generated, save it to a `.docx` file using:
    ```python
    save_lesson_content_to_docx(unit_name, chapter_name, lesson_name, lesson_content)
    ```

## File Descriptions

- **`generate_lesson_content()`**: Generates the lesson content in two parts.
- **`create_document()`**: Creates a `.docx` file structure for the generated lesson.
- **`save_lesson_content_to_docx()`**: Saves the lesson content into a `.docx` file with proper folder and version management.
- **`extract_number()`**: Extracts numbers from unit, chapter, and lesson names for file and folder naming.
- **`find_next_version_file_name()`**: Implements version control for saved lesson files.

## Customization

You can modify the following features to adapt the content:
- **Lesson Objectives**: Change the objectives and vocabulary to match specific lesson goals.
- **Performance Expectations**: Add or modify to meet curriculum standards (e.g., Common Core, NGSS).

## Future Enhancements

- Integration with additional readability analysis tools.
- Expansion to other subjects and grade levels.
- Dynamic generation of diagrams and visuals to accompany lesson content.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
