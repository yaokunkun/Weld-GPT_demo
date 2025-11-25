import torch


class Config:
    train_path = './data/train_process.json'
    validate_path = './data/validate_process.json'
    test_path = './data/test_process.json'

    seq_labels_path = './data/intents_en.txt'
    token_labels_path = './data/slots_en.txt'

    train_path_en = './data/train_process_en.json'
    validate_path_en = './data/validate_process_en.json'
    test_path_en = './data/test_process_en.json'

    seq_labels_path_en = './data/intents_en.txt'
    token_labels_path_en = './data/slots_en.txt'

    bert_dir = './prev_trained_model/bert-base-chinese/'
    bert_dir_en = './prev_trained_model/bert-base-uncased/' # 国际版
    load_dir = './checkpoints/model.pt'
    load_dir_en = './checkpoints/model.pt'
    # save_dir = './checkpoints/'
    save_dir = './checkpoints'
    save_dir_en = './checkpoints_en'

    do_train = True
    do_test = True
    do_predict = True
    continue_train = False

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    # 生成seq_label到id的映射，和id到seq_label的映射
    seq_label2id = {}
    id2seq_label = {}
    with open(seq_labels_path, 'r') as fp:
        seq_labels = fp.read().split('\n')
        for i, label in enumerate(seq_labels):
            seq_label2id[label] = i
            id2seq_label[i] = label

    # 生成token_label到id的映射，和id到token_label的映射
    token_label2id = {}
    id2token_label = {}
    with open(token_labels_path, 'r') as fp:
        token_labels = fp.read().split('\n')
        for i, label in enumerate(token_labels):
            token_label2id[label] = i
            id2token_label[i] = label

    # 生成ner_label到id的映射，和id到ner_label的映射
    label_list = ['O']
    for label in token_labels:
        B_label = 'B-' + label
        I_label = 'I-' + label
        label_list.append(B_label)
        label_list.append(I_label)
    ner_label2id = {}
    id2ner_label = {}
    for i, label in enumerate(label_list):
        ner_label2id[label] = i
        id2ner_label[i] = label

    hidden_size = 768
    seq_labels_num = len(seq_labels)
    token_labels_num = len(label_list)
    max_len = 128
    batchsize = 32
    lr = 2e-5
    epoch = 2
    # epoch = 100
    hidden_dropout_prob = 0.1

if __name__ == '__main__':
    args = Config()
    print('This is config.py')