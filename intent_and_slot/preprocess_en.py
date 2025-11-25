import re
import torch
from transformers import BertTokenizer
from config import Config


class InputExample:
    def __init__(self, dataset_type, text, labels):
        self.dataset_type = dataset_type
        self.text = text
        self.labels = labels


class InputFeature:
    def __init__(self,
                 input_ids,
                 attention_mask,
                 labels):
        self.input_ids = input_ids
        self.attention_mask = attention_mask
        self.labels = labels


class Processor:
    @classmethod
    def get_examples(cls, path, dataset_type):
        raw_examples = []
        # 读取文件
        with open(path, 'r') as fp:
            data = eval(fp.read())
        for i, d in enumerate(data):
            text = d['text']
            token_label = d['slots']
            raw_examples.append(
                InputExample(
                    dataset_type,
                    text,
                    token_label
                )
            )
        return raw_examples


def convert_example_to_feature(example_index, example, tokenizer, config):
    dataset_type = example.dataset_type
    text = example.text
    token_label = example.labels

    token_label_ids = [0] * len(tokenizer.tokenize(text))

    # 针对slots处理
    for t_label, t_entity in token_label.items():
        # 得到entity起始位置
        re_result = re.finditer(re.escape(t_entity), text)
        for span in re_result:
            entity = span.group()
            start = span.start()
            end = span.end()

            # 分词后的位置
            tokenized_entity = tokenizer.tokenize(entity)
            token_start_index = len(tokenizer.tokenize(text[:start]))
            token_end_index = token_start_index + len(tokenized_entity)

            # 确保索引在有效范围内
            if token_start_index < len(token_label_ids):
                token_label_ids[token_start_index] = config.ner_label2id['B-' + t_label]  # begin
                for i in range(token_start_index + 1, min(token_end_index, len(token_label_ids))):  # inner
                    token_label_ids[i] = config.ner_label2id['I-' + t_label]

    # 长度不够后面要补id 0
    if len(token_label_ids) >= config.max_len - 2:
        token_label_ids = [0] + token_label_ids + [0]
    else:
        token_label_ids = [0] + token_label_ids + [0] + [0] * (config.max_len - len(token_label_ids) - 2)

    inputs = tokenizer.encode_plus(
        text=text,
        max_length=config.max_len,
        padding='max_length',
        truncation='only_first',
        return_attention_mask=True,
    )

    input_ids = torch.tensor(inputs['input_ids'], requires_grad=False)
    attention_mask = torch.tensor(inputs['attention_mask'], requires_grad=False)
    token_label_ids = torch.tensor(token_label_ids, requires_grad=False)

    if example_index < 5:
        print(f'========================== {dataset_type} example-{example_index} ==========================')
        print(f'text:            {text}')
        print(f'input_ids:       {input_ids}')
        print(f'attention_mask:  {attention_mask}')
        print(f'token_label_ids: {token_label_ids}')
        token_label_indices = [i for i in range(len(token_label_ids)) if token_label_ids[i] != 0]
        token_labels = [input_ids[x] for x in token_label_indices]
        print(f'token_labels: {[tokenizer.decode(result) for result in token_labels]}')
        print(' ')

    feature = InputFeature(
        input_ids,
        attention_mask,
        token_label_ids,
    )

    return feature


def get_features(raw_examples, tokenizer, args):
    features = []
    for i, example in enumerate(raw_examples):
        feature = convert_example_to_feature(i, example, tokenizer, args)
        features.append(feature)
    return features


if __name__ == '__main__':
    config = Config()
    raw_examples = Processor.get_examples('./data/validate_process_en.json', 'test')
    tokenizer = BertTokenizer.from_pretrained('./prev_trained_model/bert-base-uncased/')
    features = get_features(raw_examples, tokenizer, config)
    print('This is preprocess.py')
    # config = Config()
    # raw_examples = Processor.get_examples('./data/test_process.json', 'test')
    # tokenizer = BertTokenizer.from_pretrained('./prev_trained_model/bert-base-chinese/')
    # features = get_features(raw_examples, tokenizer, config)
    # print('This is preprocess.py')