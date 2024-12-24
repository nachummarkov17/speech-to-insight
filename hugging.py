import os
import google.generativeai as genai

# Configure the API key (ensure the GEMINI_API_KEY environment variable is set)
genai.configure(api_key="AIzaSyDCPNjtKnxK3L406ijfxkHLV7lncw8rLiY")

# Define the generation configuration
generation_config = {
    "temperature": 0.5,  # Lower temperature for focused, deterministic summaries
    "top_p": 0.9,
    "top_k": 40,
    # "max_output_tokens": 200,  # Limit output tokens for concise summaries
    "response_mime_type": "text/plain",
}

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",  # Use the correct model name for your use case
    generation_config=generation_config,
)


def summarize_text(input_text):
    """Summarize the provided text using Google Gemini AI."""
    try:
        # Start a new chat session with the model (without a system role)
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        f"You are a professional summarizer. Please summarize the following text concisely and accurately:\n\n{input_text}"]
                }
            ]
        )
        # Send a message to generate the summary
        response = chat_session.send_message("Summarize the text.")
        return response.text.strip()
    except Exception as e:
        return f"An error occurred: {e}"


# Example usage
if __name__ == "__main__":
    # Get input text to summarize
    input_text = input("Enter the text to summarize:\n")
    summary = summarize_text(input_text)
    print("\nSummary:\n", summary)
