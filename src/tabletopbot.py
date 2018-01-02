import os
import time
import re
import json
from slackclient import SlackClient
from utilities import *

"""
TODO:
- Scoreboard
- super tic tac Toe (on hold)
- battleship
- pokemon??
"""
# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# constants
RTM_READ_DELAY = 0.1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

#teams
RED_TEAM = []
BLUE_TEAM = []
red_wins = 0
blue_wins = 0
members_list = {}
counter = 0

#Tic tac toe set
ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]]
ttt_turn = 0
countTurns = 0

#Super Tic tac toe set
sttt_turn = 0

#Connect 4 set
c4_board = [[0 for x in range(0,7)] for y in range(0,7)]
c4_turn = 0
c4_total_turns = 0

"""
    Creates a userID -> Real Name mapping of all users on the team
    @param userlist is a JSON returned by users.list api call
"""
def construct_userlist(userlist):
    global bot_id
    member_dict = {}
    for member_info in userlist["members"]:
        if member_info["real_name"] is "tabletop_bot":
            bot_id = member_info["id"]
        name = member_info["real_name"].encode("ascii", "ignore")
        member_dict[member_info["id"]] = name
    return member_dict

"""
    Parses a list of events coming from the Slack RTM API to find bot commands.
    If a bot command is found, this function returns a tuple of command and channel.
    If its not found, then this function returns None, None.
"""
def parse_bot_commands(slack_events):
    channel = ""
    global counter
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            blank, message = parse_direct_mention(event["text"])
            user_id = event["user"]
            channel = event["channel"]
            return user_id, message, event["channel"]
        if event["type"] == "team_join" and not "subtype" in event:
            if counter == 0:
                RED_TEAM.append(event["user"])
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text="Welcome to Red Team!"
                )
                counter = (counter + 1) % 2
            if counter == 1:
                BLUE_TEAM.append(event["user"])
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text="Welcome to Blue Team!"
                )
                counter = (counter + 1) % 2
    return None, None, None

"""
    Finds a direct mention (a mention that is at the beginning) in message text
    and returns the user ID which was mentioned. If there is no direct mention, returns None
"""
def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

"""
    Executes bot command if the command is known, and passes it to the correct handler
    TTT = tic tac Toe
    STTT = Super tic tac toe
    c4 = Connect 4
    leaderboard = Show the current leaderboard standings
"""
def handle_command(user_id, command, channel):
    if command.startswith("ttt"):
        handleTTT(user_id, command, channel)

    if command.startswith("sttt"):
        handleSTTT(user_id, command, channel)

    if command.startswith("c4"):
        handleC4(user_id, command, channel)

    if command.startswith("leaderboard"):
        showLeaderboard(user_id, command, channel)

