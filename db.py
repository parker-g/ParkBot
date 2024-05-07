from enum import Enum
import logging
from pathlib import Path

import pandas as pd
import mysql.connector
from mysql.connector import Error, errorcode, MySQLConnection
from mysql.connector.abstracts import MySQLConnectionAbstract

from config.configuration import DB_OPTION, WORKING_DIRECTORY, MYSQL_HOST, MYSQL_PORT, MYSQL_PASS, MYSQL_DATABASE, MYSQL_USER

MAIN_TABLE_NAME = "users"

logger = logging.Logger("db_logger")
db_log_path = Path(WORKING_DIRECTORY) / "db.log"
db_log_handler = logging.FileHandler(db_log_path, encoding="utf-8", mode="w")
formatter = logging.Formatter('[%(asctime)s - %(levelname)s] - %(message)s')
logger.addHandler(db_log_handler)

class ConnectionType(Enum):
    csv = "csv file"
    sql = "SQL database"

class SQLQueryTemplates(Enum):
    
    CREATE_MAIN_TABLE = (f"CREATE TABLE `{MAIN_TABLE_NAME}` ("
                            "  `user_id` varchar(18),"
                            "  `username` varchar(32) NOT NULL,"
                            "  `gleepcoins` int(7) DEFAULT 1000,"
                            "  PRIMARY KEY (`user_id`)"
                            ") ENGINE=InnoDB")

    ADD_USER = (f"INSERT INTO {MAIN_TABLE_NAME} "
                "(user_id, username, gleepcoins) "
                "VALUES (%(user_id)s, %(username)s, %(gleepcoins)s)")
    
    GET_GLEEPCOINS = (f"SELECT gleepcoins FROM {MAIN_TABLE_NAME} "
                      "WHERE user_id = %s")
    
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


class Connection:

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
        

    def create_user_if_none(self, username:str, user_id:str):
        """Create a row in the database for a new user, if this user doesn't already exist in the database."""
        pass

    def set_user_amount(self, user_id:int, amount:int) -> None:
        """Set a given user's GleepCoins value."""
        pass

    def get_user_amount(self, user_id:int) -> int | None:
        """Returns the given user's GleepCoins value, or None if user doesn't exist."""
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
        self.conn_type = ConnectionType.csv
        self.csv_path = Path(CSVConnection.default_csv_name)
        super().__init__(connection_point)

    def connect(self):
        print(f"Connecting to {self.conn_type.value} from {self.connection_point}")
        # for this implementation we want to create the csv file if it doesn't exist
        if not self.csv_path.is_file():
            with open(self.csv_path, "w") as file:
                file.write("UserId,GleepCoins,Username\n")

    def create_user_if_none(self, username:str, user_id:str):
        """Creates a user in the DataFrame if they don't already exist."""
        df = pd.read_csv(self.csv_path)
        users = list(df.Username)
        if username not in users:
            df.loc[len(df.index)] = [user_id, 1000, username]
        df.to_csv(self.csv_path, index=False)

    def set_user_amount(self, user_id:str, amount:int) -> None:
        df = pd.read_csv(self.csv_path)
        user_index = df.index[df['UserId'] == user_id].tolist()
        user_index = user_index[0]
        df.at[user_index, "GleepCoins"] = int(amount)
        # make sure to write new value to csv
        df.to_csv(self.csv_path, index=False)

    def get_user_amount(self, user_id) -> int | None:
        """Returns None if user doesn't exist."""
        df = pd.read_csv(self.csv_path) # we certainly created this file already, upon connect()
        user_index = df.index[df['UserId'] == user_id].tolist()
        if len(user_index) == 0:
            return None
        user_index = user_index[0]
        current_amount = df.at[user_index, "GleepCoins"]
        return int(current_amount)
    
    def stringify_all_user_amounts(self, ctx) -> str:
        df = pd.read_csv(self.csv_path)
        df_string = ""
        for index, row in df.iterrows():
            username = row["Username"]
            guild_users = [user.name.lower() for user in ctx.guild.members]
            if username.lower() in guild_users:
                df_string += f"{username}: {row['GleepCoins']} GleepCoins\n"
        return df_string
    
class MYSQLConnection(Connection):

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
            print(f"Failed to check if table '{table_name}' exists in MySQL database.")
            print(e)
        finally:
            cursor.close()
        return table_exists
    
    def _create_main_table(self, connection:MySQLConnectionAbstract) -> bool:
        """Creates the table which will hold most of your discord user data. Returns True if the MySQL operation succeeded."""
        cursor = connection.cursor()
        success = False
        try:
            cursor.execute(SQLQueryTemplates.CREATE_MAIN_TABLE.value)
            success = True
            print(f"Created '{MAIN_TABLE_NAME}' table.")
        except mysql.connector.Error as e:
            match e.errno:
                case errorcode.ER_TABLE_EXISTS_ERROR:
                    print(f"Attempted to create table '{MAIN_TABLE_NAME}', but it was already created.")
                case _:
                    print(f"{e}")
        finally:
            cursor.close()
            connection.commit()
        return success

    def connect(self):
        #NOTE upon connection, we should check if the users table already exists, trying to create it if it doesnt
        print(f"Connecting to {self.connection_point} from {self.conn_type}.")
        connection = mysql.connector.connect(user = MYSQL_USER,
                                        password = MYSQL_PASS,
                                        host = MYSQL_HOST,
                                        port = MYSQL_PORT,
                                        database = MYSQL_DATABASE,
                                        )
        main_table_exists = self._does_table_exist(connection, MAIN_TABLE_NAME)
        if not main_table_exists:
            self._create_main_table(connection)
        return connection
    
    def _get_user_row(self, user_id:str) -> tuple | None:
        cursor = self.connection.cursor()
        user_row = None
        try:
            cursor.execute(SQLQueryTemplates.GET_USER.value, (user_id,))
            user_row = cursor.fetchone()
            print(user_row)
        except mysql.connector.Error as e:
            print(f"Failed to get a user's info: {user_id}\n{e}")
        finally:
            self.connection.commit()
            cursor.close()
        return user_row
    
    def create_user_if_none(self, username, user_id) -> bool:
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
                print(f"Error creating new row for user, {username}")
                return False
        return True

    def __init__(self, connection_point:str):
        self.connection_point = connection_point
        self.conn_type = ConnectionType.sql
        self.connection = self.connect()

    def _add_new_user(self, user_info:dict) -> bool:
        """user_info must contain all fields from the ADD_USER query template.\n
        user_id: int, username:str, gleepcoins:int"""
        cursor = self.connection.cursor()
        success = False
        try:
            cursor.execute(SQLQueryTemplates.ADD_USER.value, user_info)
            success = True
        except mysql.connector.Error as e:
            print(f"Failed to add a user: {user_info}\n{e}")
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
            print(f"Failed to update user_id {user_id}'s gleepcoins: {e}")
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
            print(f"Failed to get all rows from table {MAIN_TABLE_NAME}.")
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
        

def get_connection(connection_point:str) -> Connection:
    """Returns a Connection instance based on the `db_option` value in `bot.config`.\n\nValid values include: `csv` and `mysql`."""
    match DB_OPTION:
        case "csv":
            return CSVConnection(connection_point)
        case "mysql":
            return MYSQLConnection(connection_point)
        case _:
            raise ValueError("Inappropriate value for key `db_option` in `bot.config` file.")
    
    
