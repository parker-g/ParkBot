from canvasapi import Canvas
from datetime import datetime, timedelta, date
# constants
BASE_URL = "https://learn.vccs.edu"
API_TOKEN = "13096~4WZP4l07ud8nNZFSFT7cRv5F4jR08s9EJYEKmFBtZ9fXUozCmdiYPNuMSP0h9sun"
COURSE_NUM = 517689
# request_file = "new.txt"
# posted_file = "posted.txt"
datetime_file = "data/last_time.txt"

# abstracted to function so that the api can be easily used anywhere that its necessary
def grab_assignments(canvas_url:str, api_key:str, course_num:int) ->dict:
    canvas = Canvas(canvas_url, api_key)
    course = canvas.get_course(course_num)
    assignments = course.get_assignments()
    working_dict = {}
    for assignment in assignments:
        datetm = str(assignment.due_at)
        if str(assignment) == "Attendance (11544536)":
            continue
        else:
            working_dict[str(assignment)] = datetime.strptime(datetm, "%Y-%m-%dT%H:%M:%SZ").date()
    return working_dict

def get_dates_range(how_many_days_ahead) -> list[datetime]:
    today = date.today()
    dates_list = [(today + timedelta(days=x)) for x in range(how_many_days_ahead)]
    return dates_list

def write_iterable(file_path:str, iterable:list | dict) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        for item in iterable:
            file.write(str(item) + ",")
    return None

def read_to_datetime(file_path:str) -> datetime:
    with open(file_path, "r", encoding="utf-8") as file:
        result = file.read().split(",")
        result = result[0]
        result = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
    return result

# call the api every time we call this function, to ensure fresh data is always pulled
def get_differences(datetime_file, num_days:int) -> list:
    assignments = grab_assignments(BASE_URL, API_TOKEN, COURSE_NUM)
    # be sure to write a datetime to last_time.txt before running this function
    last_call = read_to_datetime(datetime_file)
    now = datetime.now().replace(microsecond=0)
    # retrieve a list of the the next (x) days (in datetime format)
    dates_range = get_dates_range(num_days)
    assignments_due = []
    # time diff is in %H:%M:%S format (only time, no date)

    # classify which assignments are due in the specified dates_range
    for assignment in assignments:
        if assignments[assignment] in dates_range:
            assignments_due.append(assignment)

    time_dif = now - last_call
    write_iterable(datetime_file, [now])
    return assignments_due, str(time_dif)

resullt = get_differences(datetime_file, 15)
print(resullt)

    





