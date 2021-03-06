import _init_environment

from os import mkdir
from os.path import exists, join

import numpy as np
import torch
from gym_derk.envs import DerkEnv
from sklearn.preprocessing import MinMaxScaler
from torch import optim, nn
from torch.utils.data import Dataset, DataLoader

import config
from agent.bot import DerkAgent
from models.nn import QNet


class GameHistory(Dataset):
    def __init__(self, max_game_history_size: int):
        self.max_game_history_size = max_game_history_size
        self.count = self.max_game_history_size
        self.history = list()  # (observations, actions, reward, done)
        self.temp_history = list()  # (observations, actions, reward, done)
        self.training = False

    def put(self, observations, actions, rewards, done) -> None:
        for i in range(len(done)):
            self.history.append([observations[i], actions[i], rewards[i], done[i]])
            self.count -= 1

    def reset(self) -> None:
        self.count = self.max_game_history_size

    def train_mode(self) -> None:
        if not self.training:
            self.temp_history = self.history.copy()
            self.__standardize_rewards()

    def gather_mode(self) -> None:
        if self.training:
            self.history = self.temp_history

    def __standardize_rewards(self) -> None:
        rewards = np.array([entry[2] for entry in self.history]).reshape(-1, 1)

        rewards = MinMaxScaler().fit_transform(rewards)

        print(rewards)

        for i, entry in enumerate(self.history):
            entry[2] = rewards[i]

    def is_full(self) -> bool:
        return self.count <= 0
        # return len(self.history) >= self.max_game_history_size

    def __getitem__(self, index: int) -> (torch.tensor, torch.tensor, torch.tensor):
        return torch.cat([torch.tensor(self.history[index][0], dtype=torch.float32),
                          torch.tensor(self.history[index][1], dtype=torch.float32)], dim=0), \
               torch.tensor(self.history[index][2], dtype=torch.float32)  # ([observations, actions], reward)

    def __len__(self) -> int:
        return len(self.history)


def epoch_games_history_collection(env: DerkEnv, agent: DerkAgent, game_history: GameHistory) -> None:
    game_history.gather_mode()

    with torch.no_grad():
        while not game_history.is_full():

            agent.signal_env_reset(env.reset())
            previous_env_state = env.step()

            while True:
                agents_actions = agent.take_action(previous_env_state)

                agents_observations, agents_reward, agents_done, agents_info = env.step(agents_actions)

                game_history.put(previous_env_state[0], agents_actions, agents_reward, agents_done)

                previous_env_state = (agents_observations, agents_reward, agents_done, agents_info)

                if all(agents_done):
                    break

    # game_history.standardize_rewards()


def epoch_training(estimator: QNet, optimizer, loss_func: eval, game_history: GameHistory, batch_size: int,
                   training_epochs: int, device: torch.device) -> None:
    game_history.train_mode()

    train_loader = DataLoader(game_history, batch_size=batch_size, shuffle=True,
                              num_workers=1, pin_memory=True)

    estimator.train()

    for i_epoch in range(1, training_epochs):
        batch_idx = 1
        loss = 0.0

        for batch_idx, (batch_steps, batch_rewards) in enumerate(train_loader, start=1):
            batch_steps = batch_steps.to(device)
            batch_rewards = batch_rewards.to(device)

            optimizer.zero_grad()

            predicted_rewards = estimator(batch_steps)  # .detach().cpu()

            # print(predicted_rewards[0], batch_rewards[0])

            loss = loss_func(predicted_rewards, batch_rewards.reshape(-1, 1))  # TODO CHECK
            loss.backward()
            loss += loss.item()

            optimizer.step()

        loss /= batch_idx

        print(f'Epoch: {i_epoch} - Loss: {loss}')


def save_parameters(estimator: QNet, history_path: str, i_epoch: int) -> None:
    if not exists(history_path):
        mkdir(history_path)

    estimator.save_parameters(weights_path=join(history_path, f'weights__epoch_{i_epoch}'),
                              reward_function_path=join(history_path, f'reward_function__epoch_{i_epoch}'))


def main():
    seed = 2531
    np.random.seed(seed)
    torch.manual_seed(seed)

    device = torch.device('cpu' if torch.cuda.is_available() else 'cpu')

    pretrained = True

    learning_rate = 5e-3
    batch_size = 256
    per_epoch_updating = 1
    max_game_history_size = 300
    game_epochs = 30_000
    training_epochs = 40

    estimator = QNet().to(device)

    env = DerkEnv(
        mode="train",
        turbo_mode=True,
        home_team=[
            {'primaryColor': '#ff00ff'},
            {'primaryColor': '#00ff00', 'slots': ['Talons', None, None]},
            {'primaryColor': '#ff0000', 'rewardFunction': {'healTeammate1': 1}}
        ],
        away_team=[
            {'primaryColor': '#c0c0c0'},
            {'primaryColor': 'navy', 'slots': ['Talons', None, None]},
            {'primaryColor': 'red', 'rewardFunction': {'healTeammate1': 1}}
        ],
        session_args={"reward_function": estimator.reward_function}
    )

    game_history = GameHistory(max_game_history_size)

    if exists(config.weights_path) and exists(config.reward_function_path) and pretrained:
        estimator.load_parameters(config.weights_path, config.reward_function_path)

    optimizer = optim.Adam(estimator.parameters(), lr=learning_rate)

    loss_func = nn.MSELoss()

    agent = DerkAgent(env.n_agents, estimator, device=device)

    try:
        for i_epoch in range(1, game_epochs + 1):
            epsilon = max(0.01, 0.2 - 0.01 * (i_epoch / 200))  # Linear annealing from 8% to 1%  0.08

            agent.update_epsilon(epsilon)
            game_history.reset()

            epoch_games_history_collection(env, agent, game_history)

            epoch_training(estimator, optimizer, loss_func, game_history, batch_size, training_epochs, device)

            if i_epoch % per_epoch_updating == 0:
                print(f'Games epoch: {i_epoch} - Total reward: {env.total_reward}')

                agent.update_estimator(estimator)
                save_parameters(estimator, config.weights_history_path, i_epoch)

    except KeyboardInterrupt:
        print('Interrupted')

    finally:
        print('*Game closing*')
        env.close()


if __name__ == '__main__':
    main()

    # asyncio.get_event_loop().run_until_complete(main())