"""
    Command <leaderboard> will display the current leaderboard using Slack's message attachment API
"""
def showLeaderboard(user_id, command, channel):
    global red_wins, blue_wins
    text = ""
    attachment = json.dumps([
    {
        "color": "#ff2b2b",
        "text": "Red Team is at: " + str(red_wins),
    },
    {
        "color": "008fef",
        "text": "Blue Team is at: " + str(blue_wins)
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
        #response = "Sure...write some more code then I can do that!"
        response += "To participate type: `@tabletop-bot ttt-play [1-9]` Must be 1-9 from top left -> bottom right."

    """
        Command <ttt-help>: prints out a helper message so the user can figure out their team and how to play
    """
    if command.startswith(ttt_help):
        response += "To participate type: `@tabletop-bot ttt-play [1-9]` where 1-9 correspond to top left -> bottom right."
        response += "\n[1] [2] [3]\n[4] [5] [6]\n [7] [8] [9]\n"
        response += "You are on {}. It is currently {}'s turn.\n".format(getUserTeam(user_id) , currentTurn(ttt_turn))

    """
        Command <ttt-play [1-9]`: takes in a user input target 1-9 and places their respective mark on the board
    """
    if command.startswith(ttt_play):
        target = command.split(" ")[1]
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
            response = "Illegal bounds on target coordinates. Must be 1-9 which correspond to top left -> bottom right"
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
                response += "\nEnough - this board looks filled. Its a tie!\n Play another round with `@tabletop_bot ttt-play [1-9]`\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]] #reset the board
                countTurns = 0
                return None

        response += "To participate type: `@tabletop-bot ttt-play [1-9]` where 1-9 correspond to top-left to bottom-right."
        ttt_turn = (ttt_turn + 1) % 2

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )

"""
    Method to display the current tic tac toe (TTT) board gamestate with fancy slack emojis
"""
def visualizeTTT(channel):
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

def handleSTTT(user_id, command, channel):
    global sttt_turn
    sttt_start = "sttt-start"
    sttt_play = "sttt-play"
    sttt_help = "sttt-help"
    placement = lambda y: {1:(0,0), 2:(0,1), 3:(0,2), 4:(1,0), 5:(1,1), 6:(1,2), 7:(2,0), 8:(2,1), 9:(2,2)}[y]
    outer_placement = lambda y: {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7, 'i':8}[y]
    count = 0
    sttt_board = [[["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]],
                    [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]],
                    [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]]]
    # Default response is help text for the user

    # Finds and executes the given command, filling in response
    response = ""
    # This is where you start to implement more commands!
    if command.startswith(sttt_start):
        sttt_turn = 0
        response = "Starting SUPER Tic-Tac-Toe! It is now Red Team's turn. This is the board:\n"
        count = 0
        #will work out rendering a better image later
        sttt_board = [[["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],[["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]],
                        [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]],
                        [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]], [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]]]]
        #Actual output visualization should be:
        #[0][0] [1][0] [2][0]
        #[0][1] [1][1] [2][1]
        #[0][2] [1][2] [2][2]
        #divider
        #[3][0] [4][0] [5][0]
        #...
        #[3][2] [4][2] [5][2]
        #divider
        #[6][0] [7][0] [8][0]
        #...
        #[6][2] [7][2] [8][2]
        for x in sttt_board:
            response += str(x[0])
            response += " || "
            response += str(x[1])
            response += " || "
            response += str(x[2])
            count += 3
            if count % 3 == 0:
                response += "\n"
            if count % 9 == 0:
                response += "=======||=======||=======\n"

        #response = "Sure...write some more code then I can do that!"
        response += "To participate type: `@tabletop-bot sttt-play [a-i] [1-9]` Where a-i correspond to the outer boards top-left -> bottom right and 1-9 from top left -> bottom right in the respective inner squares"

    if command.startswith(sttt_help):
        response += "To participate type: `@tabletop-bot sttt-play [a-i] [1-9]` Where a-i correspond to the outer boards top-left -> bottom right and 1-9 from top left -> bottom right in the respective inner squares"
        response += "Outer Boards: [a] [b] [c]\n[d] [e] [f]\n[g] [h] [i]\nInner Boards for each a-i: [1] [2] [3]\n[4] [5] [6]\n [7] [8] [9]\n"
        response += "You are on {}. It is currently {}'s turn.\n".format(getUserTeam(user_id) , currentTurn(ttt_turn))


    if command.startswith(sttt_play):
        target_outer = command.split(" ")[1]
        target_inner = command.split(" ")[2]
        try:
            target_inner = int(target_inner)
        except TypeError:
            response = "Illegal command format: try `@tabletop_bot ttt-play [1-9]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None

        if (target_inner < 1 or target_inner > 9) or (target_outer < 'a' or target_outer > 'i'):
            response = "Illegal bounds on target coordinates. Must be a-i 1-9 which correspond to top left -> bottom right outer and inner"
        targetx,targety = placement(target_inner)
        outertarget = outer_placement(target_outer)

        if sttt_turn == 0 and str(user_id) in RED_TEAM: #valid action -> handle it
            if sttt_board[outertarget][targetx][targety] is "-":
                sttt_board[outertarget][targetx][targety] = "X"
                sttt_turn = (sttt_turn + 1) % 2
            else:
                response = "Cannot place there, there already exists a mark."
        elif sttt_turn == 1 and str(user_id) in BLUE_TEAM: #valid action -> handle it
            if sttt_board[outertarget][targetx][targety] is "-":
                sttt_board[outertarget][targetx][targety] = "O"
                sttt_turn = (sttt_turn + 1) % 2
            else:
                response = "Cannot place there, there already exists a mark."
        else:
            response = "It is not your team's turn {}, it is currently {}'s turn.\n".format(members_list[user_id], currentTurn(ttt_turn))

        response += "\n"
        counter = 0
        for x in sttt_board:
            response += str(x[0])
            response += " || "
            response += str(x[1])
            response += " || "
            response += str(x[2])
            count += 3
            if count % 3 == 0:
                response += "\n"
            if count % 9 == 0:
                response += "=======||=======||=======\n"

        """if CheckTTTVictory(targetx, targety):
            response += "\nCongrats! {} has won this round! Restart this game with `@tabletop_bot ttt-start>\n".format(currentTurn(ttt_turn))
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None"""
        #response = "Sure...write some more code then I can do that!"
        response += "To participate type: `@tabletop-bot ttt-play [1-9]` where 1-9 correspond to top-left to bottom-right."
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )

