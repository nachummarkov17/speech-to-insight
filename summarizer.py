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
                        f"""
You are an advanced AI trained to analyze text and assess threat levels based on intent and language. When provided with a text, perform the following tasks in a structured format:

1. *Title:* Generate a concise, relevant, and engaging title that reflects the core topic or concern in the text.
2. *Summary:* Provide a summary of the text, dynamically adjusting the length based on the content's complexity and importance. Ensure the summary identifies key concerns or risks if applicable.
3. *Length Analysis:* Count and return the number of words in the original text and the generated summary.
4. *Threat Level:* Assign a threat level to the text based on the criteria below:
   - *1 = No threat:* Completely benign, ordinary, or harmless content (e.g., casual conversations or mundane topics).
   - *2 = Low threat:* Slightly concerning, but no clear intent to harm or commit a crime (e.g., vague dissatisfaction or frustration).
   - *3 = Moderate threat:* Potential for risky behavior, minor crime, or veiled intent to cause harm (e.g., indirect threats or preparations without explicit details).
   - *4 = High threat:* Clear planning, intent, or discussion of harmful or illegal activities (e.g., detailed crime planning, direct threats, or dangerous intent).
   - *5 = Critical threat:* Immediate or explicit danger to individuals, groups, or public safety (e.g., active plans to harm someone imminently or evidence of extreme risk).
5. *Keyword Summary:* Extract and list key terms or phrases that indicate potential risks or concerning elements in the text.
*Output Format:*

[{{Generated Title}}]  
[{{Generated Summary}}]  
[Original Length: {{Original Word Count}} words]  
[Summary Length: {{Summary Word Count}} words]  
[Threat Level: {{1-5}}]  
[{{Comma-separated list of key terms and phrases}}]
:\n\n{input_text}"""
                    ],
                }
            ]
        )
        # Send a message to generate the summary
        response = chat_session.send_message("Summarize the text.")
        return response.text.strip()
    except Exception as e:
        return f"An error occurred: {e}"