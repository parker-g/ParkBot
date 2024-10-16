from enum import Enum
import logging
from pathlib import Path

import pandas as pd
import mysql.connector
from mysql.connector import Error, errorcode, MySQLConnection
from mysql.connector.abstracts import MySQLConnectionAbstract

from config.configuration import DB_OPTION, WORKING_DIRECTORY, THREADS_PATH, BANK_PATH, MYSQL_HOST, MYSQL_PORT, MYSQL_PASS, MYSQL_DATABASE, MYSQL_USER

# data is stored like this:
    # user_id : str - a user's Discord user ID (18 character string)
    # guild_id : str - a Discord server's unique ID (18 character string)
    # thread_id : str - a discord text channel 

MAIN_TABLE_NAME = "users"
THREADS_TABLE_NAME = "poker_threads"

logger = logging.Logger("db_logger")
db_log_path = Path(WORKING_DIRECTORY) / "db.log"
db_log_handler = logging.FileHandler(db_log_path, encoding="utf-8", mode="w")
formatter = logging.Formatter('[%(asctime)s - %(levelname)s] - %(message)s')
logger.addHandler(db_log_handler)

class ConnectionType(Enum):
    csv = "csv file"
    sql = "SQL database"

class SQLQueryTemplates(Enum):

    CREATE_THREADS_TABLE = (f"CREATE TABLE `{THREADS_TABLE_NAME}` ("
                            "  `user_id` varchar(18),"
                            "  `guild_id` varchar(32) NOT NULL,"
                            "  `thread_id` varchar(32) NOT NULL,"
                            "  PRIMARY KEY (`user_id`, `guild_id`)"
                            ") ENGINE=InnoDB")
    
    CREATE_MAIN_TABLE = (f"CREATE TABLE `{MAIN_TABLE_NAME}` ("
                            "  `user_id` varchar(18),"
                            "  `username` varchar(32) NOT NULL,"
                            "  `gleepcoins` int(7) DEFAULT 1000,"
                            "  PRIMARY KEY (`user_id`)"
                            ") ENGINE=InnoDB")

    ADD_USER_TO_BANK = (f"INSERT INTO {MAIN_TABLE_NAME} "
                        "(user_id, username, gleepcoins) "
                        "VALUES (%(user_id)s, %(username)s, %(gleepcoins)s)")
    
    ADD_USER_TO_THREADS = (f"INSERT INTO {THREADS_TABLE_NAME} "
                            "(user_id, guild_id, thread_id) "
                            "VALUES (%(user_id)s, %(guild_id)s, %(thread_id)s)")
    
    GET_GLEEPCOINS = (f"SELECT gleepcoins FROM {MAIN_TABLE_NAME} "
                      "WHERE user_id = %s")
    
    GET_GUILD_THREADS = (f"SELECT * FROM {THREADS_TABLE_NAME} "
                    "WHERE guild_id = %s")
    GET_THREAD_ID = (f"SELECT * FROM {THREADS_TABLE_NAME} "
                     "WHERE user_id = '%s' AND guild_id = '%s'")
    
    UPDATE_USER_GLEEPCOINS = (f"UPDATE {MAIN_TABLE_NAME} "
                              "SET gleepcoins = %s "
                              "WHERE user_id = %s")
    CHECK_TABLE_EXISTS = (
        "SELECT * FROM information_schema.tables "
        # f"WHERE table_schema = {MYSQL_DATABASE} "
        # "AND table_name = %s "
        "WHERE table_name = %s "
        "LIMIT 1")
    
    GET_USER = (f"SELECT * FROM {MAIN_TABLE_NAME} "
                "WHERE user_id = %s")
    
    GET_ALL_ROWS = (f"SELECT * FROM {MAIN_TABLE_NAME}")


