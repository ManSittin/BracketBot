from math import log, ceil
from typing import Optional
import gspread


def fill_byes(people: list) -> None:
    """
    mutate the list to have the nearest power of 2 people,
    with evenly spaced byes
    """
    num_byes = 2 ** nearest_power_of_two(len(people)) - len(people)
    for i in range(num_byes):
        people.insert(-1 - 2 * i, 'bye')


def nearest_power_of_two(n: int) -> int:
    """
    return the power of 2 nearest to <n>
    precondition: n > 0
    >>> nearest_power_of_two(8)
    3
    >>> nearest_power_of_two(9)
    4
    """
    if n <= 0:
        raise ValueError
    elif n == 1:
        return 1
    return ceil(log(n, 2))


def new_round(rounds: int, lst: list, worksheet: gspread.Worksheet) -> None:
    """
    commence a new round of the tournament
    """
    curr_col = chr(64 + rounds)
    increment = 2 ** (rounds + 1)
    starting_row = 2 ** rounds + 1
    if not len(lst) == 1:
        for i in range(len(lst)):
            if i % 2 == 0:
                row = str(starting_row + (i // 2) * increment)
            else:
                row = str(starting_row + ((i - 1) // 2) * increment + 1)
            # worksheet.update(curr_col + row, lst[i].split("#")[0])
            worksheet.update(curr_col + row, lst[i])


def find_winner(player_lst: list, player_dic: dict) -> Optional[str]:
    """given a dictionary of rps responses,
    return the winner or None if there is a tie"""
    player1 = player_lst[0]
    player2 = player_lst[1]
    p1_response = player_dic[player1]
    p2_response = player_dic[player2]

    if p1_response == p2_response:
        return None

    elif p1_response == "rock":
        if p2_response == "scissors":
            return player1
        else:
            return player2

    elif p1_response == "paper":
        if p2_response == "scissors":
            return player2
        else:
            return player1

    else:
        if p2_response == "rock":
            return player2
        else:
            return player1


def get_emojis(dic: dict) -> list[str]:
    """
    convert a dictionary of rps responses
    to a list of strings of emojis
    """
    lst = []
    for elem in dic:
        if dic[elem] == "paper":
            lst.append(":newspaper:")
        else:
            lst.append(":"+dic[elem]+":")
    return lst


def get_names(dic: dict) -> list[str]:
    """
    convert a dictionary of rps responses
    to a list of strings of users
    """
    lst = []
    for elem in dic:
        lst.append(str(elem).split("#")[0])
    return lst


def find_winning_cell(cell_lst: list, num_rounds: int) -> Optional[gspread.Cell]:
    """
    given a list of cells, find the one which represents a won match
    """
    for cell in cell_lst:
        if cell.col == num_rounds - 2:
            return cell
    return None
