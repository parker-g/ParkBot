from canvasapi import Canvas
from datetime import datetime
from config.config import CANVAS_API_KEY
# constants
BASE_URL = "https://learn.vccs.edu"
COURSE_NUM = 517689
request_file = "data/new.txt"
posted_file = "data/posted.txt"

# creating api requester obj, and requesting assignments
canvas = Canvas(BASE_URL, CANVAS_API_KEY)
course = canvas.get_course(COURSE_NUM)
assignments = course.get_assignments()


def write_list(file_path:str, iterable:list) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        for item in iterable:
            file.write(str(item) + ",")
        return None

#function to write assignments to folder for use later
def write_assignments(file_path:str | list) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        # line directly references assignments above - this is probably bad practice, but i feel like its better
        # than calling the api over again every time I want to work with the assignments
        for assignment in assignments:
            file.write(str(assignment) + ",")
    return None

#function for reading assignments to a list
def read_to_list(file_path:str) -> list:
    with open(file_path, "r", encoding="utf-8") as file:
        result = file.read().split(",")
        # delete empty item at the end of list
        result = result[:-1]
    return result

def read_to_datetime(file_path:str) -> datetime:
    with open(file_path, "r", encoding="utf-8") as file:
        result = file.read().split(",")
        result = result[0]
        result = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
    return result



def get_new_assignments(datetime_file:str) -> tuple:
    # be sure to write a datetime to last_time.txt before running this function
    last_call = read_to_datetime(datetime_file)
    now = datetime.now().replace(microsecond=0)
    # time diff is in %H:%M:%S format (only time, no date)
    time_dif = now - last_call
    write_list("data/last_time.txt", [now])

    write_assignments(request_file)
    just_requested_list = read_to_list(request_file)
    last_posted_list = read_to_list(posted_file)
    difference = []
    # if new assignments contains any new assignments, 
    # add new ones to differences list
    for assignment in just_requested_list:
        if not assignment in last_posted_list:
            difference.append(assignment)
    if len(difference) > 0:
        # if there are new assignments, write them to difference.txt
        # and write all assignments to posted_file for next comparison
        write_list("data/difference.txt", difference)
        write_assignments(posted_file)
    # if no differences between the two, clear the differences file
    elif len(difference) == 0:
        write_list("data/difference.txt", [])
    
    return difference, time_dif

# differences, time_dif = get_differences("data/last_time.txt")
# print(differences, time_dif)


    