class DBConnection:
    """Class used to read and write persisting data."""

    def connect(self):
        pass

    def __init__(self, connection_point:str):
        """
        Subclasses of Connection must be sure to assign a value to `self.type` before .connect() is called in the constructor.

        Params:
        connection_type:str => the name of the cog or module that's attempting to make a DB connection."""
        self.conn_type:ConnectionType
        self.connection_point = connection_point
        self.connect()
        

    def create_bank_user_if_none(self, username:str, user_id:str):
        """Create a row in the bank database for a new user, if this user doesn't already exist in the database."""
        pass

    def set_user_amount(self, user_id:int, amount:int) -> None:
        """Set a given user's GleepCoins value."""
        pass

    def get_user_amount(self, user_id:int) -> int | None:
        """Returns the given user's GleepCoins value, or None if user doesn't exist."""
        pass

    def stringify_all_user_amounts(self, ctx) -> str:
        """Returns a string containing each user's name and GleepCoin count, separated by newline characters.\n\nExample formatting: `f"{username}: {user_gleepcoins} GleepCoins`.\nContext `ctx` is required to determine which guild to grab player data for."""
        pass

    def add_thread_id_if_none(self, username:str, thread_id:str, guild_id:str) -> None:
        """Add an entry to the threads database if one doesn't exist for the given username, guild_id, and thread_id."""
        pass

    def get_guild_threads(self, guild_id:str) -> dict[str, str]:
        """Retrieve a dictionary of {username : thread_id} entries for the given guild."""
        pass

    def get_user_guild_thread(self, username:str, guild_id:str) -> str:
        """Retrieve a user's thread ID for this channel, creating one if one doesn't exist."""
        pass

