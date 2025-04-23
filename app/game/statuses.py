import enum


class GameStatus(enum.Enum):
    wait_game = 1
    wait_player = 2
    select_player = 3
    select_theme = 4
    ask_question = 5
    check_question = 6
    end_game = 7
