import tensorflow as tf
import transformers


class SentenceModel(tf.keras.Model):

    def __init__(self, modelBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transformer = transformers.TFAutoModel.from_pretrained(modelBase, from_pt=True)

    @tf.function
    def generateSingleEmbedding(self, input, training=False):
        inds, att = input
        embs = self.transformer({'input_ids': inds, 'attention_mask': att}, training=training)[0]
        outAtt = tf.cast(att, tf.float32)
        sampleLength = tf.reduce_sum(outAtt, axis=-1, keepdims=True)
        maskedEmbs = embs * tf.expand_dims(outAtt, axis=-1)
        return tf.reduce_sum(maskedEmbs, axis=1) / tf.cast(sampleLength, tf.float32)

    @tf.function
    def call(self, inputs, training=False, mask=None):
        return self.generateSingleEmbedding(inputs, training)

    def save_pretrained(self, saveName):
        self.transformer.save_pretrained(saveName)

    def from_pretrained(self, saveName):
        self.transformer = transformers.TFAutoModel.from_pretrained(saveName)


class SentenceModelWithLinearTransformation(SentenceModel):

    def __init__(self, modelBase, embeddingSize=640, *args, **kwargs):
        super().__init__(modelBase, *args, **kwargs)
        self.postTransformation = tf.keras.layers.Dense(embeddingSize, activation='linear')

    @tf.function
    def call(self, inputs, training=False, mask=None):
        return self.postTransformation(self.generateSingleEmbedding(inputs, training))
