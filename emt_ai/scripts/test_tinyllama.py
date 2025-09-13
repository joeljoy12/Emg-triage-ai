from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

prompt = "You are a triage assistant. Return JSON with triage_level."
ids = tok(prompt, return_tensors="pt")
out = model.generate(**ids, max_new_tokens=50)
print(tok.decode(out[0], skip_special_tokens=True))
