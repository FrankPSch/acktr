import tensorflow as tf
import numpy as np

from utils import get_env, parse_args, transform_monitor

from random_agent import RandomAgent
from acktr_model import ACKTRModel

def run(args):
    env = get_env(args.env,
                  results_save_dir=args.results_dir,
                  seed=args.seed)

    sess = tf.Session()
    # TODO: Switch to ACKTR model
    # agent = ACKTRModel(sess, args, env.action_space.n)
    agent = RandomAgent(sess, args, env.action_space.n)
    sess.run(tf.global_variables_initializer())

    global_step = 0
    for ep in xrange(args.num_eps):
        print '-' * 30
        print 'Episode: ', ep
        print '-' * 30

        state = env.reset()

        while True:
            action = agent.get_action(np.expand_dims(state, axis=0))
            state, reward, terminal, _ = env.step(action)

            if args.render:
                env.render()

            if args.train:
                # TODO: Figure out batching.
                global_step = agent.train_step(np.expand_dims(state, axis=0),
                                               np.array([action]),
                                               np.array([reward]),
                                               np.array([terminal]))

            if terminal or global_step > args.num_steps:
                break

        if global_step > args.num_steps:
            break

    # Close the env and write monitor results to disk
    env.close()

    # The monitor won't be transformed if this script is killed early. In the
    # case that it is, run transform_monitor.py independently.
    transform_monitor(args.results_dir, args.env)


if __name__ == '__main__':
    run(parse_args())