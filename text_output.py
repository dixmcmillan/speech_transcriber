from pynput.keyboard import Controller
import re
import time
from typing import Optional

class TextOutput:
    """Handles keyboard output to the active text field."""
    
    def __init__(self):
        self.keyboard = Controller()
        self.last_text = ""
        
    def type_text(self, text: str, smart_spacing: bool = True):
        """
        Type text at the current cursor position.
        
        Args:
            text: The text to type
            smart_spacing: Whether to add spaces intelligently
        """
        if not text or text.isspace():
            return
            
        # Clean up text
        clean_text = text.strip()
        
        # Add appropriate spacing if enabled
        if smart_spacing and self.last_text:
            # Check if we need to add space or if we have end of sentence punctuation
            last_char = self.last_text[-1] if self.last_text else ""
            if not (last_char.isspace() or last_char in ".!?"):
                if not (clean_text[0] in ".,;:!?"):
                    clean_text = " " + clean_text
                    
        # Keep track of last text we typed
        self.last_text = clean_text
        
        # Type the text
        self.keyboard.type(clean_text)
        
    def type_text_with_format(self, text: str, capitalize_sentences: bool = True):
        """
        Type text with auto-formatting.
        
        Args:
            text: The text to type
            capitalize_sentences: Whether to auto-capitalize sentences
        """
        if not text or text.isspace():
            return
            
        # Clean up text
        clean_text = text.strip()
        
        # Capitalize sentences if enabled
        if capitalize_sentences:
            # Split into sentences and capitalize each one
            sentences = re.split(r'([.!?]\s+)', clean_text)
            for i in range(0, len(sentences), 2):
                if i < len(sentences):
                    sentences[i] = sentences[i].capitalize()
            clean_text = ''.join(sentences)
            
        self.type_text(clean_text)
        
    def type_correction(self, old_text: str, new_text: str):
        """
        Type a correction by simulating backspace and new text.
        Use with caution as this can be unreliable across applications.
        
        Args:
            old_text: Text to be replaced (will simulate backspaces)
            new_text: New text to type
        """
        if not old_text:
            self.type_text(new_text)
            return
            
        # Calculate how many characters to delete
        backspaces = len(old_text)
        
        # Delete old text
        for _ in range(backspaces):
            self.keyboard.press(pynput.keyboard.Key.backspace)
            self.keyboard.release(pynput.keyboard.Key.backspace)
            time.sleep(0.01)  # Small delay to avoid race conditions
            
        # Type new text
        self.type_text(new_text)
        
    def clear(self):
        """Reset the last text tracking."""
        self.last_text = ""