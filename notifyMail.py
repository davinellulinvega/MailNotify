#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'davinellulinvega'

import notify2 as pynotify
import pyinotify
from os import environ, path
from glob import glob
from pickle import Pickler, Unpickler
from email.header import decode_header

EXCLUDE_DIR = ["Sent", "Drafts", "Trash", "Jobs", "Queue"]


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

    try:
        # Initialize an unpickler
        unpickler = Unpickler(f)
        # load the list of processed mails
        proc_list = unpickler.load()
        # Return the processed the list
        return proc_list
    except EOFError:
        return []


def dump_mail(new_list):
    """Save the list of already processed mails"""

    with open("/tmp/notified_mail.pik", "wb") as f:
        # Initialize a pickler object
        pickler = Pickler(f, protocol=-1)  # A negative protocol selects the highest available version
        # Store the newly modified list
        pickler.dump(new_list)


class EventHandler(pyinotify.ProcessEvent):
    """
    A simple handler that will send a notification upon reception of a new mail
    """

    def process_IN_CREATE(self, event):
        """
        React to the creation of a new file in the watched directory.
        :param event: The event and its properties
        :return:
        """

        # Extract the file path
        file_path = event.pathname

        # Read the interesting information from the file
        subject = ""
        fro = ""
        with open(file_path, "r") as mail_file:
            for line in mail_file:
                # Get the subject and sender
                if subject == "" and line.startswith("Subject"):
                    header = decode_header(line.strip('\r\n'))
                    subject = " ".join([s for head in header for s in head if isinstance(s, str)])
                if fro == "" and line.startswith("From"):
                    header = decode_header(line.strip('\r\n'))
                    fro = " ".join([s for head in header for s in head if isinstance(s, str)])

        # Load the mails that have already been processed
        notified_mails = load_mail()

        # Send a notification only if we have a subject or a sender
        if (subject != "" or fro != "") and (fro, subject) not in notified_mails:
            # Initialize the notify module
            if pynotify.init("Notify Mail"):

                # Add the notified mail to the list
                notified_mails.append((fro, subject))

                # Record the mails already notified
                dump_mail(notified_mails)

                # Declare a new notification
                n = pynotify.Notification("New message", "{}\n{}".format(fro, subject), "/usr/share/icons/Faenza/apps/48/mail-notification.png")
                n.set_urgency(1)

                # Show the notification
                n.show()


if __name__ == "__main__":
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wdd = wm.add_watch(path.join(environ['HOME'], "Mail"), mask, rec=True)
    notifier.loop()