class CSVConnection(DBConnection):

    def __init__(self, connection_point:str):
        self.conn_type = ConnectionType.csv
        self.bank_path = Path(BANK_PATH)
        self.threads_path = Path(THREADS_PATH)
        super().__init__(connection_point)

    def connect(self):
        logger.debug(f"Connecting to {self.conn_type.value} from {self.connection_point}")
        # for this implementation we want to create the csv file if it doesn't exist
        if not self.bank_path.is_file():
            with open(self.bank_path, "w") as file:
                file.write("UserId,GleepCoins,Username\n")
        
        if not self.threads_path.is_file():
            with open(self.threads_path, "w") as file:
                file.write("player,\n")

    def create_bank_user_if_none(self, username:str, user_id:str):
        """Creates a user in the DataFrame if they don't already exist."""
        df = pd.read_csv(self.bank_path)
        users = list(df.Username)
        if username not in users:
            df.loc[len(df.index)] = [user_id, 1000, username]
        df.to_csv(self.bank_path, index=False)

    def set_user_amount(self, user_id:str, amount:int) -> None:
        df = pd.read_csv(self.bank_path)
        user_index = df.index[df['UserId'] == user_id].tolist()
        user_index = user_index[0]
        df.at[user_index, "GleepCoins"] = int(amount)
        # make sure to write new value to csv
        df.to_csv(self.bank_path, index=False)

    def get_user_amount(self, user_id) -> int | None:
        """Returns None if user doesn't exist."""
        df = pd.read_csv(self.bank_path) # we certainly created this file already, upon connect()
        user_index = df.index[df['UserId'] == user_id].tolist()
        if len(user_index) == 0:
            return None
        user_index = user_index[0]
        current_amount = df.at[user_index, "GleepCoins"]
        return int(current_amount)
    
    def stringify_all_user_amounts(self, ctx) -> str:
        df = pd.read_csv(self.bank_path)
        df_string = ""
        for index, row in df.iterrows():
            username = row["Username"]
            guild_users = [user.name.lower() for user in ctx.guild.members]
            if username.lower() in guild_users:
                df_string += f"{username}: {row['GleepCoins']} GleepCoins\n"
        return df_string
    
    def _write_player_threads(self, guilds_to_player_threads:dict[tuple, str]):
        """Using a dictionary of `(player_name, guild_id) : thread_id`, writes a .csv file containing the values."""
        guilds = []
        players = []
        # dict structure = {(playerName, guildId) : thread_id}
        for key in guilds_to_player_threads.keys():
            guild = key[1]
            player = key[0]
            if guild not in guilds:
                guilds.append(guild)
            if player not in players:
                players.append(player)

        # build header row with structure: "players, guildid1, guildid2, guildid3"
        header_row = "players"
        for guild in guilds:
            header_row = f"{header_row},{guild}"
        with open(self.threads_path, "w") as file:
            file.write(f"{header_row}\n")
            # each row represents a player
            for player in players:
                # line starts with user's name
                line = f"{player}"
                # iterate over the existin guilds headers
                for guild in guilds:
                    try:
                        thread_id:str = guilds_to_player_threads[(player, guild)]
                    except KeyError:
                        # add empty/placeholder value if player doesn't have threadID for this guild
                        thread_id = ""
                    line = f"{line},{thread_id}"
                file.write(f"{line}\n")

    def _read_player_threads(self) -> dict[tuple, str]:
        """Returns a dict with keys like so: (username:str, guild_id:str): thread_id:str"""
        guild_player_to_threads = {}
        with open(self.threads_path, "r") as file:
            # collect header row values (guild IDs)
            guilds = file.readline().strip("\n").split(",")[1:]
            # now populate dict with guildId, user_id and thead_id
            for row in file:
                # for each row (each player)
                cols = row.strip("\n").split(",")
                thread_ids = cols[1:] # thread ids is all columns for the row besides the first one (player's name)
                user_id = cols[0]
                # iterate over the thread ids and the guild names at the same time
                for i in range(len(thread_ids)):
                    # tuple structure = (user_id:str, guild_id:str)
                    guild_player_to_threads[(user_id, guilds[i])] = thread_ids[i]
        return guild_player_to_threads
            
    def add_thread_id_if_none(self, user_id: str, thread_id: str, guild_id: str):
        players_guilds_to_threads = self._read_player_threads()
        #check if player already has a thread in this guild
        try: 
            existing_thread_id = players_guilds_to_threads[(user_id, guild_id)]
            logger.warn(f"User {user_id} already has a threadId, {existing_thread_id}, for guild with Id - {guild_id}.")
            return
        except KeyError:
            players_guilds_to_threads[(user_id, guild_id)] = thread_id
        self._write_player_threads(players_guilds_to_threads)
    
    def get_guild_threads(self, guild_id: str) -> dict[str, str]:
        players_to_threads:dict[str, str] = {}
        players_guilds_to_threads:dict[tuple[str, str], str] = self._read_player_threads()
        # get each entry which contains given guild_id
        for key in players_guilds_to_threads.keys():
            if key[1] == guild_id:
                user_id = key[0]
                thread_id = players_guilds_to_threads[key]
                players_to_threads[user_id] = thread_id
        return players_to_threads
    
    def get_user_guild_thread(self, user_id: str, guild_id: str) -> str:
        guild_threads = self.get_guild_threads(guild_id)
        return guild_threads[user_id]


