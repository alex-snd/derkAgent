# Dr. Derk's Mutant Battlegrounds - Starter Kit

<p align="center">
  <a><img src="https://i.ibb.co/p2SCH2q/scr.png"></a>
</p>


 - 💪 Challenge Page: https://www.aicrowd.com/challenges/dr-derk-s-mutant-battlegrounds
 - 🗣 Discussion Forum: https://www.aicrowd.com/challengesdr-derk-s-mutant-battlegrounds/discussion
 - 🏆 Leaderboard: https://www.aicrowd.com/challenges/dr-derk-s-mutant-battlegrounds/leaderboards

This starter kit contains a random agent to help you easily get started with this challenge! Stay tuned for an RL baseline for you to adapt!


# 💻 Installation
```
pip3 install -U gym-derk
```

For more information, refer to the [official documentation](http://docs.gym.derkgame.com/).


## Writing your own bot
You can start with the default bot.py or create your own agent that file. You can also your own script containing DerkPlayer class format present in bot.py.

The functions that are required in the DerkPlayer class are:
* `__init__`: To initialize your player and will have the parameters `n_agents` and `action_space`
* `signal_env_reset`: To signal to your player that the environment has been reset and has the parameters `observation`
* `take_action`: This is the function where the observation will be passed and the actions for each agent are returned.

Please don't change the definition of these functions. You can add more if you want to.

# Running the Starter Kit
Run the python script:
```bash
python run.py -n 1
```

The python script has the following command line arguments: 
```console
usage: run.py [-h] [-p1 FILE_NAME_OF_PLAYER1] [-p2 FILE_NAME_OF_PLAYER2]
              [-n NUMBER_OF_ARENAS] [--fast]

optional arguments:
-h: to display help messages
-p1: The name of the file that contains player 1
-p2: The name of the file that contains player 2
-n: The number of arenas to run parallely (defaults to 2)
--fast: To enable turbo mode or not (cuts down episode time by half by speeding up animations)
```

For example, if you have `bot.py` and `oldbot.py` inside the `agent` directory, you can have a fight between them by running

```
python run.py -p1 bot -p2 oldbot
```
