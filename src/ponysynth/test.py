from ponysynth.corpus import *
from ponysynth.models.triphones import dataset, preprocess
import tensorflow as tf
import tensorflow_probability as tfp
import sonnet as snt
import time
# TODO: submit a pull request to deepmind/sonnet for the ConvNDTranspose issue
from ponysynth.conv_transpose import Conv1DTranspose

tfd = tfp.distributions

def timeit(tag, f):
	start = time.time()
	result = f()
	end = time.time()
	print('{}: {}'.format(tag, end - start))
	return result

luna = SpeechCorpus('/home/celestia/data/audio-tar/Luna.tar')
luna.build_phone_index()

raw_data = dataset(luna, size=20)
features = preprocess(**raw_data)
tfds_data = tf.data.Dataset.from_generator(**features)
#tfds_data = tfds_data.shuffle()
tfds_data = tfds_data.prefetch(16)


# create an embedding that captures local information
# classify embeddings as "continuous" or "contains discontinuity"

class SeqEncoder(snt.Module, latent_dims=2):
    def __init__(self):
        snt.Module.__init__(self, None)
        self.latent_dims = latent_dims

        self.prior = tfd.MultivariateNormalDiag(
            loc=tf.zeros([self.latent_dims]),
            scale_diag=1.0)

    @snt.once
    def _initialize(self, inputs):
        self.mean_kernel = snt.Conv1D(
            output_channels=self.latent_dims,
            kernel_shape=3,
            padding='SAME')
        self.stddev_kernel = snt.Conv1D(
            output_channels=self.latent_dims,
            kernel_shape=3,
            padding='SAME')

        

    def __call__(self, inputs):
        self._initialize(inputs)
        means = self.mean_kernel(inputs)
        stddevs = self.stddev_kernel(inputs)

        return tfd.MultivariateNormalDiag(
            loc=means, scale_diag=stddevs**2)


class SeqDecoder(snt.Module):
    def __init__(self):
        snt.Module.__init__(self, None)

    @snt.once
    def _initialize(self, inputs):
        self.mean_kernel = Conv1DTranspose(
            output_channels=1,
            kernel_shape=3,
            padding='SAME')
        self.stddev_kernel = Conv1DTranspose(
            output_channels=1,
            kernel_shape=3,
            padding='SAME')

    def __call__(self, inputs):
        self._initialize(inputs)
        means = self.mean_kernel(inputs)
        stddevs = self.stddev_kernel(inputs)

        return tfd.MultivariateNormalDiag(
            loc=means, scale_diag=stddevs**2)


def estim_spec(features, labels, mode, params, config):
    encoder = SeqEncoder()
    decoder = SeqDecoder()

    latent_prior = encoder.prior
    latent_posterior = encoder(features)
    

class ContinuityClassifier(snt.Module):
    pass


class VolDiscriminator(snt.Module):
    pass


class PitchDiscriminator(snt.Module):
    pass


class PaceDiscriminator(snt.Module):
    pass


def _main():
    encoder = SeqEncoder()
    decoder = SeqDecoder()

    for example in tfds_data.batch(1):
        pitches = example['pitch.mean']
        pitches = tf.reshape(pitches, shape=(*pitches.shape, 1))

        print(pitches.shape)

        # shape: (batchSize, frames, channels)
        enc_samples = encoder(pitches).sample(1)[0]
        dec_samples = decoder(enc_samples).sample(1)[0]

        print(dec_samples.shape)


if __name__ == '__main__':
    timeit('main', _main())
