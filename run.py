import tensorflow as tf
import numpy as np

from utils import get_env, parse_args, transform_monitor, show_state

from random_agent import RandomAgent
from acktr_model import ACKTRModel
import collections
import constants as c

from atari_wrapper import EpisodicLifeEnv

class Runner:
    def __init__(self, args):
        self.args = args
        self.env = get_env(self.args.env,
                           results_save_dir=self.args.results_dir,
                           seed=self.args.seed,
                           num_envs=self.args.num_envs)

        self.global_step = 0

        self.agent = ACKTRModel(tf.Session(), self.args, self.env.action_space.n)

        # The last state for each env
        self.states = self.env.reset()

    def get_batch(self):
        batch_states = []
        batch_actions = []
        batch_rewards = []
        batch_terminals = []

        # Take the number of steps across all envs to fill a batch

        # TODO: Fix episode summaries with subproc_vec_env
        num_steps = self.args.batch_size // self.args.num_envs
        for step_num in xrange(num_steps):
            # Pick an action and perform it in the envs
            actions = self.agent.get_actions(self.states)
            next_states, rewards, terminals, infos = self.env.step(actions)


            # This will trigger when the 0th env has a "real done." ie a full episode has finished.
            if infos[0]['real_done']:
                print '-' * 30
                print 'Episode:        ', infos[0]['num_eps']
                print 'Train steps:    ', self.global_step
                print 'Env steps:      ', self.env.num_steps
                print 'Episode reward: ', infos[0]['ep_reward']
                print '-' * 30

                self.agent.write_ep_reward_summary(infos[0]['ep_reward'], infos[0]['env_steps'])


            # Store the SARS
            batch_states.append(self.states)
            batch_actions.append(actions)
            batch_rewards.append(rewards)
            batch_terminals.append(terminals)

            self.states = next_states

        # Next state for each step in an env is the last state for that env in this batch
        batch_next_states = np.empty((num_steps, self.args.num_envs, c.IN_HEIGHT, c.IN_WIDTH, c.IN_CHANNELS))
        for i in xrange(num_steps):
            for j in xrange(self.args.num_envs):
                batch_next_states[i, j] = next_states[j]

        # Flipping from num_steps x num_envs to num_envs x num_steps
        #  (20 x 32 to 32 x 20)
        batch_states = np.array(batch_states).swapaxes(1, 0)
        batch_actions = np.array(batch_actions).swapaxes(1, 0)
        batch_next_states = batch_next_states.swapaxes(1, 0)
        batch_rewards = np.array(batch_rewards).swapaxes(1, 0)
        batch_terminals = np.array(batch_terminals).swapaxes(1, 0)


        # Compute the discounted reward
        # NOTE: the discounted reward is computed over the num_steps
        #       rewards earlier get more "look ahead" reward added
        #       to them than later states
        for i, rewards in enumerate(batch_rewards):
            new_rewards = []
            # TODO: They don't stop when they hit a terminal, but maybe we should
            for j, r in enumerate(rewards):
                r_d = r * self.args.gamma ** j
                new_rewards.append(r_d)

            batch_rewards[i, :] = np.array(new_rewards)

        return (batch_states.reshape((self.args.batch_size, c.IN_HEIGHT, c.IN_WIDTH, c.IN_CHANNELS)),
                batch_actions.flatten(),
                batch_rewards.flatten(),
                batch_next_states.reshape((self.args.batch_size, c.IN_HEIGHT, c.IN_WIDTH, c.IN_CHANNELS)),
                batch_terminals.flatten())


    def run(self):
        print '-' * 30

        while self.env.num_steps < self.args.num_steps * 1.1:
            if self.args.train:
                states, actions, rewards, next_states, terminals = self.get_batch()

                self.global_step = self.agent.train_step(states,
                                                         actions,
                                                         rewards,
                                                         next_states,
                                                         terminals,
                                                         self.env.num_steps)

                print 'Train step %d' % self.global_step

        # Close the env and write monitor results to disk
        self.env.close()

        # The monitor won't be transformed if this script is killed early. In the
        # case that it is, run transform_monitor.py independently.
        transform_monitor(self.args.results_dir, self.args.env)


if __name__ == '__main__':
    runner = Runner(parse_args())
    runner.run()
