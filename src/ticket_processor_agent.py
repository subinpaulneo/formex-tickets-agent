import json

from src.llm_utils import query_llm, query_local_llm

class TicketProcessorAgent:
    """Agent responsible for extracting structured information and categorizing tickets."""
    def __init__(self, use_local_llm: bool = False):
        self.use_local_llm = use_local_llm
        print(f"TicketProcessorAgent initialized with use_local_llm={use_local_llm}.")

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

        Example JSON Response:
        ```json
        {{
            "category": "Example Category",
            "problem": "Example problem summary.",
            "steps_taken_to_solve": "Example steps taken to solve.",
            "final_solution": "Example final solution."
        }}
        ```

        --- TICKET CONVERSATION ---
        {conversation}
        --- END OF CONVERSATION ---

        JSON Response (ONLY the JSON object, no other text):
        """

        print("[TicketProcessorAgent] Querying LLM for ticket processing...")
        if self.use_local_llm:
            response_raw = query_local_llm(prompt)
            try:
                response = json.loads(response_raw)
            except json.JSONDecodeError:
                print(f"Error: Local LLM did not return valid JSON. Raw response: {response_raw}")
                return None
        else:
            response = query_llm(prompt, json_mode=True)

        if isinstance(response, dict) and "error" in response:
            print(f"Error from LLM in TicketProcessorAgent: {response['error']}")
            return None

        # Directly access keys from the parsed JSON response
        category = response.get("category")
        problem = response.get("problem")
        steps_taken_to_solve = response.get("steps_taken_to_solve")
        final_solution = response.get("final_solution")

        if not all([category, problem, steps_taken_to_solve, final_solution]):
            print(f"Warning: Could not extract all required fields from the LLM response. Raw response: {response}")
            return None

        extracted_data = {
            "category": category,
            "problem": problem,
            "steps_taken_to_solve": steps_taken_to_solve,
            "final_solution": final_solution
        }
        return extracted_data