import os
import time
import re
import json
from slackclient import SlackClient
from utilities import *

"""
TODO:
- super tic tac Toe (on hold)
- pokemon??
"""
# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
bot_id = None

# Constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

# Teams
RED_TEAM = []
BLUE_TEAM = []
red_wins = 0
blue_wins = 0
members_list = {}
counter = 0
addcounter = 0

# Tic tac toe set
ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]]
ttt_turn = 0
countTurns = 0

# Super Tic tac toe set
sttt_turn = 0

# Connect 4 set
c4_board = [[0 for x in range(0,7)] for y in range(0,7)]
c4_turn = 0
c4_total_turns = 0

# Battleship set
red_bship_board, blue_bship_board = setupBattleship([[0 for x in range(0,10)] for y in range(0,10)], [[0 for x in range(0,10)] for y in range(0,10)])
red_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
blue_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
bship_turn = 0

def construct_userlist(userlist, channel_user_list):
    """
        Creates a userID -> Real Name mapping of all users in the channel given all existing users
        :param userlist: JSON returned by users.list api call
        :param channel_user_list: list of members in a specific channel (by ID)
    """
    global bot_id
    member_dict = {}
    for member_info in userlist["members"]:
        if member_info["real_name"] is "tabletop_bot":
            bot_id = member_info["id"]
        if member_info["id"] in channel_user_list:
            name = member_info["real_name"].encode("ascii", "ignore")
            member_dict[member_info["id"]] = name
    return member_dict

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of user_id, command, channel
        If its not found, then this function returns None.
        Also handles users joining and leaving the channel by updating member list with new users and removing
        team members who leave the channel.
        :param slack_events: incoming events from the Slack RTM API
    """
    channel = ""
    global addcounter, member_list
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            blank, message = parse_direct_mention(event["text"])
            user_id = event["user"]
            channel = event["channel"]
            return user_id, message, event["channel"]
        #if a user joins, add them to a team based on team size (or alternate if same)
        if event["type"] == "member_joined_channel":
            if event["user"] in RED_TEAM or event["user"] in BLUE_TEAM:
                return None, None, None
            response = "Welcome to "
            channel = event["channel"]
            #team balancing logic
            if len(RED_TEAM) < len(BLUE_TEAM):
                response += "Red Team, "
                RED_TEAM.append(event["user"])
            elif len(RED_TEAM) > len(BLUE_TEAM):
                response += "Blue Team, "
                BLUE_TEAM.append(event["user"])
            else:
                if addcounter == 0:
                    response += "Red Team, "
                    RED_TEAM.append(event["user"])
                if addcounter == 1:
                    response += "Blue Team, "
                    BLUE_TEAM.append(event["user"])
                addcounter = (addcounter + 1) % 2
            newuser_info = slack_client.api_call("users.info", user=event["user"])
            members_list[event["user"]] = newuser_info["user"]["name"]
            response += str(members_list[event["user"]]) + "!"
            #print("found name as: " + members_list[event["user"]])
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
        #if a user leaves the channel, remove them from the team
        if event["type"] == "member_left_channel":
            if event["user"] in RED_TEAM:
                RED_TEAM.remove(event["user"])
            elif event["user"] in BLUE_TEAM:
                BLUE_TEAM.remove(event["user"])
    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(user_id, command, channel):
    """
        Executes bot command if the command is known, and passes it to the correct handler
        ttt = tic tac Toe
        sttt = Super tic tac toe
        c4 = Connect 4
        battleship/fire = play battleship
        leaderboard = Show the current leaderboard standings
        :param user_id: user ID that was read from the slack real-time messaging event
        :param command: user's command (after being stripped of direct mention)
        :param channel: current operating channel (by ID), parsed from RTM Event
    """
    if command.startswith("help"):
        handleHelp(user_id, command, channel)

    if command.startswith("ttt"):
        handleTTT(user_id, command, channel)

    if command.startswith("sttt"):
        handleSTTT(user_id, command, channel)

    if command.startswith("c4"):
        handleC4(user_id, command, channel)

    if command.startswith("battleship") or command.startswith("fire"):
        handleBattleship(user_id, command, channel)

    if command.startswith("leaderboard"):
        showLeaderboard(user_id, command, channel)

def handleHelp(user_id, command, channel):
    """
        Command <help> enumerates all possible commands for new users
    """
    response = ""
    response += "Hi! I'm tabletop bot - I currently support playing *Tic-Tac-Toe*, *Connect 4* and *Battleship* with your whole slack team on this channel!\n"
    response += "{}, you are currently on {}.\n".format(members_list[user_id].split(" ")[0], getUserTeam(user_id))
    response += "Preface all commands with a Direct Mention @tabletop_bot.\n"
    response += "To get started, try these commands for the games you wan to play: \n"
    response += "1. `ttt-help`: displays info about the tic tac toe game, and how to participate.\n"
    response += "2. `c4-help`: displays info about connect 4, and how to join.\n"
    response += "3. `ttt-play [1-9]`: place a tic tac toe marker for your team at spot 1-9 on the board. Example: `ttt-play 2`.\n"
    response += "4. `c4-play [1-7]`: place a marker for your team on the connect 4 board at columns 1-7. Example: `c4-play 7`.\n"
    response += "5. `battleship-start`: starts a new game of battleship! (places ships randomly for both teams)\n"
    response += "Check the leaderboard with the `leaderboard` command!"
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )
    return None

def showLeaderboard(user_id, command, channel):
    """
        Command <leaderboard> will display the current leaderboard using Slack's message attachment API
    """
    global red_wins, blue_wins
    text = ""
    attachment = json.dumps([
    {
        "color": "#ff2b2b",
        "text": "Red Team points: " + str(red_wins),
    },
    {
        "color": "008fef",
        "text": "Blue Team points: " + str(blue_wins)
    }
    ])
    if red_wins > blue_wins:
        text = "Red Team seems to be winning here!"
    elif blue_wins > red_wins:
        text = "Hmm... it seems Blue Team is winning!"
    else:
        text = "You're evenly matched!"
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        attachments=attachment
    )

def handleTTT(user_id, command, channel):
    """
        Maintains and updates the on-going tic tac toe game in the slack through commands
        :param user_id: The user's ID assigned by Slack
        :param command: User's parsed command with the direct mention removed
        :param channel: Channel ID that the bot is operating in
    """
    ttt_start = "ttt-start"
    ttt_play = "ttt-play"
    ttt_help = "ttt-help"
    placement = lambda y: {1:(0,0), 2:(0,1), 3:(0,2), 4:(1,0), 5:(1,1), 6:(1,2), 7:(2,0), 8:(2,1), 9:(2,2)}[y]
    global countTurns, ttt_turn, ttt_board, red_wins, blue_wins

    # Finds and executes the given command, filling in response
    response = ""

    """
        Command <ttt-start>: restarts the game, initiates turn where it left off
    """
    if command.startswith(ttt_start):
        ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]]
        ttt_turn = 0
        countTurns = 0
        response = "Starting Tic-Tac-Toe! It is now {}'s turn. This is the board:\n".format(currentTurn(ttt_turn))
        visualizeTTT(channel)
        response += "To participate type: `@tabletop-bot ttt-play [1-9]` Must be 1-9 from top left -> bottom right."

    """
        Command <ttt-help>: prints out a helper message so the user can figure out their team and how to play
    """
    if command.startswith(ttt_help):
        response += "To participate type: `@tabletop-bot ttt-play [1-9]` where 1-9 correspond to top left -> bottom right."
        response += "\n[1] [2] [3]\n[4] [5] [6]\n [7] [8] [9]\n"
        response += "You are on {}. It is currently {}'s turn.\n".format(getUserTeam(user_id) , currentTurn(ttt_turn))

    """
        Command <ttt-play [1-9]>: takes in a user input target 1-9 and places their respective mark on the board
    """
    if command.startswith(ttt_play):
        target = command.split(" ")
        if(len(target) < 2): #make sure the user has entered the command correctly
            response = "Check your syntax: try `@tabletop_bot ttt-play [1-9]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        target = target[1]
        try:
            target = int(target)
        except TypeError:
            response = "Illegal command format: try `@tabletop_bot ttt-play [1-9]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None

        if target < 1 or target > 9:
            response = "Illegal bounds on target coordinates. Must be 1-9 which correspond to top-left -> bottom-right"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        targetx,targety = placement(target)

        if ttt_turn == 0 and str(user_id) in RED_TEAM: #valid action -> handle it
            if ttt_board[targetx][targety] is "-":
                ttt_board[targetx][targety] = "X"
            else:
                response = "Cannot place there, there already exists a mark."
                response += "\n"
                for x in ttt_board:
                    response += str(x)
                    response += " "
                    response += "\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                return None
        elif ttt_turn == 1 and str(user_id) in BLUE_TEAM: #valid action -> handle it
            if ttt_board[targetx][targety] is "-":
                ttt_board[targetx][targety] = "O"
            else:
                response = "Cannot place there, there already exists a mark."
                response += "\n"
                visualizeTTT(channel)
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                return None
        else:
            response = "It is not your team's turn {}, it is currently {}'s turn.\n".format(members_list[user_id].split(" ")[0], currentTurn(ttt_turn))
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None

        countTurns += 1 #check the overall number of turns in the game, if too many, call it.

        #print the current board state
        visualizeTTT(channel)

        #victory check after every move, and restart the game if a victor is found
        if CheckTTTVictory(targetx, targety, ttt_board):
            response += "\nCongrats! {} has won this round! Play another round with `@tabletop_bot ttt-play [1-9]`\n".format(currentTurn(ttt_turn))
            response += "{} will start the next round.\n".format(currentTurn(ttt_turn))
            if ttt_turn is 0:
                red_wins += 1
            if ttt_turn is 1:
                blue_wins += 1
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]] #reset the board
            return None
        else:
            if countTurns is 9:
                response += "\nThis board looks filled... Its a tie!\n Play another round with `@tabletop_bot ttt-play [1-9]`\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]] #reset the board
                countTurns = 0
                return None

        response += "To participate type: `@tabletop-bot ttt-play [1-9]` where 1-9 correspond to top-left -> bottom-right."
        ttt_turn = (ttt_turn + 1) % 2

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )

def visualizeTTT(channel):
    """
        Method to display the current tic tac toe (TTT) board gamestate with fancy slack emojis
        :param channel: current operating channel by ID
    """
    global ttt_board
    response = ""
    for x in ttt_board:
        for y in x:
            if y == "-":
                response += " :slack: "
            elif y == "X":
                response += " :x: "
            elif y == "O":
                response += " :black_circle: "
        response += "\n"
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )

# TODO - finish STTT
def handleSTTT(user_id, command, channel):

def handleC4(user_id, command, channel):
    """
        Maintains and updates the on-going connect 4 game in the slack through commands
        :param user_id: The user's ID assigned by Slack
        :param command: User's parsed command with the direct mention removed
        :param channel: Channel ID that the bot is operating in
    """
    global c4_board, c4_turn, c4_total_turns, red_wins, blue_wins
    c4_start = "c4-start"
    c4_play = "c4-play"
    c4_help = "c4-help"

    response = ""

    """
        Command <c4-start>: (re)starts the connect 4 game, initiates turn
    """
    if command.startswith(c4_start):
        c4_board = [[0 for x in range(0,7)] for y in range(0,7)]
        c4_turn = 0
        response = "Starting Connect 4! It is now {}'s turn. This is the board:\n".format(currentTurn(c4_turn))
        response += "To participate type: `@tabletop-bot c4-play [1-7]` Must be 1-7 from left -> right columns."
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
        )
        visualizeC4(channel)
        return None

    """
        Command <c4-help>: prints out a helper message so the user can figure out their team and how to play
    """
    if command.startswith(c4_help):
        response += "To participate type: `@tabletop-bot c4-play [1-7]` where 1-7 correspond to left -> right columns on the board."
        response += "You are on {}. It is currently {}'s turn.\n".format(getUserTeam(user_id) , currentTurn(c4_turn))
        response += "In Connect 4, the goal is to connect 4 of your team's markers in a horizontal, vertical or diagonal way.\n"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
        )
        visualizeC4(channel)
        return None

    """
        Command <c4-play [1-7]: Initiates/continues a connect 4 game session between the teams
        Input [1-7] corresponds to the respective row on a 7x7 standard Connect 4 Board
    """
    if command.startswith(c4_play):
        target = command.split(" ")
        #first check if their format is correct
        if(len(target) < 2):
            response = "Check your syntax: try `@tabletop_bot c4-play [1-7]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        target = target[1] #isolate the actual target
        """ Error checking on input """
        try:
            target = int(target)
        except ValueError, TypeError:
            response = "Check your syntax: try `@tabletop_bot c4-play [1-7]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        if target < 1 or target > 7:
            response = "Check your row number. It must be 1-7 which correspond to left -> right columns"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None

        target = target - 1 #get the array index format of their target
        if c4_turn == 0 and str(user_id) in RED_TEAM: #valid action -> handle it
            c4_board[target], status = push(c4_board[target], 1)
            if status is -1:
                response += "Cannot place there, that row is full. Please select another column [1-7].\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                return None

        elif c4_turn == 1 and str(user_id) in BLUE_TEAM: #valid action -> handle it
            c4_board[target], status = push(c4_board[target], 2)
            if status is -1:
                response += "Cannot place there, that row is full. Please select another column [1-7].\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                return None
        else: #oops invalid/out of turn action
            response = "It is not your team's turn {}, it is currently {}'s turn.\n".format(members_list[user_id].split(" ")[0], currentTurn(c4_turn))
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None

        #count total number of turns, for tie/unplayable sitations
        c4_total_turns += 1
        #print the current gamestate
        visualizeC4(channel)

        #check victory here
        if checkC4Victory(c4_board, c4_turn):
            response = "Congrats! {} has won the game!! Start another round by typing `@tabletop_bot c4-play [1-7]`. *(Winning team gets first play.)*\n".format(currentTurn(c4_turn))
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            c4_board = [[0 for x in range(0,7)] for y in range(0,7)]
            if c4_turn is 0:
                red_wins += 1
            if c4_turn is 1:
                blue_wins += 1
            return None
        else:
            if c4_total_turns is 49:
                response = "I...think we've played enough. This board looks like a tie to me.\n Play another round with `@tabletop_bot c4-play [1-7]`! *(Red Team starts)*\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                c4_turn = 0
                c4_total_turns = 0
                c4_board = [[0 for x in range(0,7)] for y in range(0,7)]
                return None

        c4_turn = (c4_turn + 1) % 2

def visualizeC4(channel):
    """
        Prints out a visual representation of the Connect 4 Board state using fancy slack emojis
        :param channel: type String, Channel ID (assigned by Slack) that the bot is operating in
    """
    global c4_board
    response = ""
    for x in range(6, -1, -1):
        for y in range(0, 7):
            if c4_board[y][x] is 0:
                response += ":white_circle: "
            elif c4_board[y][x] is 1:
                response += ":red_circle: "
            elif c4_board[y][x] is 2:
                response += ":large_blue_circle: "
        response += "\n"
    response += ":one: :two: :three: :four: :five: :six: :seven:\n"
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )

def handleBattleship(user_id, command, channel):
    """
        Maintains and updates the on-going battleship game in the slack through commands
        Assigns and randomly places battleships on a board for each team.
        :param user_id: The user's ID assigned by Slack
        :param command: User's parsed command with the direct mention removed
        :param channel: Channel ID that the bot is operating in
    """
    global red_bship_board, blue_bship_board, red_hit_detection, blue_hit_detection, bship_turn
    global red_wins, blue_wins
    bs_start = "battleship-start"
    bs_play = "fire"
    bs_help = "battleship-help"

    response = ""

    """
        Command <battleship-start>: (re)starts the battleship game, initiates turn
        Will also set up a new board with a new ship layout and reset the hit detection boards
    """
    if command.startswith(bs_start):
        red_bship_board, blue_bship_board = setupBattleship(red_bship_board, blue_bship_board)
        red_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
        blue_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
        bship_turn = 0
        response = "Starting Battleship! It is now {}'s turn.\n".format(currentTurn(bship_turn))
        response += "The ships have been placed! *You will not see your ships, only where you've fired*.\n"
        response += "To shoot, type: `@tabletop-bot fire [A-J] [1-10]` where A-J are rows, 1-10 correspond to the columns of the board.\n"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
        )
        return None

    """
        Command <battleship-help>: prints out a helper message so the user can figure out their team and how to play battleship
    """
    if command.startswith(bs_help):
        response += "To participate type: `@tabletop-bot fire [A-J] [1-10]` where A-J are rows, and 1-10 are columns left -> right."
        response += "\nYou are on {}. It is currently {}'s turn.\n".format(getUserTeam(user_id), currentTurn(bship_turn))
        response += "In Battleship, this is where your team has currently hit/missed. The objective is to destroy all your enemies ships by correctly placing your shots!\n"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
        )
        if bship_turn is 0:
            visualizeBS(red_hit_detection)
        else:
            visualizeBS(blue_hit_detection)
        return None

    """
        Command <fire [A-J] [1-9]>: main battleship playing command, executes the desired action of that team.
        Will print the hit-detection boards publicly because no information is leaked by doing this.
    """
    if command.startswith(bs_play):
        # Switch-style lambda functions
        placement = lambda a: {'A':0, 'B':1, 'C':2, 'D':3, 'E':4, 'F':5, 'G':6, 'H':7, 'I':8, 'J':9}[a]
        ship_name = lambda b: {1: 'Carrier', 2:'Battleship', 3:'Submarine', 4:'Destroyer', 5:'Cruiser'}[b]
        target = command.split(" ")
        if(len(target) < 3):
            response = "Check your syntax: try `@tabletop_bot fire [A-J] [1-10]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        try:
            targetx = placement(str(target[1]).upper()) #A-J -> 0-9
        except KeyError:
            response = "Check your syntax: try `@tabletop_bot fire [A-J] [1-10]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        try:
            targety = int(target[2])-1
        except ValueError, TypeError:
            response = "Check your syntax: try `@tabletop_bot fire [A-J] [1-10]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        if (targety < 0 or targety > 9):
            response = "Check your column number. It must be 1-10 which correspond to left -> right columns"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        # Execute the desired action of the turn, if its valid
        if bship_turn == 0 and str(user_id) in RED_TEAM: #valid action -> handle it
            if red_hit_detection[targetx][targety] is not 0:
                response = "Your team already fired at this location before. Please choose a new location with `@tabletop_bot fire [A-J] [1-10]`.\n"
                response += "You can visualize the current board hit/miss state for your team with `@tabletop_bot battleship-help`."
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                return None
            if blue_bship_board[targetx][targety] is not 0:
                response += "Its a hit on the enemy's "
                response += str(ship_name(blue_bship_board[targetx][targety]))
                response += "!\n"
                red_hit_detection[targetx][targety] = blue_bship_board[targetx][targety] #makes comparing easier later
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
            else:
                response += "Its a miss!\n"
                # slight future optimization: also change the corresponding battleship board for easy comparing
                # no replacing needed for win checking then?
                red_hit_detection[targetx][targety] = 'X'
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
            visualizeBS(red_hit_detection)
        elif bship_turn == 1 and str(user_id) in BLUE_TEAM: #valid action -> handle it
            if blue_hit_detection[targetx][targety] is not 0:
                response = "Your team already fired at this location before. Please choose a new location with `@tabletop_bot fire [A-J] [1-10]`.\n"
                response += "You can visualize the current board hit/miss state for your team with `@tabletop_bot battleship-help`."
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                return None
            if red_bship_board[targetx][targety] is not 0:
                response += "Its a hit on the enemy's "
                response += str(ship_name(red_bship_board[targetx][targety]))
                response += "!\n"
                blue_hit_detection[targetx][targety] = red_bship_board[targetx][targety]
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
            else:
                response += "Its a miss!\n"
                blue_hit_detection[targetx][targety] = 'X'
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
            visualizeBS(blue_hit_detection)
        else: # oops invalid/out of turn action
            response = "It is not your team's turn {}, it is currently {}'s turn.\n".format(members_list[user_id].split(" ")[0], currentTurn(c4_turn))
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None

        # Victory check: do the hit detection boards and the opposing team's boards match? If so, win
        # On win - place new ships on the boards, reset the hit detection boards, increment wins
        if bship_turn is 0:
            if checkBSVictory(red_hit_detection, blue_bship_board):
                response = "Congrats! Red Team has won the game!!\n"
                response += "A new ship layout has been set for both teams. You can start playing with `@tabletop_bot fire [A-J] [1-10]`. *Winning team gets first shot!*\n".format(currentTurn(bship_turn))
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                red_bship_board, blue_bship_board = setupBattleship(red_bship_board, blue_bship_board)
                red_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
                blue_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
                red_wins += 1
                return None
        if bship_turn is 1:
            if checkBSVictory(blue_hit_detection, red_bship_board):
                response = "Congrats! Blue Team has won the game!!\n".format(currentTurn(bship_turn))
                response += "A new ship layout has been set for both teams. You can start playing with `@tabletop_bot fire [A-J] [1-10]`. *Winning team gets first shot!*\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                red_bship_board, blue_bship_board = setupBattleship(red_bship_board, blue_bship_board)
                red_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
                blue_hit_detection = [[0 for x in range(0,10)] for y in range(0,10)]
                blue_wins += 1
                return None
        bship_turn = (bship_turn + 1) % 2

def visualizeBS(board):
    """
        Given a hit detection board for some team, visualize it. In this case, we use ? for unknowns, X for misses and
        the corresponding 1-5 ship number if it was a hit.
        Uses slack's attachment feature to make it color-coded for each team.
        :param board: a 10x10 nested list which is some team's hit-detection board
    """
    global bship_turn
    lettering = lambda a: {0:'A ', 1:'B ', 2:'C ', 3:'D', 4:'E ', 5:'F ', 6:'G', 7:'H', 8:'I  ', 9:'J '}[a]
    text = "*LEGEND*: *?* = Have not fired | *X* = MISS | *[1-5]* HIT on: (1)Carrier, (2)Battleship, (3)Submarine, (4)Destroyer, (5)Cruiser\n"
    vis = ""
    vis += "* / 1    2   3    4    5   6    7   8    9   10\n" # I dont know why this spacing turns out right but it does
    for y in range(0, len(board)):
        vis += lettering(y)
        vis += "| "
        for z in board[y]:
            if z is 0:
                vis += "? "
            else:
                vis += str(z)
            vis += "   "
        vis += "\n"
    if bship_turn is 0:
        attachment = json.dumps([
        {
            "color": "#ff2b2b",
            "text": "Red Team's Hit Board:\n " + str(vis),
        }])
    else:
        attachment = json.dumps([{
            "color": "008fef",
            "text": "Blue Team's Hit Board:\n " + str(vis)
        }
        ])
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        attachments=attachment
    )

def getUserTeam(user_id):
    """
        Returns which team the user is on in string format (for help purposes)
        :param user_id: a user's string ID assigned by Slack
    """
    global RED_TEAM, BLUE_TEAM
    if user_id in RED_TEAM:
        return "Red Team"
    elif user_id in BLUE_TEAM:
        return "Blue Team"
    else:
        return "Unknown team"

def setChannelID(bot_id):
    """
        Finds out which channel this bot is a part of and set the channel ID accordingly
        :param bot_id: bot's user ID, retrieved through constructing a user dictionary
    """
    channels = slack_client.api_call("channels.list")
    print("setting Channel ID")
    for c in channels["channels"]:
        if bot_id in c["members"]:
            print("Set bot channel to: " + str(c["name"] + " with ID: " + str(c["id"])))
            return c["id"]

if __name__ == "__main__":
    count = 0
    if slack_client.rtm_connect(with_team_state=False):
        print("Tabletop Bot connected and running!")

        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]
        # Get all users currently in the channel first, and assign them to a team
        channel_id = setChannelID(bot_id)
        channel_curr_info = slack_client.api_call("channels.info",channel=channel_id)
        members_list = construct_userlist(slack_client.api_call("users.list"), channel_curr_info["channel"]["members"])

        """
            Place all users (except bots) on either red team or blue team, alternating between each one.
            Also, after placing users on teams, create a message letting them know who's on what team.
        """
        for memID, username in members_list.iteritems():
            if username == "slackbot" or username == "tabletop_bot":
                continue
            if count == 0:
                RED_TEAM.append(memID)
            if count == 1:
                BLUE_TEAM.append(memID)
            count = (count + 1) % 2

        red_team = ""
        blue_team = ""
        if len(RED_TEAM) > 0:
            for member in RED_TEAM:
                name = members_list[member]
                red_team += name
                if(len(RED_TEAM) > 1 and member is not RED_TEAM[len(RED_TEAM) - 1]):
                    red_team += ", "
        if len(BLUE_TEAM) > 0:
            for member in BLUE_TEAM:
                name = members_list[member]
                blue_team += name
                if(len(BLUE_TEAM) > 1 and member is not BLUE_TEAM[len(BLUE_TEAM) - 1]):
                    blue_team += ", "
        if len(red_team) > 0:
            if len(RED_TEAM) == 1:
                red_team += " is"
            else:
                red_team += " are"
            red_team += " on Red Team!\n"
        if len(blue_team) > 0:
            if len(BLUE_TEAM) == 1:
                blue_team += " is"
            else:
                blue_team += " are"
            blue_team += " on Blue Team!"

        #display the teams
        slack_client.api_call(
            "chat.postMessage",
            channel=channel_id,
            text=red_team + blue_team
        )

        #keep reading all RTM events
        while True:
            user_id, command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(user_id, command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