"""
    Maintains and updates the on-going connect 4 game in the slack through commands
"""
def handleC4(user_id, command, channel):
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
        #response = "Sure...write some more code then I can do that!"
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
        response += "You are on {}. It is currently {}'s turn.\n".format(getUserTeam(user_id) , currentTurn(ttt_turn))
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
        except TypeError:
            response = "Check your syntax: try `@tabletop_bot c4-play [1-7]`"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        if target < 1 or target > 7:
            response = "Check your row number. It must be 1-7 which correspond to left -> right rows"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None

        target = target - 1 #get the array index format of their target
        if c4_turn == 0 and str(user_id) in RED_TEAM: #valid action -> handle it
            c4_board[target], status, y = push(c4_board[target], 1)
            if status is -1:
                response += "Cannot place there, that row is full. Please select another row [1-7].\n"
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=response
                )
                return None

        elif c4_turn == 1 and str(user_id) in BLUE_TEAM: #valid action -> handle it
            c4_board[target], status, y = push(c4_board[target], 2)
            if status is -1:
                response += "Cannot place there, that row is full. Please select another row [1-7].\n"
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
            if ttt_turn is 0:
                red_wins += 1
            if ttt_turn is 1:
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

"""
    Prints out a visual representation of the Connect 4 Board state using fancy slack emojis
"""
def visualizeC4(channel):
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

"""
    Returns which team the user is on in string format (for help purposes)
"""
def getUserTeam(user_id):
    global RED_TEAM, BLUE_TEAM
    if user_id in RED_TEAM:
        return "Red Team"
    elif user_id in BLUE_TEAM:
        return "Blue Team"
    else:
        return "Unknown team"

"""
    Finds out which channel this bot is a part of and set the channel ID accordingly
"""
def setChannelID(members_list, bot_id):
    channels = slack_client.api_call("channels.list")
    print("setting Channel ID")
    for c in channels["channels"]:
        if bot_id in c["members"]:
            gamesCID = c["id"]
            print("Set bot channel to: " + str(c["name"] + " with ID: " + str(c["id"])))
            return c["id"]

if __name__ == "__main__":
    count = 0
    if slack_client.rtm_connect(with_team_state=False):
        print("Tabletop Bot connected and running!")

        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]
        # Get all users currently in the channel first, and assign them to a team
        channel_id = setChannelID(members_list, bot_id)
        members_list = construct_userlist(slack_client.api_call("users.list"))
        channel_curr_info = slack_client.api_call("channels.info",channel=channel_id)

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
