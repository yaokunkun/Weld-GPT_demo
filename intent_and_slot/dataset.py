from torch.utils.data import DataLoader, Dataset

class BertDataset(Dataset):
    def __init__(self, features):
        self.features = features

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return {
            'input_ids': self.features[idx].input_ids.long(),
            'attention_mask': self.features[idx].attention_mask.long(),
            # 'seq_label_ids': self.features[idx].seq_label_ids.long(),
            'labels': self.features[idx].labels.long(),
        }


if __name__ == '__main__':
    from config import Config
    from preprocess_en import Processor, get_features
    from transformers import BertTokenizer


    config = Config()
    tokenizer = BertTokenizer.from_pretrained('./prev_trained_model/bert-base-uncased/')

    raw_examples = Processor.get_examples('./data/train_process_en.json', 'train')
    train_features = get_features(raw_examples, tokenizer, config)
    train_dataset = BertDataset(train_features)
    train_loader = DataLoader(train_dataset, batch_size=config.batchsize, shuffle=True)

    for step, train_batch in enumerate(train_loader):
        print('================= train batch example =================')
        print(train_batch)
        print(' ')
        break

    raw_examples = Processor.get_examples('./data/test_process_en.json', 'test')
    test_features = get_features(raw_examples, tokenizer, config)
    test_dataset = BertDataset(train_features)
    test_loader = DataLoader(test_dataset, batch_size=config.batchsize, shuffle=True)

    for step, test_batch in enumerate(test_loader):
        print('================= test batch example =================')
        print(test_batch)
        print(' ')
        break
