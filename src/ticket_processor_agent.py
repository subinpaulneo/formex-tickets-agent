from src.llm_utils import query_llm
import json

class TicketProcessorAgent:
    """Agent responsible for extracting structured information and categorizing tickets."""
    def __init__(self):
        print("TicketProcessorAgent initialized.")

    def process_ticket(self, conversation: str) -> dict:
        """
        Processes a raw ticket conversation to extract structured details and suggest a category.
        Args:
            conversation: The full text of the ticket conversation.
        Returns:
            A dictionary containing extracted details and a suggested category.
        """
        prompt = f"""
        You are an expert customer support analyst. Your task is to read a ticket conversation and extract key information.
        Based on the conversation, you should also suggest a category for the ticket.

        The categories should be concise and general, avoiding overly specific or numerous categories.
        Examples of good categories: "Shipping", "Returns", "Account Issues", "Product Inquiry", "Technical Support", "Billing".
        If a suitable category is not clear, use "General Inquiry".

        Extract the following details:
        - **category**: A suggested category for the ticket (string).
        - **problem**: A concise summary of the customer's core issue (string).
        - **steps_taken_to_solve**: A summary of the actions taken by the support agent or system to resolve the issue (string).
        - **final_solution**: The final resolution or outcome of the ticket (string).

        Respond with ONLY a valid JSON object. The JSON object should have the following keys:
        "category", "problem", "steps_taken_to_solve", "final_solution".

        --- TICKET CONVERSATION ---
        {conversation}
        --- END OF CONVERSATION ---

        JSON Response:"""

        print("[TicketProcessorAgent] Querying LLM for ticket processing...")
        response = query_llm(prompt, json_mode=True)

        if isinstance(response, dict) and "error" in response:
            print(f"Error from LLM in TicketProcessorAgent: {response['error']}")
            return {
                "category": "LLM Error",
                "problem": "Could not extract problem due to LLM error.",
                "steps_taken_to_solve": "N/A",
                "final_solution": "N/A",
                "raw_llm_response": response.get("raw_response", "")
            }
        
        # Ensure all expected keys are present, provide defaults if missing
        extracted_data = {
            "category": response.get("category", "Uncategorized"),
            "problem": response.get("problem", "No problem extracted."),
            "steps_taken_to_solve": response.get("steps_taken_to_solve", "No steps extracted."),
            "final_solution": response.get("final_solution", "No final solution extracted.")
        }
        
        return extracted_data
