import discord
import gspread

from functions import nearest_power_of_two, fill_byes, \
    new_round, find_winner, get_emojis, get_names, find_winning_cell

from discord.utils import find

# == DISCORD BOT SETUP ==

# unique identifier for the discord bot
# include a token.txt file if you want to implement this code
with open('token.txt', 'r') as f:
    TOKEN = f.readline().strip()

# the client is the bot itself
client = discord.Client()


# == GOOGLE SHEETS SETUP ==
JSON_FILE_NAME = "deerhacks-2022-11d51d5aa955.json"
SPREADSHEET_NAME = "Tournament Data"
WORKSHEET_NAME = "Sheet1"

# fill these in if you want to implement this code

sa = gspread.service_account(
    filename=JSON_FILE_NAME)  # service account
sh = sa.open(SPREADSHEET_NAME)  # spreadsheet
wks = sh.worksheet(WORKSHEET_NAME)  # worksheet

# == GLOBAL VARIABLES ==

participant_names = []  # the tags of the participants
participant_tags = []  # the participants in a tournament
not_full = False  # checks whether the tournament is full
num_games = 1  # the number of games in the tournament
command_dict = {}  # to create new commands, in the format of
# (!command, response)
default_commands = ['help', 'tournament', 'me', 'start', 'newcommand',
                    'winner', 'clear', 'hello', 'removecommand']
embed_fields = []
temp_bool, tournament_over = False, False
lst1 = []  # participants[:]
lst2 = []
rps_started = False
rps_players = []
rps_dict = {}
rps_channel = ""
help_embed = discord.Embed(
    title='Bracket Bot Commands',
    description='This is a bot used for making ' +
    'tournament brackets along with a few other things!',
    color=discord.Colour(880808))

# == HELP EMBED ==

help_embed.add_field(
    name='!tournament', value='This starts a tournament queue that people can '
    + 'join with the !me command',
    inline=False)
help_embed.add_field(
    name='!me', value='This adds the person to the queue ' +
    ' (assuming one is open)', inline=False)
help_embed.add_field(name='!start',
                     value='This ends the queue for the tournament, ' +
                           'finalizing and sending the bracket link', inline=False)
help_embed.add_field(name='!clear', value='This clears the ' +
                                          'excel sheet for the tournament', inline=False)
help_embed.add_field(name='!newcommand', value='Add a new' +
'command, proper format is: !newcommand!*command word*!*phrase*', inline=False)
help_embed.add_field(name='!rps', value='Play a game of rock, ' +
'paper, and scissors, Dm your choice to the bot', inline=False)
help_embed.add_field(name='!removecommand', value='Remove a command')
# == EVENTS ==


# this event runs when the bot comes online
@client.event
async def on_ready():
    print(f'logged in as user:{client.user}')


