from enum import Enum
import logging
from pathlib import Path

import pandas as pd
import mysql.connector
from mysql.connector import Error, errorcode, MySQLConnection

from config.configuration import DB_OPTION, WORKING_DIRECTORY, MYSQL_HOST, MYSQL_PORT, MYSQL_PASS, MYSQL_DATABASE, MYSQL_USER


logger = logging.Logger("db_logger")
db_log_path = Path(WORKING_DIRECTORY) / "db.log"
db_log_handler = logging.FileHandler(db_log_path, encoding="utf-8", mode="w")
formatter = logging.Formatter('[%(asctime)s - %(levelname)s] - %(message)s')
logger.addHandler(db_log_handler)

class ConnectionType(Enum):
    csv = "csv file"
    sql = "SQL database"

class QueryTemplates(Enum):
    
    CREATE_DEFAULT_TABLE = ("CREATE TABLE `users` ("
                            "  `user_id` varchar(18),"
                            "  `username` varchar(32) NOT NULL,"
                            "  `gleepcoins` int(7) DEFAULT 1000,"
                            "  `thread_id` varchar(18),"
                            "  PRIMARY KEY (`user_id`)"
                            ") ENGINE=InnoDB")

    ADD_USER = ("INSERT INTO users "
                "(user_id, username, gleepcoins, thread_id) "
                "VALUES (%(user_id)s, %(username)s, %(gleepcoins)s, %(thread_id)s)")
    
    GET_GLEEPCOINS = ("SELECT gleepcoins FROM users "
                      "WHERE user_id = %s")
    
    UPDATE_USER_GLEEPCOINS = ("UPDATE users "
                              "SET gleepcoins = %s "
                              "WHERE user_id = %s")


class Connection:

    def connect(self):
        pass

    def __init__(self, connection_point:str):
        """
        Subclasses of Connection must be sure to assign a value to `self.type` before .connect() is called in the constructor.

        Params:
        connection_type:str => the name of the cog or module that's attempting to make a DB connection."""
        self.type:ConnectionType
        self.connection_point = connection_point
        self.connect()
        

    def create_user_if_none(self, username):
        """Create a row in the database for a new user, if this user doesn't already exist in the database."""
        pass

    def set_user_amount(self, username:str, amount:int) -> None:
        """Set a given user's GleepCoins value."""
        pass

    def get_user_amount(self, username:str) -> int:
        """Returns the given user's GleepCoins value"""
        pass

    def stringify_all_user_amounts(self, ctx) -> str:
        """Returns a string containing each user's name and GleepCoin count, separated by newline characters.\n\nExample formatting: `f"{username}: {user_gleepcoins} GleepCoins`\n"""
        pass

    def get_column(self, column_name:str):
        pass

    def get_row(self, username:str):
        pass

class CSVConnection(Connection):

    default_csv_name = "data/bank.csv"

    def __init__(self, connection_point:str):
        self.type = ConnectionType.csv
        self.csv_path = Path(CSVConnection.default_csv_name)
        super().__init__(connection_point)

    def connect(self):
        print(f"Connecting to {self.type.value} from {self.connection_point}")
        # for this implementation we want to create the csv file if it doesn't exist
        if not self.csv_path.is_file():
            with open(self.csv_path, "w") as file:
                file.write("Usernames,GleepCoins\n")

    def create_user_if_none(self, username):
        """Creates a user in the DataFrame if they don't already exist."""
        df = pd.read_csv(self.csv_path)
        users = list(df.Usernames)
        if username not in users:
            df.loc[len(df.index)] = [username, 1000]

    def set_user_amount(self, username:str, amount:int) -> None:
        df = pd.read_csv(self.csv_path)
        user_index = df.index[df['Usernames'] == username].tolist()
        user_index = user_index[0]
        df.at[user_index, "GleepCoins"] = int(amount)
        # make sure to write new value to csv
        df.to_csv(self.csv_path, index=False)

    def get_user_amount(self, username) -> int:
        df = pd.read_csv(self.csv_path)
        user_index = df.index[df['Usernames'] == username].tolist()
        user_index = user_index[0]
        current_amount = df.at[user_index, "GleepCoins"]
        return int(current_amount)
    
    def stringify_all_user_amounts(self, ctx) -> str:
        df = pd.read_csv(self.csv_path)
        df_string = ""
        for index, row in df.iterrows():
            username = row["Usernames"]
            guild_users = [user.name.lower() for user in ctx.guild.members]
            if username.lower() in guild_users:
                df_string += f"{username}: {row['GleepCoins']} GleepCoins\n"
        return df_string
    
class MYSQLConnection(Connection):

    def connect(self):
        print(f"Connecting to {self.connection_point} from {self.type}.")
        connection = mysql.connector.connect(user = MYSQL_USER,
                                        password = MYSQL_PASS,
                                        host = MYSQL_HOST,
                                        port = MYSQL_PORT,
                                        database = MYSQL_DATABASE,
                                        )
        return connection

    def __init__(self, connection_point:str):
        self.connection_point = connection_point
        self.type = ConnectionType.sql
        self.connection = self.connect()


def get_connection(connection_point:str) -> Connection:
    """Returns a Connection instance based on the `db_option` value in `bot.config`.\n\nValid values include: `csv` and `mysql`."""
    match DB_OPTION:
        case "csv":
            return CSVConnection(connection_point)
        case "mysql":
            return MYSQLConnection(connection_point)
        case _:
            raise ValueError("Inappropriate value for key `db_option` in `bot.config` file.")
    
    
