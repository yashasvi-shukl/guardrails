from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import logging

def load_llamaguard_model(local_path, dtype):
    try:
        logging.info("Loading llamaguard model.")
        model = AutoModelForCausalLM.from_pretrained(local_path, torch_dtype = dtype) #, torch_dtype = dtype, device = device
        return model
    except Exception as e:
        logging.error("Failed to load llamaguard model")

def load_llamaguard_tokenizer(local_path):
    try:
        logging.info("Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path = local_path)
        return tokenizer
    except Exception as e:
        logging.error("Failed to load llamaguard tokenizer.")