# this event runs when anyone on the server types a message
@client.event
async def on_message(message):
    global not_full, lst1, lst2, help_embed, rps_started, rps_players, \
        rps_dict, rps_channel, tournament_over, temp_bool, num_games, \
        participant_tags, participant_names

    user_message = str(message.content)  # the message sent by the user

    # HELP COMMAND

    if user_message.lower() == '!help':
        await message.channel.send(embed=help_embed)

    # TO ADD CUSTOM COMMANDS TO THE BOT

    elif len(user_message) > 12 and user_message.lower()[:12] == '!newcommand!':

        command_str = user_message[1:].split('!')

        if len(command_str) > 2 and command_str[1] not in default_commands:
            new_message = '!'.join(command_str[2:])
            command_dict['!' + command_str[1].strip()] = new_message
            help_embed.add_field(name='!' + command_str[1].strip(),
                                 value='Responds with: '
                                       + new_message, inline=False)
            embed_fields.append('!' + command_str[1].strip())
            await message.channel.send(
                f'New command - !{command_str[1].strip()}' +
                 f' has been set to: {new_message}')

        elif command_str[1] in default_commands:
            await message.channel.send(
                'That command is a default command and cannot be modified')

        else:
            await message.channel.send(
                'Proper format is !newcommand!*command*!*phrase*')

    # RESPONDS TO CUSTOM COMMANDS

    elif user_message in command_dict:
        await message.channel.send(command_dict[user_message])


    elif len(user_message) > 15 and user_message[:15].lower() == '!removecommand!':

        command_str = user_message[1:].split('!')
        removed = '!' + command_str[1]

        if len(command_str) == 2:
            if removed in default_commands:
                await message.channel.send('That command is a default command'
                                           + ' and cannot be changed')
            elif removed in command_dict:
                command_dict.pop(removed)
                await message.channel.send('Command ' + removed + ' has'
                                           + ' been removed')
                help_embed.remove_field(embed_fields.index(removed) + 7)
            else:
                await message.channel.send('There is no command ' +
                                           removed)


    # RESPONDS HELLO

    elif user_message.lower() == '!hello':
        await message.channel.send(
            "Hello " + str(message.author).split("#")[0] + " :wave:")

    # STARTS AN RPS GAME
    elif user_message.lower() == '!rps':
        rps_started = True
        rps_channel = message.channel
        await message.channel.send(
            "Who is playing " + " :question: " + " DM me to join!")

    # RECORDS IF SOMEONE MAKES A RPS RESPONSE
    if isinstance(message.channel, discord.channel.DMChannel) and \
            message.author != client.user and rps_started:

        # if game is full
        if len(rps_dict) == 1 and message.content in \
                ["rock", "paper", "scissors"] and \
                message.author not in rps_players:
            rps_started = False
            rps_players.append(message.author)
            rps_dict[message.author] = message.content
            lst = get_emojis(rps_dict)
            other_lst = get_names(rps_dict)
            winner = find_winner(rps_players, rps_dict)
            if winner is None:
                await rps_channel.send(str(other_lst[0]) + lst[0] +
                                       ":crossed_swords:" + lst[1] +
                                       str(other_lst[1]))
                await rps_channel.send("There was a tie!")

            elif winner == rps_players[0]:
                await rps_channel.send(
                    str(other_lst[0]) + " " + lst[0] + " :crossed_swords: "
                    + lst[1] + " " + str(other_lst[1]))
                without_tag = str(rps_players[0]).split("#")[0]
                await rps_channel.send(without_tag + " is the winner!")

            else:
                await rps_channel.send(
                    str(other_lst[0]) + lst[0] + " :crossed_swords: "
                    + lst[1] + str(other_lst[1]))
                without_tag = str(rps_players[1]).split("#")[0]
                await rps_channel.send(without_tag + " is the winner!")

            # rest variables
            rps_players = []
            rps_dict = {}

        # if game is not full
        else:
            if message.content in ["rock", "paper", "scissors"]:
                if message.author not in rps_dict:
                    rps_dict[message.author] = message.content
                else:
                    rps_dict.update({message.author: message.content})

                if message.author not in rps_players:
                    rps_players.append(message.author)
                await message.channel.send('Your response has been saved')
            else:
                await message.channel.send('Invalid input, try again')

    # CLEARS THE SHEET AND RESETS PARTICIPANTS
    elif user_message.lower() == '!clear':
        wks.clear()
        wks.format('A:Z', {'textFormat': {'bold': False}})
        wks.format('A:Z',
                   {"backgroundColor": {"red": 1, "green": 1, "blue": 1}})
        participant_names = []
        participant_tags = []
        tournament_over = False
        await message.channel.send(
            "The sheet has been cleared and the participants have been reset")

    # ALLOWS PLAYERS TO BE ADDED TO THE TOURNAMENT

    elif user_message.lower() == '!tournament':
        not_full = True
        await message.channel.send(
            "Who is playing " + " :question: " + " Respond with !me to join!")

    # ADDS THE PLAYER TO THE PARTICIPANTS LIST

    elif not_full and user_message.lower() == '!me':
        if message.author.mention not in participant_tags:
            participant_tags.append(message.author.mention)
            participant_names.append(str(message.author).split('#')[0])
            emoji = '\N{THUMBS UP SIGN}'
            await message.add_reaction(emoji)  # react to the user's message
        else:
            emoji = "\N{Neutral Face}"
            await message.add_reaction(emoji)

    # ---------------------------------------------------
    # STOPS PLAYERS FROM BEING ABLE TO JOIN THE TOURNAMENT
    # ---------------------------------------------------

    elif not_full and user_message.lower() == '!start':
        not_full = False  # stop adding participants
        fill_byes(participant_tags)  # include byes if necessary
        fill_byes(participant_names)

        # create round headings

        num_people = len(participant_names)
        num_games = nearest_power_of_two(num_people)


        for i in range(num_games):
            col = chr(65 + i)
            wks.update(col + "1", "Round " + str(i+1))
            wks.format(col + "1", {'textFormat': {'bold': True}})
            wks.format(
                col + "1", {"backgroundColor":
                            {"red": 1, "green": 163/255, "blue": 59/255}})

        # display the teams in round 1 (first column of sheets)

        for i in range(num_people):
            if i % 2 == 0:
                row = str(2 * i + 3)
            else:
                row = str(2 * i + 2)
            # wks.update("A" + row, participants[i].split("#")[0])
            wks.update("A" + row, participant_names[i])

        # once the first column and the round/winner headings are created,
        # the tournament starts
        await message.channel.send(
            "Tournament is ready. You can view live updates of " +
            "the tournament here: https://docs.google.com/spreadsheets" +
            "/d/1kaAp0XADWR0JXQlqxeb95ucmYKx4a9dD97_vuvO_o-w/edit#gid=0 " +
            "You can save the tournament bracket at any point by going to " +
            "File -> Download -> PDF")

        lst1_names = participant_names[:]  # creates a copy of the participants
        lst2_names = []
        lst1_tags = participant_tags[:]
        lst2_tags = []
        num_rounds = 2

        # keep playing games as long as there are players in \
        # both lists and the tournament is not over

        winner_position = 0
        print('new tournament')
        while (len(lst1_tags) > 0 or len(lst2_tags) > 0) \
                and not tournament_over:
            print("major while loop ran", lst1_tags, lst2_tags, tournament_over)
            print(lst1_names, lst2_names)
            # as long as the first list is not empty
            while len(lst1_tags) > 0:
                print("first sub while loop ran", lst1_tags, lst2_tags, tournament_over)
                print(lst1_names, lst2_names)
                # winner has been determined
                if len(lst1_tags) == 1:
                    tournament_over = True  # end the tournament
                    await message.channel.send("*The tournament has ended*")
                    break

                # winner has not been determined bc \
                # it would have broken the loop

                check = True  # used to determine if there are byes playing
                winner = ""

                player1 = lst1_tags[0]
                player2 = lst1_tags[1]

                # CHECKING FOR BYES

                if player1 == "bye":
                    winner = player2
                    winner_position = 1
                    check = False

                elif player2 == "bye":
                    winner = player1
                    winner_position = 0
                    check = False

                # NO BYES

                else:
                    await message.channel.send(
                        "Enter the game winner as: !winner ...")
                    await message.channel.send(
                        f"The game is {player1} vs {player2}")

                while check:  # check is used so it keeps asking for a player
                    # until a correct !winner command is entered

                    msg = await client.wait_for("message")

                    # checks if player has entered !winner command

                    if msg.content.lower()[0:7] == "!winner":

                        # valid message for player 1
                        if player1 in msg.content[7:]:
                            winner = player1
                            winner_position = 0
                            check = False

                        # valid message for player 2
                        elif player2 in msg.content[7:]:
                            winner = player2
                            winner_position = 1
                            check = False

                        # invalid message
                        else:
                            await message.channel.send(
                                "Invalid player, try again")

                # remove the players from the initial list
                # and add winners to the other list

                lst2_tags.append(winner)
                lst2_names.append(lst1_names[winner_position])

                lst1_tags.pop(0)
                lst1_tags.pop(0)

                lst1_names.pop(0)
                lst1_names.pop(0)

                # announce the winner
                await message.channel.send(f"The game winner is {winner}")

            new_round(
                num_rounds, lst2_names, wks)  # update the sheet for this round
            num_rounds += 1  # increment the number of rounds by 1

            # color the winners. They are the items of lst2_names.
            for player in lst2_names:
                cell_lst = wks.findall(player)
                cell = find_winning_cell(cell_lst, num_rounds)
                if cell is not None:
                    cell_str = chr(64 + cell.col) + str(cell.row)
                    wks.format(cell_str, {'textFormat': {'bold': True}})
                    wks.format(cell_str, {
                        "backgroundColor": {"red": 50 / 255, "green": 168 / 255,
                                            "blue": 82 / 255}})

            while len(lst2_tags) > 0:
                print("second sub while loop ran", lst1_tags, lst2_tags, tournament_over)
                print(lst1_names, lst2_names)
                if len(lst2_tags) == 1:
                    tournament_over = True
                    await message.channel.send("*The tournament has ended*")
                    break
                player1 = lst2_tags[0]
                player2 = lst2_tags[1]
                check = True
                winner = ""
                if player1 == "bye":
                    winner = player2
                    winner_position = 1
                    check = False
                elif player2 == "bye":
                    winner = player1
                    winner_position = 0
                    check = False
                await message.channel.send(
                    f"The game is {player1} vs {player2}")
                if not (player1 == "bye" or player2 == "bye"):
                    await message.channel.send(
                        "Enter the game winner as: !winner ...")

                while check:
                    msg = await client.wait_for("message")
                    if msg.content.lower()[0:7] == "!winner":
                        if player1 in msg.content[7:]:
                            winner = player1
                            winner_position = 0
                            check = False
                        elif player2 in msg.content[7:]:
                            winner = player2
                            winner_position = 1
                            check = False
                        else:
                            await message.channel.send(
                                "Invalid player, try again")

                lst1_tags.append(winner)
                lst1_names.append(lst2_names[winner_position])

                lst2_tags.pop(0)
                lst2_tags.pop(0)

                lst2_names.pop(0)
                lst2_names.pop(0)
                await message.channel.send(f"The game winner is {winner}")

            new_round(
                num_rounds, lst1_names, wks)  # update the sheet for this round
            num_rounds += 1  # increment the number of rounds by 1

            # color the winners. They are the items of lst1_names.
            for player in lst1_names:
                cell_lst = wks.findall(player)
                cell = find_winning_cell(cell_lst, num_rounds)
                if cell is not None:
                    cell_str = chr(64 + cell.col) + str(cell.row)
                    wks.format(cell_str, {'textFormat': {'bold': True}})
                    wks.format(cell_str, {
                        "backgroundColor": {"red": 50 / 255, "green": 168 / 255,
                                            "blue": 82 / 255}})

        if len(lst1_names) == 0:
            await message.channel.send(
                "**The champion is: **" + lst2_tags[0] + ":fire:")
        else:
            await message.channel.send(
                "**The champion is: **" + lst1_tags[0] + ":fire:")


# == MAIN FILE OUTPUT ==

if __name__ == "__main__":
    # make the bot run
    client.run(TOKEN)
