import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# ==========================================
# Google Colab Fine-Tuning Script
# ==========================================
MODEL_NAME = "NousResearch/Meta-Llama-3-8B"
DATASET_PATH = "agri_dataset.jsonl"
NEW_MODEL = "Llama-3-8B-Agri-Expert"

print("1. Loading dataset...")
dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

print("2. Configuring 4-bit Quantization (QLoRA)...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

print("3. Downloading Llama-3 (This takes a few minutes)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.float16,
)
model.config.use_cache = False
model = prepare_model_for_kbit_training(model)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

print("4. Defining LoRA Adapters...")
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
# TRL 1.x automatically wraps the model, so we no longer call get_peft_model manually!

def format_prompts(batch):
    prompts = []
    for instruction, output in zip(batch['instruction'], batch['output']):
        prompt = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"
        prompts.append(prompt)
    return {"text": prompts}

dataset = dataset.map(format_prompts, batched=True)

from trl import SFTTrainer, SFTConfig

# ... (omitting top imports for brevity, replacing the config block)
training_arguments = SFTConfig(
    output_dir="./results",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    optim="paged_adamw_32bit",
    save_steps=25,
    logging_steps=10,
    learning_rate=2e-4,
    max_steps=100, # Quick training run for 125 examples
    dataset_text_field="text",
)

print("5. Starting SFT Trainer...")
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    processing_class=tokenizer,
    args=training_arguments,
)

trainer.train()

print("6. Saving Fine-Tuned Model...")
trainer.model.save_pretrained(NEW_MODEL)
print(f"✅ Success! Your fine-tuned model weights are saved in the '{NEW_MODEL}' folder.")