class MYSQLConnection(DBConnection):

    def _does_table_exist(self, connection:MySQLConnectionAbstract, table_name:str) -> bool:
        """Checks the MySQL connection for a table named `table_name` in the MySQL database specified in `bot.config`."""
        cursor = connection.cursor()
        table_exists = False
        try:   
            cursor.execute(SQLQueryTemplates.CHECK_TABLE_EXISTS.value, (table_name,))
            result = cursor.fetchall()
            if len(result) > 0: # if we have a row, the table exists
                table_exists = True
        except mysql.connector.Error as e:
            logger.error(f"Failed to check if table '{table_name}' exists in MySQL database.")
            logger.error(e)
        finally:
            cursor.close()
        return table_exists
    
    def _create_threads_table(self, connection:MySQLConnectionAbstract) -> bool:
        cursor = connection.cursor()
        success = False
        try:
            cursor.execute(SQLQueryTemplates.CREATE_THREADS_TABLE.value)
            success = True
            print(f"Created '{THREADS_TABLE_NAME}' table.")
        except mysql.connector.Error as e:
            match e.errno:
                case errorcode.ER_TABLE_EXISTS_ERROR:
                    print(f"Attempted to create table '{THREADS_TABLE_NAME}', but it was already created.")
                case _:
                    print(f"{e}")
        finally:
            cursor.close()
            connection.commit()
        return success
    
    def _create_main_table(self, connection:MySQLConnectionAbstract) -> bool:
        """Creates the table which will hold most of your discord user data. Returns True if the MySQL operation succeeded."""
        cursor = connection.cursor()
        success = False
        try:
            cursor.execute(SQLQueryTemplates.CREATE_MAIN_TABLE.value)
            success = True
            logger.info(f"Created '{MAIN_TABLE_NAME}' table.")
        except mysql.connector.Error as e:
            match e.errno:
                case errorcode.ER_TABLE_EXISTS_ERROR:
                    logger.debug(f"Attempted to create table '{MAIN_TABLE_NAME}', but it was already created.")
                case _:
                    logger.error(f"{e}")
        finally:
            cursor.close()
            connection.commit()
        return success

    def connect(self):
        logger.debug(f"Connecting to {self.connection_point} from {self.conn_type}.")
        connection = mysql.connector.connect(user = MYSQL_USER,
                                        password = MYSQL_PASS,
                                        host = MYSQL_HOST,
                                        port = MYSQL_PORT,
                                        database = MYSQL_DATABASE,
                                        )
        main_table_exists = self._does_table_exist(connection, MAIN_TABLE_NAME)
        threads_table_exists = self._does_table_exist(connection, THREADS_TABLE_NAME)
        if not main_table_exists:
            self._create_main_table(connection)
        if not threads_table_exists:
            self._create_threads_table(connection)
        return connection
    
    def _get_user_row(self, user_id:str) -> tuple | None:
        cursor = self.connection.cursor()
        user_row = None
        try:
            cursor.execute(SQLQueryTemplates.GET_USER.value, (user_id,))
            user_row = cursor.fetchone()
        except mysql.connector.Error as e:
            logger.error(f"Failed to get a user's info: {user_id}\n{e}")
        finally:
            self.connection.commit()
            cursor.close()
        return user_row
    
    def create_bank_user_if_none(self, username, user_id) -> bool:
        # check if user exists
        user_row = self._get_user_row(user_id)
        if user_row is None or len(user_row) == 0:
            # user doesn't exist
            # create user
            user_info = {"user_id": user_id,
                         "username": username,
                         "gleepcoins": 1000}
            success = self._add_new_user(user_info)
            if not success:
                logger.error(f"Error creating new row for user, {username}")
                return False
        return True

    def __init__(self, connection_point:str):
        self.connection_point = connection_point
        self.conn_type = ConnectionType.sql
        self.connection = self.connect()

    def _add_new_user(self, user_info:dict) -> bool:
        """user_info must contain all fields from the ADD_USER_TO_BANK query template.\n
        user_id: int, username:str, gleepcoins:int"""
        cursor = self.connection.cursor()
        success = False
        try:
            cursor.execute(SQLQueryTemplates.ADD_USER_TO_BANK.value, user_info)
            success = True
        except mysql.connector.Error as e:
            logger.error(f"Failed to add a user: {user_info}\n{e}")
        finally:
            self.connection.commit()
            cursor.close()
        return success
    
    def get_user_amount(self, user_id:str) -> int | None:
        """Returns user gleepcoins, or None if user doesn't exist."""
        user_row = self._get_user_row(user_id) # tuple
        if user_row is None:
            return None
        gc = user_row[2]
        return gc
    
    def set_user_amount(self, user_id:str, new_gleepcoins:int) -> bool:
        cursor = self.connection.cursor()
        success = False
        try:
            cursor.execute(SQLQueryTemplates.UPDATE_USER_GLEEPCOINS.value, (new_gleepcoins, user_id))
            success = True
        except mysql.connector.Error as e:
            logger.error(f"Failed to update user_id {user_id}'s gleepcoins: {e}")
        finally:
            self.connection.commit()
            cursor.close()
        return success
    
    def stringify_all_user_amounts(self, ctx) -> str | None:
        cursor = self.connection.cursor()
        users_string = ""
        rows:list[tuple] = []
        try:
            cursor.execute(SQLQueryTemplates.GET_ALL_ROWS.value)
            rows = cursor.fetchall()
        except mysql.connector.Error as e:
            logger.error(f"Failed to get all rows from table {MAIN_TABLE_NAME}.")
        finally:
            self.connection.commit()
            cursor.close()
        guild_users = [user.name.lower() for user in ctx.guild.members]
        for row in rows:
            username = row[1]
            gleepcoins = row[2]
            if username.lower() in guild_users: # only display members of this guild who are in the database
                users_string += f"{username}: {gleepcoins} GleepCoins\n"
        return users_string
     
    def get_guild_threads(self, connection:MySQLConnectionAbstract, guild_id:str) -> dict[str, str]:
        """Returns a dictionary of {user_id : thread_id} for each player in the database associated with the given `guild_id`."""
        cursor = connection.cursor()
        guild_threads = {} # dict of {user_id: thread_id}
        rows = []
        try:
            cursor.execute(SQLQueryTemplates.GET_GUILD_THREADS.value, (guild_id,))
            rows:list[tuple] = cursor.fetchall()
        except mysql.connector.Error as e:
            logger.error(f"Failed to retrieve rows from {THREADS_TABLE_NAME} table, in `get_guild_threads`. {e}")
            pass
        finally:
            connection.commit()
            cursor.close()
        # populate dict with retrieved data
        for row in rows:
            user_id = row[0]
            thread_id = row[2]
            guild_threads[user_id] = thread_id
        return guild_threads
    
    def add_thread_id_if_none(self, connection:MySQLConnectionAbstract, user_id:str, thread_id:str, guild_id:str) -> bool:
        """Adds a user ID to the {THREAD_TABLE_NAME} table. Return value indicates whether the key exists in the table after this function call.
        \n user_info:dict - A dictionary containing necessary info about the row to be created, {"user_id": str, "thread_id": str, "guild_id": str}"""
        cursor = connection.cursor()
        user_dict:dict = {"user_id": user_id, "thread_id": thread_id, "guild_id": guild_id}
        try:
            cursor.execute(SQLQueryTemplates.ADD_USER_TO_THREADS.value, user_dict)
        except mysql.connector.Error as e:
            match e.errno:
                case 1062:
                    logger.info(f"The key ({user_id}, {guild_id}) already exists in this table.")
                    return True
                case _:
                    logger.error(f"Failed to add row to {THREADS_TABLE_NAME}, for follwing info: {user_dict}. {e}")
                    return False
        finally:
            connection.commit()
            cursor.close()
        return True
    
    def get_user_guild_thread(self, connection:MySQLConnectionAbstract, user_id:str, guild_id:str) -> str:
        cursor = connection.cursor()
        id_row = []
        try:
            cursor.execute(SQLQueryTemplates.GET_THREAD_ID.value, (user_id, guild_id))
            id_row:list = cursor.fetchone() # [user_id, guild_id, thread_id]
        except mysql.connector.Error as e:
            logger.error(f"Failed to get thread ID for user {user_id} in guild {guild_id}.\n{e}")
        finally:
            cursor.close()
        thread_id = id_row[2]
        return thread_id


def get_db_connection(connection_point:str) -> DBConnection:
    """Returns a Connection instance based on the `db_option` value in `bot.config`.\n\nValid values include: `csv` and `mysql`."""
    match DB_OPTION:
        case "csv":
            return CSVConnection(connection_point)
        case "mysql":
            return MYSQLConnection(connection_point)
        case _:
            raise ValueError("Inappropriate value for key `db_option` in `bot.config` file.")
    
    
