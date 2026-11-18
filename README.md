# Course Notes AI Tutor

[![Built with askThili](https://ask.thili.ai/api/v1/public/projects/mh2ufvfn9w/badge.svg)](https://ask.thili.ai/b/mh2ufvfn9w)

This project develops a simple command-line AI tutor that learns from student course notes. By training a GPT model from scratch on educational text, the tutor can complete sentences and provide concise explanations, leveraging contextual relationships to aid revision.

## What you are building

**Goal.** You will build a command-line AI tutor that learns from educational text, capable of completing sentences and offering short explanations to help students revise.

**Done when.** The project is complete when the GPT model is trained on educational text, can generate coherent sentence completions, and offers explanations through a functional command-line interface.

## Milestones

Tick these off as you go, and commit after each one.

- [ ] **1. Prepare a small corpus of educational text data (e.g., sample lecture notes).**  
      Hint: Use text processing to clean and prepare your educational data.
- [ ] **2. Implement the byte-pair tokenizer and generate token embeddings from the corpus.**  
      Hint: Apply the byte-pair encoding technique to create a vocabulary and convert text to numerical tokens.
- [ ] **3. Build the causal self-attention mechanism and assemble the transformer block.**  
      Hint: Implement the self-attention mechanism with a causal mask to ensure future tokens are not seen.
- [ ] **4. Set up the training loop and train the GPT model on the prepared text.**  
      Hint: Set up the optimization loop and loss calculation for training the transformer model.
- [ ] **5. Implement text generation, allowing users to input a prompt and get completions.**  
      Hint: Implement the sampling strategy (e.g., greedy or top-k) to generate new text based on a prompt.
- [ ] **6. Create a simple CLI interface for interacting with the AI tutor.**  
      Hint: Use basic input/output functions to create an interactive command-line experience.

## Run it

You need Python 3.12 and git.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then choose a model; see the comments inside
python -m app.cli hello
pytest
```

Your work goes in `app/core.py` (one stub per milestone) and `tests/test_core.py`. The first tests pass already; they
check the plumbing.

## Settings and secrets

Model settings live in `.env`, which is ignored by git. **Never commit `.env` or paste a key into code.** If a key ever
reaches GitHub, treat it as leaked and make a new one.

## Stretch ideas

- Enhance the CLI to support multi-turn conversations with the AI tutor.
- Allow the user to specify a 'topic' or 'concept' for the tutor to focus its explanations on.
- Implement a feature to save and load different trained model states for various courses.
