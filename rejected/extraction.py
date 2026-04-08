import json
import os
import re

class ShadowCOO:
    def __init__(self):
        self.name = "Shadow COO (Extraction)"
        # In a real scenario, you would initialize your LLM client here
        # self.llm = LLMClient(api_key=os.getenv("OPENAI_KEY"))

    def process_task(self, task):
        """
        Main entry point for the worker.
        """
        task_type = task.get("task_type")
        payload = task.get("payload", {})

        print(f"[{self.name}] Processing Task: {task_type}")

        if task_type == "extract_from_text":
            return self.extract_structured_data(payload.get("text"))
        
        elif task_type == "synthesize_chat_thread":
            return self.operationalize_chat(payload.get("chat_log"))
        
        else:
            return {"error": "Unknown task type"}

    def operationalize_chat(self, chat_log):
        """
        Scans LLM chat threads to produce an Execution Plan.
        """
        print(f"[{self.name}] Synthesizing Chat Thread...")
        
        # 1. PARSE: Separate User vs. AI (Simple Regex for MVP)
        # In production, we'd feed this whole block to an LLM with a prompt.
        # Here we simulate the extraction of key operational artifacts.
        
        lines = chat_log.split('\n')
        action_items = []
        strategic_notes = []
        
        for line in lines:
            # Simple heuristic: Lines starting with "- [ ]" or "TODO" are actions
            if "- [ ]" in line or "TODO:" in line:
                action_items.append(line.replace("- [ ]", "").replace("TODO:", "").strip())
            # Heuristic: Lines with "Strategy:" or "Insight:" are strategic
            elif "Strategy:" in line or "Insight:" in line:
                strategic_notes.append(line.strip())

        # 2. REFINE: Structure the output
        execution_plan = {
            "source_type": "llm_chat_log",
            "synthesis": {
                "summary": "Chat thread analyzed for operational directives.",
                "strategic_intent": strategic_notes,
                "tactical_actions": action_items
            },
            "implementation_plan": [
                {"step": i+1, "action": item, "status": "pending"} 
                for i, item in enumerate(action_items)
            ]
        }
        
        return execution_plan

    def extract_structured_data(self, text):
        # ... existing logic for raw text extraction ...
        return {"extracted": text[:50] + "..."}

# Worker Entry Point
if __name__ == "__main__":
    # Test the new capability immediately
    worker = ShadowCOO()
    
    test_chat = """
    User: We need to launch the gumroad product.
    AI: Okay, here is the plan.
    Strategy: Use the 'Unarming Avatar' approach.
    TODO: Record HeyGen video.
    TODO: Upload via Huntsman.
    """
    
    result = worker.process_task({
        "task_type": "synthesize_chat_thread",
        "payload": {"chat_log": test_chat}
    })
    
    print(json.dumps(result, indent=2))