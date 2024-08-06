# leverage checkpoints for Bert2Bert model...
# use BERT's cls token as BOS token and sep token as EOS token
import torch
from transformers import BertGenerationEncoder, BertGenerationDecoder, EncoderDecoderModel, BertTokenizer

TOKENIZER_PATH = '/dev_data_2/zkyao/pretrain_model/bert-large-uncased'
MODEL_PATH = '/dev_data_2/zkyao/pretrain_model/bert-large-uncased'

tokenizer = BertTokenizer.from_pretrained(TOKENIZER_PATH)
encoder = BertGenerationEncoder.from_pretrained(MODEL_PATH, bos_token_id=101, eos_token_id=102)
decoder = BertGenerationDecoder.from_pretrained(MODEL_PATH, add_cross_attention=True, is_decoder=True, bos_token_id=101, eos_token_id=102)
bert2bert = EncoderDecoderModel(encoder=encoder, decoder=decoder)
bert2bert.eval()  # Set the model to evaluation mode

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
bert2bert.to(device)

def generation(query: str, max_length=50) -> str:
    input_ids = tokenizer(query, add_special_tokens=True, return_tensors="pt").input_ids.to(device)
    decoder_start_token_id = 101
    # Start with just the [CLS] token for the decoder input
    decoder_input_ids = torch.tensor([[101]], dtype=torch.long).to(device)

    for _ in range(max_length):
        outputs = bert2bert(input_ids=input_ids, decoder_input_ids=decoder_input_ids)
        next_token_logits = outputs.logits[:, -1, :]
        next_token_id = next_token_logits.argmax(1).unsqueeze(1)

        # Stop if [EOS] is generated
        if next_token_id[0][0].item() == 102:  # 102 is [SEP] which you're using as EOS
            break

        decoder_input_ids = torch.cat([decoder_input_ids, next_token_id], dim=-1)

    predicted_text = tokenizer.decode(decoder_input_ids[0], skip_special_tokens=True)
    return predicted_text

