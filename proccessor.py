"""
Package  
===============

Author: S.

Description:
------------
This script processes a PDF article to extract trading strategy and risk management information. It generates a summary and 
produces QuantConnect Python code for algorithmic trading based on the extracted data. The script utilizes OpenAI's language 
models for summarization and code generation, and presents the results in a graphical user interface (GUI) built with Tkinter.

LLM used : GPT-4o-latest preferred

License:
--------
This project is licensed under the MIT License. You are free to use, modify, and distribute this software. See the LICENSE file 
for more details.
"""

import re
from typing import Dict, List, Optional
import openai
from openai import OpenAI
import logging
import ast
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name

class OpenAIHandler:
    """Handles interactions with the OpenAI API."""

    def __init__(self, model: str = "claude-3-5-sonnet-20240620"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = OpenAI(api_key="sk-drSNKmEZN3b6AqkM5242E20262944c7f9dD8Bd813d1bA90b", base_url="https://api.bianxie.ai/v1")
        self.model = model

    def generate_summary(self, trading_signals,risk_management ) -> Optional[str]:
        """
        Generate a summary of the trading strategy and risk management based on extracted data.
        """
        self.logger.info("Generating summary using OpenAI.")

        prompt = f"""Provide a clear and concise summary of the following trading strategy and its associated risk management rules. Ensure the explanation is understandable to traders familiar with basic trading concepts and is no longer than 300 words.

        ### Trading Strategy Overview:
        - Core Strategy: Describe the primary trading approach, including any specific indicators, time frames (e.g., 5-minute), and entry/exit rules.
        - Stock Selection: Highlight any stock filters (e.g., liquidity, trading volume thresholds, or price conditions) used to choose which stocks to trade.
        - Trade Signals: Explain how the strategy determines whether to go long or short, including any conditions based on candlestick patterns or breakouts.

        {trading_signals}

        ### Risk Management Rules:
        - Stop Loss: Describe how stop-loss levels are set (e.g., 10% ATR) and explain the position-sizing rules (e.g., 1% of capital at risk per trade).
        - Exit Conditions: Clarify how and when positions are closed (e.g., at the end of the trading day or if certain price targets are hit).
        - Additional Constraints: Mention any leverage limits or other risk controls (e.g., maximum leverage of 4x, focusing on Stocks in Play).

        {risk_management}

        Summarize the details in a practical and structured format.
        """

        try:
            response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an algorithmic trading expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.5
        )
            summary = response.choices[0].message.content.strip()
            self.logger.info("Summary generated successfully.")
            return summary
        except openai.OpenAIError as e:
            self.logger.error(f"OpenAI API error during summary generation: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during summary generation: {e}")
        return None

    def generate_qc_code(self, summary: str) -> Optional[str]:
        """
        Generate QuantConnect Python code based on extracted data.
        """
        self.logger.info("Generating QuantConnect code using OpenAI.")
        #trading_signals = '\n'.join(extracted_data.get('trading_signal', []))
        #risk_management = '\n'.join(extracted_data.get('risk_management', []))

        prompt = f"""
        You are a QuantConnect algorithm developer. Convert the following trading strategy descriptions into a complete, error-free QuantConnect Python algorithm.

        ### Trading Strategy Summary:
        {summary}

        ### Requirements:
        1. **Initialize Method**:
            - Set the start and end dates.
            - Set the initial cash.
            - Define the universe selection logic as described in trading strategy summary. 
            - Initialize required indicators as described in summary.
        2. **OnData Method**:
            - Implement buy/sell logic as described in summary. 
            - Ensure indicators are updated correctly.
        3. **Risk Management**:
            - Apply position sizing or stop-loss mechanisms as described in summary. 
        4. **Ensure Compliance**:
            - Use only QuantConnect's supported indicators and methods.
            - The code must be syntactically correct and free of errors.
        ```

        ### Generated Code:
        ```
        # The LLM will generate the code after this line
        ```
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specialized in generating QuantConnect algorithms in Python."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            generated_code = response.choices[0].message.content.strip()
            # Process the generated code as needed
            self.logger.info("QuantConnect code generated successfully.")
            return generated_code
        except openai.OpenAIError as e:
            self.logger.error(f"OpenAI API error during code generation: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during code generation: {e}")
        return None
        
    def refine_code(self, code: str, info: str) -> Optional[str]:
        """
        Ask the LLM to fix syntax errors in the generated code.
        """
        self.logger.info("Refining generated code using OpenAI.")
        prompt = f"""
        The following QuantConnect Python code has the following logical errors: {info}. Please fix them as required and provide the corrected code.

        ```python
        {code}
        ```
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in QuantConnect Python algorithms."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2,
                n=1
            )
            corrected_code = response.choices[0].message.content.strip()
            # Extract code block
            code_match = re.search(r'```python(.*?)```', corrected_code, re.DOTALL | re.IGNORECASE)
            if code_match:
                corrected_code = code_match.group(1).strip()
            self.logger.info("Code refined successfully.")
            return corrected_code
        except openai.error.OpenAIError as e:
            self.logger.error(f"OpenAI API error during code refinement: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during code refinement: {e}")
        return None

