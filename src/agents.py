from src.db_utils import get_db_collection
from src.llm_utils import query_llm
import re
import json

class TicketAnalysisAgent:
    """Agent responsible for analyzing specific tickets."""
    def __init__(self):
        self.db_collection = get_db_collection()
        print("TicketAnalysisAgent initialized.")

    def summarize_ticket(self, ticket_id: str) -> str:
        """Retrieves a ticket by its ID and uses the LLM to summarize it."""
        print(f"[TicketAnalysisAgent] Received request to summarize ticket: {ticket_id}")
        try:
            results = self.db_collection.get(where={"ticket_id": int(ticket_id)})
            if not results or not results['documents']:
                return f"Error: No data found for ticket ID {ticket_id}."
            full_conversation = "\n---\n".join(results['documents'])
        except Exception as e:
            return f"Error retrieving ticket {ticket_id} from database: {e}"

        prompt = f"""You are a helpful customer support analyst. Based on the following ticket conversation, please provide a concise summary that includes these three sections:
1. **Customer Query**: What was the customer's initial issue?
2. **Agent's Actions**: What were the key steps the support agent took?
3. **Final Resolution**: What was the final outcome?

--- TICKET CONVERSATION ---
{full_conversation}
--- END OF CONVERSATION ---

SUMMARY:"""
        print(f"[TicketAnalysisAgent] Querying LLM for summary of ticket {ticket_id}...")
        return query_llm(prompt)

class KnowledgeWriterAgent:
    """Agent responsible for creating structured knowledge documents."""
    def __init__(self):
        self.db_collection = get_db_collection()
        print("KnowledgeWriterAgent initialized.")

    def generate_manual(self, topic: str, category_filter: str = None) -> str:
        """Generates a section of the instruction manual on a given topic using RAG, optionally filtering by category."""
        print(f"[KnowledgeWriterAgent] Received request to generate manual for: {topic}")
        try:
            print(f"[KnowledgeWriterAgent] Searching for context on '{topic}'...")
            where_clause = {}
            if category_filter:
                where_clause["category"] = category_filter
                print(f"[KnowledgeWriterAgent] Filtering by category: {category_filter}")

            results = self.db_collection.query(
                query_texts=[topic],
                n_results=20,
                where=where_clause if where_clause else None
            )
            if not results or not results['documents']:
                return f"No relevant context found for topic '{topic}' and category '{category_filter or 'any'}'."

            context = "\n\n---\n\n".join(results['documents'][0])
        except Exception as e:
            return f"Error querying database for topic '{topic}' and category '{category_filter or 'any'}': {e}"

        prompt = f"""You are an expert technical writer creating a manual for customer support agents. Based on the following context, which includes resolved tickets and official policies, write a clear, step-by-step guide for the topic: '{topic}'.

The guide should include:
1. A summary of common customer questions.
2. A step-by-step process for the agent to follow.
3. Examples of good phrasing to use with customers.
4. The general tone to adopt for this type of issue.

--- CONTEXT ---
{context}
--- END OF CONTEXT ---

MANUAL SECTION FOR '{topic}':"""
        print(f"[KnowledgeWriterAgent] Querying LLM to write manual for '{topic}'...")
        return query_llm(prompt)

    def generate_customer_response(self, customer_query: str) -> str:
        """Generates a customer-facing response template based on a customer query using RAG."""
        print(f"[KnowledgeWriterAgent] Received request to generate customer response for: {customer_query}")
        try:
            print(f"[KnowledgeWriterAgent] Searching for context related to customer query: '{customer_query}'...")
            results = self.db_collection.query(query_texts=[customer_query], n_results=20)
            if not results or not results['documents']:
                return f"No relevant context found for customer query '{customer_query}'."

            context = "\n\n---\n\n".join(results['documents'][0])
        except Exception as e:
            return f"Error querying database for customer query '{customer_query}': {e}"

        prompt = f"""You are a helpful and empathetic customer support agent. Based on the following context, which includes resolved tickets and official policies, draft a polite and clear response template for a customer who is asking: '{customer_query}'.

The response template should:
1. Acknowledge the customer's query.
2. Provide a clear and concise answer or solution.
3. Maintain a helpful and friendly tone.
4. Include any necessary steps or links (if applicable, assume placeholders for links).
5. End with a polite closing.

--- CONTEXT ---
{context}
--- END OF CONTEXT ---

CUSTOMER RESPONSE TEMPLATE FOR '{customer_query}':"""
        print(f"[KnowledgeWriterAgent] Querying LLM to generate customer response for '{customer_query}'...")
        return query_llm(prompt)

