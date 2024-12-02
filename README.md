# AlphaChemistry Manuscripts Content Generator

## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [File and Folder Structure](#file-and-folder-structure)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Usage](#usage)
7. [File Descriptions](#file-descriptions)
8. [Customization](#customization)
9. [Future Enhancements](#future-enhancements)
10. [License](#license)

---

## Overview

**AlphaChemistry Manuscripts Content Generator** is an AI-powered system designed to create structured chemistry lesson content for students in grades 9–10 (ages 14–15) in the United States. This system aligns with the **Next Generation Science Standards (NGSS)**, which are based on the **"Framework for K–12 Science Education"** by the National Research Council. The content generation leverages OpenAI's GPT models and incorporates educational strategies such as **SMART objectives**, **DOK Levels**, **Bloom's Taxonomy**, and **phenomenon-based learning**.

The generated content ensures a high **Flesch Reading Ease Score** (above 70), chosen to maintain a balance between accessibility and technical accuracy for high school students. Outputs are saved in `.docx` format with an automated folder structure, ensuring consistency and version control.

---

## Key Features

### Lesson Structure:
1. **Lesson**
2. **Chapter** (Opener & Closer)
3. **Unit** (Opener & Closer)

### **Structured Content Generation Parts (Prompts):**
- **Part 1**: Engages students with sections like Engage, Evaluate, and Elaborate.
- **Part 2**: Detailed explanations, including the "Explain" section (up to 3000 words).
- **Part 3**: Engages students with sections like Elaborate (Power Up), Progress Check (Final Evaluation), and Extend (Beyond the Lesson).

### **Instructional Framework Alignment:**
- Content adheres to NGSS and modern instructional frameworks.
- Incorporates educational strategies such as **SMART objectives**, **DOK Levels**, **Bloom's Taxonomy**, and **phenomenon-based learning**.

### **Chain-of-Thought Prompting:**
- Ensures logical, step-by-step reasoning to create high-quality educational materials.

### **Retrieval-Augmented Generation (RAG):**
- Implements a RAG pipeline to enhance content accuracy by incorporating external knowledge.
- Uses a vector database like **FAISS** to store and retrieve embeddings.
- Dynamically enriches lesson content by integrating relevant information retrieved from external sources.

### **Automated File Management:**
- Organizes lessons into folders with automatic versioning (`V1`, `V2`, etc.).

### **Readability Guarantee:**
- Ensures lessons are accessible to the target grade level with a Flesch Reading Ease Score of 70+, balancing technical detail and student comprehension.

---

## File and Folder Structure

The system organizes generated content into a structured hierarchy:

```plaintext
AI_generated_content/
├── UnitX/
│   ├── ChapterY/
│   │   ├── LessonZ/
│   │   │   └── U{X}Ch{Y}L{Z}.docx

```

## Requirements

- Python 3.x
- `python-docx` for handling `.docx` files
- OpenAI API for GPT-based content generation
- `os` and `re` for file management
- A vector database (fiass)
- Embedding
- OpenAI models (chatgpt-4o-latest, gpt-4o)
- Langchain, Langchain_community
- 

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
