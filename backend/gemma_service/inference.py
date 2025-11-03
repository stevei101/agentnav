"""
Inference functions for Gemma model
Handles text generation and tokenization
"""

import logging
import torch

logger = logging.getLogger(__name__)


class GemmaInference:
    """Handles inference with Gemma model"""

    def __init__(self, model, tokenizer, device: str):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
    ) -> str:
        """
        Generate text from prompt

        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter

        Returns:
            Generated text
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")

        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,  # Reasonable max input length
            ).to(self.device)

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Decode output (remove input prompt)
            input_length = inputs["input_ids"].shape[1]
            generated_ids = outputs[0][input_length:]
            generated_text = self.tokenizer.decode(
                generated_ids,
                skip_special_tokens=True,
            )

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise

    def generate_embeddings(self, text: str) -> list:
        """
        Generate embeddings for text

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")

        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            ).to(self.device)

            # Get embeddings (use model's embedding layer or last hidden state)
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True)
                # Use last hidden state mean as embedding
                embeddings = outputs.hidden_states[-1].mean(dim=1).squeeze()

            return embeddings.cpu().tolist()

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
