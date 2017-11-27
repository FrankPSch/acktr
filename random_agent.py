import tensorflow as tf
import constants as c
from random import randint

# noinspection PyAttributeOutsideInit
class RandomAgent(object):
    def __init__(self, sess, args, n_actions):
        self.sess = sess
        self.args = args
        self.n_actions = n_actions

        self.define_graph()

    def define_graph(self):
        self.input = tf.placeholder(tf.float32, (None, c.IN_HEIGHT, c.IN_WIDTH, c.IN_CHANNELS))
        self.w = tf.Variable(tf.truncated_normal(
            (c.IN_HEIGHT * c.IN_WIDTH * c.IN_CHANNELS, self.n_actions), stddev=0.01))
        self.b = tf.Variable(tf.constant(0.1), (self.n_actions,))
        self.preds = self.get_preds(self.input)

        # Ignore this. Doesn't really mean anything:
        self.global_step = tf.Variable(0, trainable=False)
        self.loss = self.preds * tf.random_uniform([self.n_actions])
        optimizer = tf.train.AdamOptimizer(learning_rate=1)
        self.train_op = optimizer.minimize(self.loss, global_step=self.global_step)

    def get_preds(self, inputs):
        preds = tf.contrib.layers.flatten(inputs)
        preds = tf.matmul(preds, self.w) + self.b
        return preds


    #
    # API for train loop:
    #

    def get_action(self, state):
        """
        :param state: A numpy array with a single state (shape: (1, 84, 84, 4))

        :return: The action from the policy (an int in [0, self.n_actions])
        """
        return randint(0, self.n_actions - 1)

    def train_step(self, states, actions, rewards, terminal):
        """
        :param states: A numpy array with a batch of states (shape: (batch, 84, 84, 4))
        :param actions: A numpy array with a batch of actions (shape: (batch))
        :param rewards: A numpy array with a batch of rewards (shape: (batch))
        :param terminal: A numpy array with a batch of terminal (shape: (batch))

        :return: The action from the policy (an int in [0, self.n_actions])
        """
        _, global_step = self.sess.run([self.train_op, self.global_step],
                                        feed_dict={self.input: states})

        if global_step % 100 == 0:
            print 'Step: ', global_step

        return global_step
