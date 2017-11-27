import tensorflow as tf
import numpy as np

from utils import get_env, parse_args, transform_monitor

from random_agent import RandomAgent
from acktr_model import ACKTRModel
import collections
import constants as c


batch = {}

def add_sars_to_batch(sars, r_d):
    global batch
    batch['state'].append(sars[0])
    batch['action'].append(sars[1])
    batch['reward'].append(r_d)
    batch['terminal'].append(sars[3])

def reset_batch():
    global batch
    batch = {
        'state': [],
        'action': [],
        'reward': [],
        'terminal': []
    }

def run(args):
    global batch

    env = get_env(args.env,
                  results_save_dir=args.results_dir,
                  seed=args.seed)

    sess = tf.Session()
    # TODO: Switch to ACKTR model
    agent = ACKTRModel(sess, args, env.action_space.n)
    # agent = RandomAgent(sess, args, env.action_space.n)
    sess.run(tf.global_variables_initializer())

    global_step = 0
    for ep in xrange(args.num_eps):
        print '-' * 30
        print 'Episode: ', ep
        print '-' * 30

        state = env.reset()

        buff = collections.deque(args.k)
        reset_batch()

        while True:
            # Fill up the batch until it is full or we reach a terminal state
            if len(batch['action']) < args.batch_size and not terminal:
                start_state = state
                action = agent.get_action(np.expand_dims(state, axis=0))
                state, reward, terminal, _ = env.step(action)

                # The SARS queue is full so the first item will be popped off
                if len(buff) == args.k:
                    popped_sars = buff[0]

                    # Compute the discounted reward
                    r_d = 0
                    for i in range(args.k):
                        r_d += buff[i][2] * args.gamma**i

                    # Add the SARS to the batch
                    add_sars_to_batch(popped_sars, r_d)

                buff.append((start_state, action, reward, terminal))
            else:
                if args.render:
                    env.render()

                if args.train:
                    # Convert the batch dict to numpy arrays
                    states = np.array(batch['state'])
                    actions = np.array(batch['action'])
                    rewards = np.array(batch['reward'])
                    terminals = np.array(batch['terminal'])

                    # TODO 1. check on the shape of states
                    # TODO 2. do we need next states somewhere (might be related to 1.)
                    global_step = agent.train_step(states,
                                                   actions,
                                                   rewards,
                                                   terminals)

                    # Reset the batch
                    reset_batch()

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
