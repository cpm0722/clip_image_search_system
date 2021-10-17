import torch

from src.mclip import load_model

model = load_model('base')
model.eval().cuda()

dummy = '이것은 더미 문장입니다.'
tokenized = model.tokenizer(dummy)
args = [torch.LongTensor(tokenized[k]).unsqueeze(dim=0).cuda() for k in tokenized.keys()]

traced_model = torch.jit.trace(model, args, strict=False)
torch.jit.save(traced_model, 'mCLIP_base.pt')
