from transformers import AutoTokenizer, BertForSequenceClassification
import torch

MODEL_PATH = "/dev_data_2/zkyao/code/Weld-GPT_demo/models/bert-base-uncased-yelp-polarity"
TOKENIZER_PATH = "/dev_data_2/zkyao/code/Weld-GPT_demo/models/bert-base-uncased-yelp-polarity"

tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=TOKENIZER_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH)



def inference(query: str) -> str:
    inputs = tokenizer(query, return_tensors="pt")

    with torch.no_grad():
        logits = model(**inputs).logits

        predicted_class_id = logits.argmax().item()
        predicted_class_label = model.config.id2label[predicted_class_id]
    return str(predicted_class_label)
