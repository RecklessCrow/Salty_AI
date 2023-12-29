from torch import onnx, zeros, long
from torch.nn import Module, Embedding, EmbeddingBag, Dropout


class BaseModel(Module):
    def __init__(self, num_tokens, e_dim=1024, e_mode=None, num_classes=2, dropout=0.0):
        super(BaseModel, self).__init__()

        self.e_dim = e_dim
        self.e_mode = e_mode

        if self.e_mode is None:
            self.embedding = Embedding(num_tokens, self.e_dim)
        else:
            self.embedding = EmbeddingBag(num_tokens, self.e_dim, mode=self.e_mode)

        self.dropout = Dropout(dropout)
        self.num_classes = num_classes

    def forward(self, x):
        raise NotImplementedError

    def save_model(self, path):
        # Ensure the model is on the cpu
        self.cpu()

        # Ensure the model is in evaluation mode
        self.eval()

        # Provide an example input tensor (you may need to adjust the shape)
        example_input = zeros((1, 2), dtype=long)

        # Export the model to ONNX format
        onnx.export(
            self,
            example_input,
            path,
            export_params=True,
            do_constant_folding=True,
            input_names=['input'],  # Provide input names for better interpretability
            output_names=['output'],  # Provide output names for better interpretability
            dynamic_axes={  # Dynamic axes so the model can process batches of arbitrary size
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}}
        )
