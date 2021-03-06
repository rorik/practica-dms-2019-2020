from lib.data.model.shared.abstract_gamemaster import AbstractGameMaster
from lib.data.model.shared.abstract_factory import AbstractFactory
from lib.data.model.go.go_factory import GoFactory
from lib.data.model.tictactoe.tictactoe_factory import TicTacToeFactory
from lib.data.auth.restclient import RestClient
from threading import Semaphore, Timer
from flask import Request
from os import getenv


class RestApi():
    """ REST API facade.
    ---
    This class is a facade with the operations provided through the REST API.
    """
    __gm: AbstractGameMaster = None
    __factory: AbstractFactory = None
    __lock = Semaphore()
    __restarting: Timer = None

    def __init__(self):
        self.__gm_type = getenv('GAME_SERVER_GAME', 'tictactoe').lower()
        size = getenv('GAME_SERVER_BOARD_SIZE')
        if self.__gm_type == 'tictactoe':
            self.__factory = TicTacToeFactory()
        elif self.__gm_type == 'go':
            self.__factory = GoFactory()
        else:
            raise NameError(f'The value of GAME_SERVER_GAME is invalid ({self.__gm_type})' +
                            ', available options: [tictactoe, go]')

        self.__factory.board_size = size
        self.__gm = self.__factory.build()

        if self.__gm is None:
            raise AssertionError('gamemaster cannot be None')

    def status(self, request: Request):
        """ Status handler.
        ---
        Always returns a tuple with the 200 status code and an "OK" message.
        """
        return (200, f'OK\t{self.__gm_type}')

    def join(self, request: Request):
        """ Game join handler.
        ---
        Join the game and get a client_id.
        """
        token = self.__get_parameter(request, 'token')
        if token is None:
            return (401, 'Unauthorized')

        self.__lock.acquire()
        user_info = RestClient.instance().user_info(token)
        self.__lock.release()

        if user_info is None:
            return (401, 'Unauthorized')

        client_id = self.__gm.join(user_info.get('username'))
        if client_id is None:
            return (404, 'The game is full, cannot add more users')
        return (200, client_id)

    def place(self, request: Request):
        """ Place handler.
        ---
        Place a piece in a cell.
        """
        client_id = self.__get_parameter(request, 'clientId')

        x = self.__get_parameter(request, 'x')
        y = self.__get_parameter(request, 'y')

        try:
            x = int(x)
            y = int(y)
        except (ValueError, TypeError) as ex:
            return (404, 'The x and y parameters must be defined and be a valid positive integer')

        result = self.__gm.place(client_id, x, y)

        if result[0] is None:
            if result[1] == 0:
                return (401, 'Unauthorized')
            elif result[1] == 1:
                return (403, 'The game hasn\'t started yet')
            elif result[1] == 2:
                return (403, 'It\'s not the player\'s turn')
            elif result[1] == 3:
                return (404, 'The given coordinate does not exist')
            else:
                return (500, 'Unexpected game server error')

        if result[1] and self.__restarting is None:
            self.__restarting = Timer(10, self.__restart)
            self.__restarting.start()

        return (200, result[0])

    def play_status(self, request: Request, brief: bool):
        """ Status handler.
        ---
        Return current state of the game.
        """
        client_id = self.__get_parameter(request, 'clientId')

        status = self.__gm.status(client_id, brief)
        return (200, status)

    @staticmethod
    def __get_parameter(request: Request, parameter: str):
        client_id = request.values.get(parameter)
        if client_id is None:
            if request.json is not None and parameter in request.json:
                client_id = request.json[parameter]
        return client_id

    def __restart(self):
        self.__restarting = None
        self.__gm = self.__factory.build()
        print(' - - [GAME RESTARTED] - -')