class OrchestratorAgent:
    """Main agent that delegates tasks to specialist agents using LLM-based routing."""
    def __init__(self):
        self.analysis_agent = TicketAnalysisAgent()
        self.writer_agent = KnowledgeWriterAgent()
        self.db_collection = get_db_collection() # Initialize db_collection here
        print("OrchestratorAgent initialized.")

    def get_ticket_count(self) -> str:
        """Returns the total number of tickets in the database."""
        try:
            count = self.db_collection.count()
            return f"There are {count} tickets in the database."
        except Exception as e:
            return f"Error retrieving ticket count: {e}"

    def _get_intent(self, user_prompt: str) -> dict:
        """Uses the LLM to classify intent and extract details from the user prompt."""
        # Sanitize the user prompt to avoid breaking the JSON structure
        # Escape double quotes and newlines to ensure valid JSON
        sanitized_prompt = user_prompt.replace("\"", "\\\"").replace("\n", "\\n")

        classifier_prompt = f"""
        You are a routing agent. Your job is to classify the user's request into one of the following categories and extract the necessary information.
        The categories are: ["ticket_summary", "manual_generation", "generate_all_manuals", "ticket_count", "customer_response_template", "unknown"].

        Respond with ONLY a valid JSON object containing two keys: "intent" and "details".

        - For "ticket_summary", the "details" should be the ticket number as a string.
        - For "manual_generation", the "details" should be the topic for the manual.
        - For "generate_all_manuals", the "details" should be null (as it applies to all categories).
        - For "ticket_count", the "details" should be null.
        - For "customer_response_template", the "details" should be the customer's query for which a response template is needed.
        - For "unknown", the "details" should be null.

        EXAMPLES:
        User Request: "can you summarize ticket 12345 for me"
        {{"intent": "ticket_summary", "details": "12345"}}

        User Request: "write the manual for warranty claims"
        {{"intent": "manual_generation", "details": "warranty claims"}}

        User Request: "what is the weather today"
        {{"intent": "unknown", "details": null}}
        ---
        CLASSIFY THE FOLLOWING REQUEST:
        User Request: "{sanitized_prompt}"
        """
        
        intent_json_str = query_llm(classifier_prompt)
        try:
            # The LLM sometimes adds markdown backticks, remove them.
            if intent_json_str.startswith('```json'):
                intent_json_str = intent_json_str[7:-3].strip()
            return json.loads(intent_json_str)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error decoding intent JSON: {e}")
            print(f"Received string: {intent_json_str}")
            return {"intent": "unknown", "details": "Could not understand the request."}

    def handle_request(self, user_prompt: str) -> str:
        """Handles a user's request by routing it to the correct agent via LLM classification."""
        print(f"[OrchestratorAgent] Received prompt: {user_prompt}")
        intent_data = self._get_intent(user_prompt)
        intent = intent_data.get('intent')
        details = intent_data.get('details')

        if intent == 'ticket_summary':
            if not details:
                return "Please specify a ticket ID for the summary."
            return self.analysis_agent.summarize_ticket(ticket_id=details)
        elif intent == 'manual_generation':
            if not details:
                return "Please specify a topic for the manual."
            return self.writer_agent.generate_manual(topic=details)
        elif intent == 'ticket_count':
            return self.get_ticket_count()
        elif intent == 'generate_all_manuals':
            # Get unique categories from ChromaDB
            db_collection = get_db_collection()
            # ChromaDB does not have a direct way to get unique metadata values
            # We will query all documents and extract unique categories
            all_documents = db_collection.get(
                include=['metadatas']
            )
            categories = set()
            if all_documents and all_documents['metadatas']:
                for metadata in all_documents['metadatas']:
                    if 'category' in metadata:
                        categories.add(metadata['category'])
            
            if not categories:
                return "No categories found in the database to generate manuals for."

            manuals_output = []
            for category in sorted(list(categories)):
                print(f"[OrchestratorAgent] Generating manual for category: {category}")
                manual_section = self.writer_agent.generate_manual(topic=category, category_filter=category)
                manuals_output.append(f"--- Manual for Category: {category} ---\n{manual_section}\n")
            
            return "\n\n".join(manuals_output)
        elif intent == 'customer_response_template':
            if not details:
                return "Please provide a customer query to generate a response template."
            return self.writer_agent.generate_customer_response(customer_query=details)
        else: # unknown intent
            return "I'm sorry, I don't have a tool to handle that request. Please ask me to summarize a ticket, generate a manual on a topic, generate all manuals, or ask for the ticket count."

if __name__ == '__main__':
    print("\n--- Testing Agent Architecture ---")
    orchestrator = OrchestratorAgent()
    
    # Note: These tests will only work if you have ingested data first and set your API key.
    prompt1 = "Can you summarize ticket 12345 for me?"
    summary = orchestrator.handle_request(prompt1)
    print("\n--- Test Result for Prompt 1 ---")
    print(summary)

    prompt2 = "Write a manual section for warranty claims."
    manual = orchestrator.handle_request(prompt2)
    print("\n--- Test Result for Prompt 2 ---")
    print(manual)