class CodeValidator:
    """Validates Python code for syntax correctness."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_code(self, code: str) -> tuple[bool, str]:
        """
        Validate the generated code for syntax errors.
        """
        self.logger.info("Validating generated code for syntax errors.")
        try:
            ast.parse(code)
            self.logger.info("Generated code is syntactically correct.")
            return True, ""
        except SyntaxError as e:
            self.logger.error(f"Syntax error in generated code: {e}")
            return False, f"{e}"
        except Exception as e:
            self.logger.error(f"Unexpected error during code validation: {e}")
            return False, f"{e}"

class CodeRefiner:
    """Refines code by fixing syntax errors using OpenAI."""

    def __init__(self, openai_handler: OpenAIHandler):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.openai_handler = openai_handler

    def refine_code(self, code: str, info: str) -> Optional[str]:
        """
        Refine the code by fixing syntax errors.
        """
        self.logger.info("Refining code using OpenAI.")
        return self.openai_handler.refine_code(code, info)

class GUI:
    """Handles the graphical user interface using Tkinter."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def display_summary_and_code(self, summary: str, code: str):
        """
        Display the summary and the generated code side by side with syntax highlighting.
        """
        self.logger.info("Displaying summary and code in GUI.")
        try:
            # Create the main Tkinter root
            root = tk.Tk()
            root.title("Article Processor")
            root.geometry("1200x800")
            root.configure(bg="#F0F0F0")

            # Configure grid layout
            root.columnconfigure(0, weight=1)
            root.columnconfigure(1, weight=1)
            root.rowconfigure(0, weight=1)

            # Summary Frame
            summary_frame = tk.Frame(root, bg="#FFFFFF", padx=10, pady=10)
            summary_frame.grid(row=0, column=0, sticky='nsew')

            summary_label = tk.Label(
                summary_frame, text="Article Summary", font=("Arial", 16, "bold"), bg="#FFFFFF"
            )
            summary_label.pack(pady=(0, 10))

            summary_text = scrolledtext.ScrolledText(
                summary_frame, wrap=tk.WORD, font=("Arial", 12)
            )
            summary_text.pack(expand=True, fill='both')
            summary_text.insert(tk.END, summary)
            summary_text.configure(state='disabled')  # Make it read-only

            # Add copy button in summary_frame
            copy_summary_btn = tk.Button(
                summary_frame, text="Copy Summary", command=lambda: self.copy_to_clipboard(summary)
            )
            copy_summary_btn.pack(pady=5)

            # Code Frame
            code_frame = tk.Frame(root, bg="#2B2B2B", padx=10, pady=10)
            code_frame.grid(row=0, column=1, sticky='nsew')

            code_label = tk.Label(
                code_frame,
                text="Generated QuantConnect Code",
                font=("Arial", 16, "bold"),
                fg="#FFFFFF",
                bg="#2B2B2B",
            )
            code_label.pack(pady=(0, 10))

            code_text = scrolledtext.ScrolledText(
                code_frame,
                wrap=tk.NONE,
                font=("Consolas", 12),
                bg="#2B2B2B",
                fg="#F8F8F2",
                insertbackground="#FFFFFF",
            )
            code_text.pack(expand=True, fill='both')

            # Apply syntax highlighting
            self.apply_syntax_highlighting(code, code_text)

            code_text.configure(state='disabled')  # Make it read-only

            # Add copy and save buttons in code_frame
            copy_code_btn = tk.Button(
                code_frame, text="Copy Code", command=lambda: self.copy_to_clipboard(code)
            )
            copy_code_btn.pack(pady=5)

            save_code_btn = tk.Button(
                code_frame, text="Save Code", command=lambda: self.save_code(code)
            )
            save_code_btn.pack(pady=5)

            # Start the Tkinter event loop
            root.mainloop()
        except Exception as e:
            self.logger.error(f"Failed to display GUI: {e}")
            messagebox.showerror("GUI Error", f"An error occurred while displaying the GUI: {e}")

    def apply_syntax_highlighting(self, code: str, text_widget: scrolledtext.ScrolledText):
        """
        Apply syntax highlighting to the code using Pygments and insert it into the Text widget.
        """
        self.logger.info("Applying syntax highlighting to code.")
        try:
            lexer = PythonLexer()
            style = get_style_by_name('monokai')  # Choose a Pygments style
            token_colors = {
                'Token.Keyword': '#F92672',
                'Token.Name.Builtin': '#A6E22E',
                'Token.Literal.String': '#E6DB74',
                'Token.Operator': '#F8F8F2',
                'Token.Punctuation': '#F8F8F2',
                'Token.Comment': '#75715E',
                'Token.Name.Function': '#66D9EF',
                'Token.Name.Class': '#A6E22E',
                'Token.Text': '#F8F8F2',  # Default text color
                # Add more mappings as needed
            }

            # Define tags in the Text widget
            for token, color in token_colors.items():
                text_widget.tag_config(token, foreground=color)

            # Tokenize the code using Pygments
            tokens = lex(code, lexer)

            # Enable the widget to insert text
            text_widget.configure(state='normal')
            text_widget.delete(1.0, tk.END)  # Clear existing text

            # Insert tokens with appropriate tags
            for token, content in tokens:
                token_type = str(token)
                tag = token_type if token_type in token_colors else 'Token.Text'
                text_widget.insert(tk.END, content, tag)

            # Re-enable the widget
            text_widget.configure(state='disabled')
        except Exception as e:
            self.logger.error(f"Failed to apply syntax highlighting: {e}")
            text_widget.insert(tk.END, code)  # Fallback: insert without highlighting

    def copy_to_clipboard(self, text: str):
        """
        Copies the given text to the system clipboard.
        """
        self.logger.info("Copying text to clipboard.")
        try:
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()  # Now it stays on the clipboard after the window is closed
            root.destroy()
            messagebox.showinfo("Copied", "Text copied to clipboard.")
        except Exception as e:
            self.logger.error(f"Failed to copy to clipboard: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy text to clipboard: {e}")

    def save_code(self, code: str):
        """
        Saves the generated code to a file selected by the user.
        """
        self.logger.info("Saving code to file.")
        try:
            filetypes = [('Python Files', '*.py'), ('All Files', '*.*')]
            filename = filedialog.asksaveasfilename(
                title="Save Code", defaultextension=".py", filetypes=filetypes
            )
            if filename:
                with open(filename, 'w') as f:
                    f.write(code)
                messagebox.showinfo("Saved", f"Code saved to {filename}.")
        except Exception as e:
            self.logger.error(f"Failed to save code: {e}")
            messagebox.showerror("Save Error", f"Failed to save code: {e}")
