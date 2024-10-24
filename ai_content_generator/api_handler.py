# api_handler.py file for ai_content_generator module
import openai

class APIHandler:
    def __init__(self, api_key, model_name='chatgpt-4o-latest'):
        """
        Initializes the APIHandler with the OpenAI API key and the model name to use.
        """
        self.api_key = api_key
        self.model_name = model_name
        openai.api_key = api_key

    def generate_content(self, messages, max_tokens=9000, temperature=0.7):
        """
        Makes a call to the OpenAI API to generate content based on the provided messages.

        Parameters:
        - messages (list): The messages used as input for the OpenAI model.
        - max_tokens (int): Maximum number of tokens to generate in the response.
        - temperature (float): Sampling temperature to control the creativity of the output.

        Returns:
        - str: The generated content from the OpenAI model.
        - None: If there is an error with the API call.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response['choices'][0]['message']['content'].strip()
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error: {e}")
            return None
