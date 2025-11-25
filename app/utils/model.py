import torch.nn as nn
from transformers import BertModel

class BertForIntentAndSlot(nn.Module):
    def __init__(self, config):
        super(BertForIntentAndSlot, self).__init__()
        self.config = config
        self.bert = BertModel.from_pretrained(config.bert_dir)
        self.bert_config = self.bert.config
        self.sequence_classification = nn.Sequential(
            nn.Dropout(config.hidden_dropout_prob),
            nn.Linear(config.hidden_size, 
                      config.seq_labels_num),
        )
        self.token_classification = nn.Sequential(
            nn.Dropout(config.hidden_dropout_prob),
            nn.Linear(config.hidden_size, 
                      config.token_labels_num),
        )

    def forward(self,
                input_ids,
                attention_mask,
                # token_type_ids,
                ):
        # bert_output = self.bert(input_ids, attention_mask, token_type_ids)
        bert_output = self.bert(input_ids, attention_mask)
        pooler_output = bert_output[1]  # 进一步处理后序列的第一个token（分类token）的最后一层隐藏状态
        token_output = bert_output[0]  # 模型最后一层输出处的隐藏状态序列

        seq_output = self.sequence_classification(pooler_output)
        token_output = self.token_classification(token_output)
        return seq_output, token_output
