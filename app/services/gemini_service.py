import google.generativeai as genai
from flask import current_app
import logging
from typing import Dict, List, Optional

class GeminiService:
    """Service class for handling Google Gemini API interactions."""
    
    def __init__(self):
        """Initialize the Gemini service with API configuration."""
        self.model = None
        self._configure_api()
    
    def _configure_api(self):
        """Configure the Gemini API with the provided API key."""
        try:
            api_key = current_app.config.get('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("Google API key not found in configuration")
            
            genai.configure(api_key=api_key)
            # Initialize the model
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("Gemini API configured successfully")
            
        except Exception as e:
            logging.error(f"Failed to configure Gemini API: {str(e)}")
            raise
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict:
        """
        Generate a response using Gemini model.
        
        Args:
            prompt (str): The user's prompt
            context (str, optional): Additional context for the prompt
            
        Returns:
            Dict: Response containing text and metadata
        """
        try:
            if not self.model:
                self._configure_api()
            
            # Construct the full prompt with context if provided
            full_prompt = self._construct_prompt(prompt, context)
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Extract response text and metadata
            result = {
                'text': response.text,
                'prompt_feedback': getattr(response, 'prompt_feedback', None),
                'safety_ratings': getattr(response, 'safety_ratings', [])
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Error generating Gemini response: {str(e)}")
            return {
                'text': "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                'error': str(e)
            }
    
    def generate_rag_response(self, query: str, context_documents: List[str], 
                            conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Generate a response using RAG approach with context documents.
        
        Args:
            query (str): User's query
            context_documents (List[str]): Relevant document chunks
            conversation_history (List[Dict], optional): Previous conversation
            
        Returns:
            Dict: Response with sources and metadata
        """
        try:
            # Construct RAG prompt
            rag_prompt = self._construct_rag_prompt(
                query, context_documents, conversation_history
            )
            
            response = self.model.generate_content(rag_prompt)
            
            return {
                'text': response.text,
                'sources': context_documents,
                'confidence': self._calculate_confidence(response),
                'safety_ratings': getattr(response, 'safety_ratings', [])
            }
            
        except Exception as e:
            logging.error(f"Error generating RAG response: {str(e)}")
            return {
                'text': "I apologize, but I couldn't retrieve the information you requested. Please try rephrasing your question.",
                'error': str(e)
            }
    
    def analyze_application_intent(self, message: str) -> Dict:
        """
        Analyze if the user message indicates intent to apply for university.
        
        Args:
            message (str): User's message
            
        Returns:
            Dict: Analysis result with intent and confidence
        """
        try:
            analysis_prompt = f"""
            Analyze the following message to determine if the user is expressing intent to apply to a university.
            
            Message: "{message}"
            
            Respond with a JSON object containing:
            - "has_application_intent": boolean
            - "confidence": float between 0 and 1
            - "reasoning": string explaining the decision
            
            Only respond with the JSON object, no other text.
            """
            
            response = self.model.generate_content(analysis_prompt)
            
            # Parse the JSON response
            import json
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # Fallback to keyword-based analysis
                return self._keyword_based_intent_analysis(message)
            
        except Exception as e:
            logging.error(f"Error analyzing application intent: {str(e)}")
            return self._keyword_based_intent_analysis(message)
    
    def _construct_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Construct a well-formatted prompt with context."""
        if context:
            return f"""
            Context: {context}
            
            User Question: {prompt}
            
            Please provide a helpful and accurate response based on the context provided.
            """
        return prompt
    
    def _construct_rag_prompt(self, query: str, context_documents: List[str], 
                            conversation_history: Optional[List[Dict]] = None) -> str:
        """Construct a RAG prompt with documents and conversation history."""
        
        system_prompt = """
        You are a helpful university assistant chatbot. Use the provided context documents to answer questions about the university.
        Always be accurate and helpful. If you cannot find the answer in the provided context, say so clearly.
        Maintain a friendly and professional tone.
        """
        
        # Add conversation history if available
        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get('message_type', 'user')
                content = msg.get('content', '')
                history_text += f"{role.capitalize()}: {content}\n"
        
        # Add context documents
        context_text = "\n\nRelevant University Information:\n"
        for i, doc in enumerate(context_documents, 1):
            context_text += f"\n[Document {i}]:\n{doc}\n"
        
        # Construct final prompt
        final_prompt = f"""
        {system_prompt}
        {history_text}
        {context_text}
        
        Current Question: {query}
        
        Response:
        """
        
        return final_prompt
    
    def _calculate_confidence(self, response) -> float:
        """Calculate confidence score for the response."""
        # This is a simple implementation
        # In production, you might want more sophisticated confidence calculation
        try:
            if hasattr(response, 'safety_ratings'):
                # Use safety ratings as a proxy for confidence
                return 0.8  # Default confidence
            return 0.7
        except:
            return 0.5
    
    def _keyword_based_intent_analysis(self, message: str) -> Dict:
        """Fallback keyword-based intent analysis."""
        application_keywords = [
            'apply', 'application', 'enroll', 'enrollment', 'admission', 
            'register', 'registration', 'join', 'enter', 'study at'
        ]
        
        message_lower = message.lower()
        matches = [keyword for keyword in application_keywords if keyword in message_lower]
        
        has_intent = len(matches) > 0
        confidence = min(0.8, len(matches) * 0.3)
        
        return {
            'has_application_intent': has_intent,
            'confidence': confidence,
            'reasoning': f"Keyword-based analysis found: {matches}" if matches else "No application keywords found"
        } 