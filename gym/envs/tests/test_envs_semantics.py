import numpy as np
import json
import hashlib
import os

from nose2 import tools
import logging
logger = logging.getLogger(__name__)

from gym import envs, spaces

from test_envs import should_skip_env_spec_for_tests

DATA_DIR = os.path.dirname(__file__)
ROLLOUT_FILE = os.path.join(DATA_DIR, 'rollout.json')
ROLLOUT_STEPS = 100
episodes = ROLLOUT_STEPS
steps = ROLLOUT_STEPS

if not os.path.isfile(ROLLOUT_FILE): 
  with open(ROLLOUT_FILE, "w") as outfile:
    json.dump({}, outfile, indent=2)

def generate_rollout_hash(spec):
  spaces.seed(0)
  env = spec.make()
  env.seed(0)

  observation_list = []
  action_list = []
  reward_list = []
  done_list = []

  total_steps = 0
  for episode in xrange(episodes):
    if total_steps >= ROLLOUT_STEPS: break
    observation = env.reset()

    for step in xrange(steps):
      action = env.action_space.sample()
      observation, reward, done, _ = env.step(action)

      action_list.append(action)
      observation_list.append(observation)
      reward_list.append(reward)
      done_list.append(done)

      total_steps += 1
      if total_steps >= ROLLOUT_STEPS: break

      if done: break

  observations_hash = hashlib.sha1(str(observation_list)).hexdigest()
  actions_hash = hashlib.sha1(str(action_list)).hexdigest()
  rewards_hash = hashlib.sha1(str(reward_list)).hexdigest()
  dones_hash = hashlib.sha1(str(done_list)).hexdigest()

  return observations_hash, actions_hash, rewards_hash, dones_hash

specs = [spec for spec in envs.registry.all() if spec._entry_point is not None]
@tools.params(*specs)
def test_env_semantics(spec):
  with open(ROLLOUT_FILE) as data_file:
    rollout_dict = json.load(data_file)

  if spec.id not in rollout_dict:
    if not spec.nondeterministic or should_skip_env_spec_for_tests(spec):
      logger.warn("Rollout does not exist for {}, run generate_json.py to generate rollouts for new envs".format(spec.id))
    return

  logger.info("Testing rollout for {} environment...".format(spec.id))

  observations_now, actions_now, rewards_now, dones_now = generate_rollout_hash(spec)

  assert rollout_dict[spec.id]['observations'] == observations_now, 'Observations not equal for {}'.format(spec.id)
  assert rollout_dict[spec.id]['actions'] == actions_now, 'Actions not equal for {}'.format(spec.id)
  assert rollout_dict[spec.id]['rewards'] == rewards_now, 'Rewards not equal for {}'.format(spec.id)
  assert rollout_dict[spec.id]['dones'] == dones_now, 'Dones not equal for {}'.format(spec.id)


def test_all_env_semantics():
  specs = [spec for spec in envs.registry.all() if spec._entry_point is not None]

  for spec in specs: 
    test_env_semantics(spec)


#test_all_env_semantics()
