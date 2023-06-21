from abc import ABC, abstractmethod
import win32serviceutil
import win32service
import win32event
import time

class PythonService(win32serviceutil.ServiceFramework, ABC):
    
    @classmethod
    def parse_command_line(cls):
        ''' Parse the command line '''
        win32serviceutil.HandleCommandLine(cls)

    # Override the method in the subclass to do something just before the service is stopped.
    @abstractmethod
    def stop(self):

        # if bot is not alive, stop service and send signal that service crashed/stopped.

        pass

    # Override the method in the subclass to do something at the service initialization.
    @abstractmethod
    def start(self):

        # I will init the bot here

        pass

    # Override the method in the subclass to perform actual service task.
    @abstractmethod
    def main(self):

         # check if the bot is still alive every 30 seconds

        pass


    def __init__(self, args):
        ''' Class constructor'''
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Create an event which we will use to wait on.
        # The "service stop" request will set this event.
        self.hWaitStop = win32event.CreateEvent(None, 0, 0,None)

    def SvcStop(self):
        '''Called when the service is asked to stop'''
        # We may need to do something just before the service is stopped.
        self.stop()
        # Before we do anything, tell the SCM we are starting the stop process.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # And set my event.
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        '''Called when the service is asked to start. The method handles the service functionality.'''
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        # We may do something at the service initialization.
        self.start()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        # Starts a worker loop waiting either for work to do or a notification to stop, pause, etc.
        self.main() 

