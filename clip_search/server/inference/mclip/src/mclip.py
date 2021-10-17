import os
import pickle

import torch
import transformers


class MultilingualClip(torch.nn.Module):
    def __init__(self, model_name, tokenizer_name, head_name, weights_dir='weights'):
        super().__init__()
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        self.head_path = os.path.join(weights_dir, head_name)

        self.tokenizer = transformers.AutoTokenizer.from_pretrained(tokenizer_name)
        self.transformer = transformers.AutoModel.from_pretrained(model_name)
        self.clip_head = torch.nn.Linear(in_features=768, out_features=640)
        self._load_head()

    def forward(self, input_ids, token_type_ids, attention_mask):
        embs = self.transformer(input_ids=input_ids, token_type_ids=token_type_ids, attention_mask=attention_mask)[0]
        embs = (embs * attention_mask.unsqueeze(2)).sum(dim=1) / attention_mask.sum(dim=1)[:, None]
        return self.clip_head(embs)

    def _load_head(self):
        with open(self.head_path, 'rb') as f:
            lin_weights = pickle.loads(f.read())
        self.clip_head.weight = torch.nn.Parameter(torch.tensor(lin_weights[0]).float().t())
        self.clip_head.bias = torch.nn.Parameter(torch.tensor(lin_weights[1]).float())


AVAILABLE_MODELS = {
    'distil': {
        'model_name': 'M-CLIP/M-BERT-Distil-40',
        'tokenizer_name': 'M-CLIP/M-BERT-Distil-40',
        'head_name': 'distil.pkl'
    },

    'base': {
        'model_name': 'M-CLIP/M-BERT-Base-69',
        'tokenizer_name': 'M-CLIP/M-BERT-Base-69',
        'head_name': 'base.pkl'
    },

    'vit': {
        'model_name': 'M-CLIP/M-BERT-Base-ViT-B',
        'tokenizer_name': 'M-CLIP/M-BERT-Base-ViT-B',
        'head_name': 'vit.pkl'
    },
}


def load_model(name):
    config = AVAILABLE_MODELS[name]
    return MultilingualClip(**config)
