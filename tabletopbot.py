import os
import time
import re
from slackclient import SlackClient

"""
TODO: ~~everything~~
- add checks for row/col bound on ttt board
"""
# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None
gamesCID = "C8LJ4KMN1"

# constants
RTM_READ_DELAY = 0.1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

#teams
RED_TEAM = []
BLUE_TEAM = []
members_list = {}
counter = 0

#Tic tac toe set
ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]]
ttt_turn = 0

# userlist is a JSON returned by users.list api call
def construct_userlist(userlist):
    member_dict = {}
    for member_info in userlist["members"]:
        name = member_info["real_name"].encode("ascii", "ignore")
        member_dict[member_info["id"]] = name

    #print(member_dict)
    return member_dict

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    channel = ""
    global counter
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            blank, message = parse_direct_mention(event["text"])
            user_id = event["user"]
            #print(message + " " + user_id)
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
                return None, None, channel
            if counter == 1:
                BLUE_TEAM.append(event["user"])
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text="Welcome to Blue Team!"
                )
                counter = (counter + 1) % 2
                return None, None, channel

    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

#this method has to handle gamestate + turn order --> respond accordingly
def handle_command(user_id, command, channel):
    """
        Executes bot command if the command is known
    """
    ttt_start = "ttt-start"
    ttt_play = "ttt-play"
    global ttt_turn, ttt_board
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)
    print(user_id, command)
    # Finds and executes the given command, filling in response
    response = ""
    # This is where you start to implement more commands!
    if command.startswith(ttt_start):
        ttt_board = [["-", "-", "-"],["-", "-", "-"],["-", "-", "-"]]
        ttt_turn = 0
        response = "Starting Tic-Tac-Toe! It is now Red Team's turn. This is the board:\n"
        for x in ttt_board:
            response += str(x)
            response += " "
            response += "\n"
        #response = "Sure...write some more code then I can do that!"
        response += "To participate type: <@tabletop-bot ttt-play [1-3] [1-3]> where 1-9 correspond to the squares from top left to bottom right."

    if command.startswith(ttt_play):
        row = command.split(" ")[1]
        column = command.split(" ")[2]
        try:
            targetx = int(row) - 1
            targety = int(column) - 1
        except TypeError:
            response = "Illegal command format: try <@tabletop_bot ttt-play [1-3] [1-3]>"
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        #print(str(targetx) + " " + str(targety) + " " + str(user_id))
        if (targetx < 0 or targetx > 3) or (targety < 0 or targety > 3):
            response = "Illegal bounds on target coordinates. Must be 1-3 1-3 as row and column"
        if (ttt_turn == 0 and str(user_id) in RED_TEAM): #valid action -> handle it
            if ttt_board[targetx][targety] is "-":
                ttt_board[targetx][targety] = "X"
                ttt_turn = (ttt_turn + 1) % 2
            else:
                response = "Cannot place there, there already exists a mark."
        elif (ttt_turn == 1 and str(user_id) in BLUE_TEAM): #valid action -> handle it
            if ttt_board[targetx][targety] is "-":
                ttt_board[targetx][targety] = "O"
                ttt_turn = (ttt_turn + 1) % 2
            else:
                response = "Cannot place there, there already exists a mark."
        else:
            if ttt_turn == 0:
                turn = "Red Team"
            if ttt_turn == 1:
                turn = "Blue Team"
            response = "It is not your team's turn {}, it is currently {}'s turn.\n".format(members_list[user_id], turn)

        response += "\n"
        for x in ttt_board:
            response += str(x)
            response += " "
            response += "\n"

        if CheckTTTVictory(targetx, targety):
            if ttt_turn == 0:
                turn = "Red Team"
            if ttt_turn == 1:
                turn = "Blue Team"
            response += "\nCongrats! {} has won this round! Restart this game with <@tabletop_bot tt-start>\n".format(turn)
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=response
            )
            return None
        #response = "Sure...write some more code then I can do that!"
        response += "To participate type: <@tabletop-bot ttt-play [1-3] [1-3]> where 1-9 correspond to the squares from top left to bottom right."

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )

"""def updateBoard(x, y):"""


def CheckTTTVictory(x, y):
    global ttt_board
    #check if previous move caused a win on vertical line
    if (ttt_board[0][y] == ttt_board[1][y] == ttt_board[2][y]):
        if (ttt_board[0][y] == "-" or ttt_board[1][y] == "-" or ttt_board[2][y] == "-"):
            return False
        return True

    #check if previous move caused a win on horizontal line
    if ttt_board[x][0] == ttt_board[x][1] == ttt_board[x][2]:
        if ttt_board[x][0] == "-" or ttt_board[x][1] == "-" or ttt_board[x][2] == "-":
            return False
        return True

    #check if previous move was on the main diagonal and caused a win
    if x == y and ttt_board[0][0] == ttt_board[1][1] == ttt_board[2][2]:
        if x == y and ttt_board[0][0] == "-" or ttt_board[1][1] == "-" or ttt_board[2][2] == "-":
            return False
        return True

    #check if previous move was on the secondary diagonal and caused a win
    if x + y == 2 and ttt_board[0][2] == ttt_board[1][1] == ttt_board[2][0]:
        if x + y == 2 and ttt_board[0][2] == "-" or ttt_board[1][1] == "-" or ttt_board[2][0] == "-":
            return False
        return True

    return False

if __name__ == "__main__":
    count = 0
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")

        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        # Get all users currently in the channel first, and assign them to a team
        channel_curr_info = slack_client.api_call("channels.info",channel=gamesCID)
        members_list = construct_userlist(slack_client.api_call("users.list"))
        #print(slack_client.api_call("users.list"))
        #print(members_list)

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
                red_team += ", "
                name = ""
        if len(BLUE_TEAM) > 0:
            for member in BLUE_TEAM:
                name = members_list[member]
                blue_team += name
                if member is not BLUE_TEAM[len(BLUE_TEAM)-1]:
                    blue_team += ", "
                name = ""
        if len(red_team) > 0:
            red_team += " is on Red Team!\n"
        if len(blue_team) > 0:
            blue_team += " is on Blue Team!"

        slack_client.api_call(
            "chat.postMessage",
            channel=gamesCID,
            text=red_team + blue_team
        )

        while True:
            user_id, command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(user_id, command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
