#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'davinellulinvega'

import notify2 as pynotify
import pyinotify
from os import environ, path
from glob import glob
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

        for ex_dir in EXCLUDE_DIR:
            if file_path.find(ex_dir) != -1:
                break
        else:
            # Read the interesting information from the file
            subject = ""
            fro = ""
            try:
                with open(file_path, "r") as mail_file:
                    for line in mail_file:
                        # Get the subject and sender
                        if not subject and line.startswith("Subject: "):
                            header = decode_header(line.strip('\r\n'))
                            subject = " ".join([head[0] for head in header])
                        if not fro and line.startswith("From: "):
                            header = decode_header(line.strip('\r\n'))
                            fro = " ".join([head[0] for head in header])
                        if subject and fro:
                            break
            except IOError:
                pass

            # Send a notification only if we have a subject or a sender
            if subject or fro:
                # Initialize the notify module
                pynotify.init("Notify Mail")

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
