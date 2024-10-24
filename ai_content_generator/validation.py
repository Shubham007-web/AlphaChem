# validation.py file for ai_content_generator module
# validation.py file for ai_content_generator module

from textstat import flesch_reading_ease

def validate_reading_score(content):
    """
    Validates the readability of the content using the Flesch Reading Ease Score.

    Parameters:
    - content (str): The content to be validated.

    Returns:
    - float: The Flesch Reading Ease Score of the content.
    - None: If the content cannot be validated (e.g., empty content).
    """
    if not content:
        print("Warning: Content is empty, cannot validate reading score.")
        return None
    
    # Calculate the Flesch Reading Ease Score
    reading_score = flesch_reading_ease(content)
    
    # Print warnings if the score is below a certain threshold
    if reading_score < 80:
        print(f"Warning: Flesch Reading Ease Score is {reading_score}, which is lower than the desired score for 13-14-year-old students.")
    
    return reading_score
