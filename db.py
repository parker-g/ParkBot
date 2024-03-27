from pathlib import Path

import pandas as pd

from config.configuration import DB_OPTION


class Connection:

    def connect(self):
        pass

    def __init__(self, *args, **kwargs):
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

    def __init__(self):
        self.csv_path = Path(CSVConnection.default_csv_name)
        self.connect()

    def connect(self):
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

    def connect(self, sql_server_url, sql_server_port):
        pass

    def __init__(self, sql_server_url:str, sql_server_port:int):
        self.connect(sql_server_url, sql_server_port)




def get_connection() -> Connection:
    """Returns a Connection instance based on the `db_option` value in `bot.config`.\n\nValid values include: `csv` and `mysql`."""
    match DB_OPTION:
        case "csv":
            return CSVConnection()
        case "mysql":
            return MYSQLConnection("127.0.0.1", 3306)
        case _:
            raise ValueError("Inappropriate value for key `db_option` in `bot.config` file.")
    
    
