from datetime import datetime, timedelta, date

from discord import Embed
from canvasapi import Canvas
from discord.ext import commands

from config.configuration import CANVAS_API_KEY, CANVAS_BASE_URL, CANVAS_COURSE_NUM, DATETIME_FILE


class CanvasClient(commands.Cog):
    @staticmethod
    def write_iterable(file_path:str, iterable:list | dict) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            for item in iterable:
                file.write(str(item) + ",")
        return None

    def __init__(self, bot, api_key, base_url, course_num):
        self.bot = bot
        self.key = api_key
        self.base_url = base_url
        self.course = course_num
    
    def get_dates_range(self, how_many_days_ahead) -> list[date]:
        today = date.today()
        dates_list = [(today + timedelta(days=x)) for x in range(how_many_days_ahead)]
        return dates_list

    def read_to_datetime(self, file_path:str) -> datetime:
        with open(file_path, "r", encoding="utf-8") as file:
            result = file.read().split(",")
            result = result[0]
            result = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        return result
    
    # produces a dictionary of assignment: due date, pairs
    def getAllAssignments(self) ->dict:
        canvas = Canvas(self.base_url, self.key)
        course = canvas.get_course(CANVAS_COURSE_NUM)
        assignments = course.get_assignments()
        working_dict = {}
        for assignment in assignments:
            datetm = str(assignment.due_at)
            if str(assignment) == "Attendance (11544536)":
                continue
            else:
                working_dict[str(assignment)] = datetime.strptime(datetm, "%Y-%m-%dT%H:%M:%SZ").date()
        return working_dict


    def _get_new_assignments(self, datetime_file, num_days:int) -> list:
        assignments = self.getAllAssignments()
        # be sure to write a datetime to last_time.txt before running this function
        last_call = self.read_to_datetime(datetime_file)
        now = datetime.now().replace(microsecond=0)
        # retrieve a list of the the next (x) days (in datetime format)
        dates_range = self.get_dates_range(num_days)
        assignments_due = []
        # time diff is in %H:%M:%S format (only time, no date)

        # classify which assignments are due in the specified dates_range
        for assignment in assignments:
            if assignments[assignment] in dates_range:
                assignments_due.append(assignment)

        time_dif = now - last_call
        CanvasClient.write_iterable(datetime_file, [now])
        return assignments_due, str(time_dif)
    
    @commands.command()
    async def getNewAssignments(self, ctx, num:str):
        int_num = int(num)
        assignments, time_diff = self._get_new_assignments(DATETIME_FILE, int_num)
        pretty_string = ""
        for item in assignments:
            pretty_string += f"{item}\n"
        if len(assignments) == 0:
            pretty_string = "Yay, no new assignments in that range!"
        
        em = Embed(title="New assignments", description=pretty_string)
        em.add_field(name="Time since last checked: (hours/minutes/seconds)", value=f"{time_diff}")
        await ctx.send(embed = em)
    
async def setup(bot):
    await bot.add_cog(CanvasClient(bot, CANVAS_API_KEY, CANVAS_BASE_URL, CANVAS_COURSE_NUM))