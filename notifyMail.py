#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'davinellulinvega'

import pynotify
import pyinotify
from os import environ
from pickle import Pickler
from pickle import Unpickler

EXCLUDE_DIR = ["[Gmail]", "Drafts", "Trash", "Jobs", "Queue"]


def is_excluded(path):
    """Check if the present path should be excluded"""

    # Check for folder to exclude
    exclude = False
    for folder in EXCLUDE_DIR:
        if path.find(folder) != -1:
            exclude = True
            break

    return exclude

def load_mail():
    """Load a the list of already processed mails"""
    try:
        f = open("/tmp/notified_mail.pik", "rb")
    except IOError:
        return []

    # Initialize an unpickler
    unpickler = pickle.Unpickler(f)
    # Return the list read
    return unpickler.load()

def dump_mail(new_list):
    """Save the list of already processed mails"""

    with open("/tmp/notified_mail.pik", "wb") as f:
        # Initialize a pickler object
        pickler = pickle.Pickler(f, protocol=-1)
        # Store the newly modified list
        pickler.save(new_list)


class MailEventHandler(pyinotify.ProcessEvent):
    """
    A simple handler that will send a notification upon reception of a new mail
    """

    def process_IN_CREATE(self, event):
        """
        React to the creation of a new file in the watched directory.
        :param event: The event and its properties
        :return:
        """

        # Get the file linked to the event
        file_path = event.pathname

        # Read the interesting information from the file
        subject = ""
        fro = ""
        with open(file_path, "r") as mail_file:
            line = mail_file.readline()
            while line != "":
                # Get the subject and sender
                if line.startswith("Subject"):
                    subject = line
                if line.startswith("From"):
                    fro = line
                # Read the next line
                line = mail_file.readline()

        # Load the mails that have already been processed
        notified_mails = load_mail()
        
        # Send a notification only if we have a subject or a sender
        if (subject != "" or fro != "") and (fro, subject) not in notified_mails:
            # Initialize the notify module
            if pynotify.init("Notify Mail"):

                # Declare a new notification
                n = pynotify.Notification("New message", "{}{}".format(fro, subject), "/usr/share/icons/Faenza/apps/48/mail-notification.png")
                n.set_urgency(1)

                # Show the notification
                n.show()

                # Add the notified mail to the list
                notified_mails.append((fro, subject))

                # Record the mails already notified
                dump_mail(notified_mails)

if __name__ == "__main__":

    # Instantiate a watch manager
    wm = pyinotify.WatchManager()

    # Instantiate a notifier object
    notifier = pyinotify.ThreadedNotifier(wm, MailEventHandler())

    # Add the folder to watch
    wdd = wm.add_watch("{}/.claws-mail/imapcache/".format(environ["HOME"]), pyinotify.IN_CREATE, rec=True,
                       exclude_filter=is_excluded)

    try:
        # Start the thread
        notifier.start()

    except:
        notifier.stop()
