import torch
from torch.utils.data import Dataset


class BertDataset(Dataset):
    def __init__(self, features):
        self.features = features

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return {
            'input_ids': self.features[idx].input_ids.long(),
            'attention_mask': self.features[idx].attention_mask.long(),
            'seq_label_ids': self.features[idx].seq_label_ids.long(),
            'token_label_ids': self.features[idx].token_label_ids.long(),
        }

    def get_features(examples, tokenizer, args):
        features = []
        for example in examples:
            encoding = tokenizer(example["text"], padding='max_length', truncation=True, max_length=args.max_seq_length)
            features.append({
                "input_ids": torch.tensor(encoding["input_ids"]),
                "attention_mask": torch.tensor(encoding["attention_mask"]),
                "seq_label_ids": torch.tensor(example["seq_label_ids"]),
                "token_label_ids": torch.tensor(example["token_label_ids"])
            })
        return features
