# prompts.py file for ai_content_generator module
# Prompt Template For the various sections
def lesson_content_prompt_part1(unit_name, chapter_name, lesson_name, essential_question, lesson_vocabulary, lesson_objectives, phenomenon):
    return f"""
    Generate a detailed and structured lesson plan for "{lesson_name}" in Chapter "{chapter_name}" of Unit "{unit_name}" and please rememeber the target aduince is 13-14 years students, so don't phase "student, student have to...".
    The content should be structured, consistent, and align with the following points:
     - lesson objective: {lesson_objectives}
     - lesson vocabulary: {lesson_vocabulary}
     - Essential Question: {essential_question}

    ## Unit Title
    ## Chapter Title
    # Lesson Title
    ### Essential Questions:
     Write the following Essential Questions (EQs) to ensure they drive curiosity and critical thinking:
    - {essential_question}

    ### 1. Big Idea:
    - One line that addresses the main concept of the lesson.
    - A subordinate of the Chapter's Big Idea that addresses the main concepts in the lesson.

    ### 2. Essential Questions
    - Include the following Essential Question(s) as given:
        - {essential_question}
        - Provide answer of each questions.

    ### 3.1 Phenomenon-Based Learning
    - The lesson should build upon the chapter's storyline and introduce a specific aspect, question, or issue that will be explored through hands-on tasks. Focus on connecting the phenomenon to the lesson's tasks and investigations.
    - Phenomenon: {phenomenon}
   ### 3.2 Lesson Phenomenon
   - create lesson Phenomenon based on given unit and chapter Phenomenon and lesson onjectives.
    ### 4. Vocabulary
    - Define these key terms to support students’ understanding:
        - {lesson_vocabulary}

    ### 5. SMART Objectives
    - Write the lesson objective as given in bullet points:
        - {lesson_objectives}

    ### 6. Engage (Ignite)
    - Start with a phenomenon-related question or task to grab attention and continue on the same storyline.
    - Include one hands-on experiment relevant to the lesson topic, with a step-by-step procedure.
    - Add 2-3 follow-up questions based on the activity.
    - Provide answer of each questions if applicable

    ### 7. Pre-Explore (Direct Instruction)
    - Provide background information linking the phenomenon and key concepts.
    - Use interactive elements (notes, discussions, scaffolded questions) to break up the content.
    - Provide answer of each questions if applicable

    ### 8. Evaluate (Progress Check) - Pre-Explore
    - Frame up to 3 scaffolded questions (DOK 1-3) to connect concepts to the hands-on activity.
    - Provide answer of each questions if applicable

    ### 9. Explain (Lightbulb) 
    - Please generate approximately **5000-6000 words** of content that deeply explains the core and main concept of the lesson based on the storyline/Phenomenon: {phenomenon}.
    - Ensure the explanation follows the unit and chapter storyline and aligns with the lesson objectives : {lesson_objectives}.
    - Break down complex concepts into structured sections or subsections, making them digestible for 14-15-year-olds (around 5-6 pages long).
    - Include prompts to help students make sense of the hands-on activity by themselves, based on their prior knowledge, the evidence they gathered in their inquiry activities, and discussions with classmates.
    - After students make their attempt, provide expansion of the concepts explored in the Explore section to build a tight connection to the lessons’ objectives.
    - For every main concept explained, introduce one solved sample problem where applicable, followed by one question for students to solve as a Progress Check.
    - Provide answer of each questions if applicable
    """

def lesson_content_prompt_part2(unit_name, chapter_name, lesson_name, essential_question, lesson_vocabulary, lesson_objectives, phenomenon):
    return f"""
    ### 10. Evaluate (Progress Check) - Explain
    - Include 3 scaffolded questions (DOK 1-3) to confirm understanding of key concepts covered in the "Explain" section but don't mention  DOK level in the text,
       - Provide answer of each questions based on dok level.

    ### 11. Elaborate (Power Up)
    - Pose mini-tasks or open-ended questions encouraging deeper thinking.
    - Allow space for additional questions to extend understanding,
      - Provide answer of each questions based on dok level.

    ### 12. Final Evaluation
    - Provide 1 debate question, including arguments and points for discussion.
    - Frame 8 assessment questions:
        - 4 multiple-choice questions (with options and correct answers, and its explaination).
        - 4 long-answer questions requiring application of knowledge,
           - Provide answer of each questions.
    - Ensure alignment with the unit learning outcomes.

    ### 13. Extend (Beyond the Lesson)
    - Suggest additional tasks, readings, or challenges related to the lesson.
    - Activities (could include readings) and/or questions that challenge students to think about the application of what they’ve learned to new real-world situations, applications, or problems, enhancing their understanding of the chapter and unit tasks.
    - Provide opportunities for spaced practice, allowing students to revisit and reinforce their understanding over time.
    """