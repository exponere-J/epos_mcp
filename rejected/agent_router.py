import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from anthropic import Anthropic
from openai import OpenAI

# Load API keys
load_dotenv()

class UnifiedAgent:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def _read_identity_kernel(self):
        """Loads the Soul of EPOS from the kernel file."""
        try:
            with open("kernel/EPOS_Identity_Kernel_v2.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "Identity Kernel not found. Defaulting to standard AI mode."

    def _get_system_prompt(self):
        """
        Combines the Technical Specs (Web Speech API) with the Identity Specs (Warrior/Sovereign).
        """
        identity = self._read_identity_kernel()
        
        return f"""
        You are EPOS, an advanced autonomous project orchestrator acting on behalf of Jamie.
        
        --- IDENTITY KERNEL (THE SOUL) ---
        {identity}
        
        --- CRITICAL TECHNICAL INSTRUCTIONS ---
        1. WEB DEV: If building a website, YOU MUST include the 'webkitSpeechRecognition' API for voice features.
        2. ARCHETYPES: Adopt the tone appropriate for the request (Warrior for code/action, Sovereign for strategy, Father/Lover for personal).
        """

    def run(self, user_prompt, model_choice):
        system_instruction = self._get_system_prompt()
        full_prompt = f"{system_instruction}\n\nUSER REQUEST: {user_prompt}"

        try:
            if model_choice == "Gemini 1.5 Pro":
                if not self.gemini_key: return "❌ Error: Missing GEMINI_API_KEY in .env"
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                response = model.generate_content(full_prompt)
                return response.text

            elif model_choice == "Claude 3.5 Sonnet":
                if not self.anthropic_key: return "❌ Error: Missing ANTHROPIC_API_KEY in .env"
                client = Anthropic(api_key=self.anthropic_key)
                message = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": full_prompt}]
                )
                return message.content[0].text

            elif model_choice == "GPT-4o":
                # We keep this here for future Sovereign capability, even if unused today.
                if not self.openai_key: return "⚠️ OpenAI Key not set (Optional)"
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": system_instruction},
                              {"role": "user", "content": user_prompt}]
                )
                return response.choices[0].message.content
            
            else:
                return "⚠️ Error: Select a valid model."
                
        except Exception as e:
            return f"❌ System Error: {str(e)}"

# --- Streamlit Dashboard ---

cat > .env << 'EOF'
GEMINI_API_KEY=AIzaSyDKvK3ixUFVh0v9hLfkfePfSchGUbfE7mU
ANTHROPIC_API_KEY=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
OPENAI_API_KEY=

