import os
import time
import re
from slackclient import SlackClient

"""
TODO: ~~everything~~
"""
# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None
gamesCID = "C8LJ4KMN1"

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

#teams
RED_TEAM = []
BLUE_TEAM = []
members_list = {}


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
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                channel = event["channel"]
                return message, event["channel"]
        if event["type"] == "team_join" and not "subtype" in event:
            if counter == 0:
                RED_TEAM.append(event["user"])
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text="Welcome to Red Team!"
                )
                counter = (counter + 1) % 2
                return None, channel
            if counter == 1:
                BLUE_TEAM.append(event["user"])
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text="Welcome to Blue Team!"
                )
                counter = (counter + 1) % 2
                return None, channel

    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

#this method has to handle gamestate + turn order --> respond accordingly
def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    count = 0
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")

        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        # Get all users currently in the channel first, and assign them to a team
        channel_curr_info = slack_client.api_call("channels.info",channel=gamesCID)
        members_list = construct_userlist(slack_client.api_call("users.list"))

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
                red_team += ","
                name = ""
        if len(BLUE_TEAM) > 0:
            for member in BLUE_TEAM:
                name = members_list[member]
                blue_team += name
                blue_team += ", "
                name = ""
        if len(red_team) > 0:
            red_team += " is on Red Team! "
        if len(blue_team) > 0:
            blue_team += " is on Blue Team!"
            
        slack_client.api_call(
            "chat.postMessage",
            channel=gamesCID,
            text=red_team + blue_team
        )

        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
