# Slack Plays Tabletop games
A simple slackbot that allows you to add team game functionality to your workspace!
Currently supports tic-tac-toe and Connect 4!

# Installation
- clone the directory
- $virtualenv tbbot
- $source tbbot/bin/activate
- $pip install -r requirements.txt
- export SLACK_BOT_TOKEN="your-bot-user-access-token-goes-here"
- python tabletopbot.py

# Usage
Add this bot as an app to any channel, and run the bot. The following commands can be used to interface with the bot:
- \@tabletop_bot ttt-[help/start/play] [1-9] to initiate a tic tac toe session in the channel
- \@tabletop_bot c4-[help/start/play] [1-7] to initiate a connect 4 session in the channel
- \@tabletop_bot leaderboard will show the current leaderboard

# Check it out in action!
![](ttt.png)
![](connect4.png)
