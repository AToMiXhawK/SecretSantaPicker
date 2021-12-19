import argparse
import csv
import logging
import random
import smtplib
import socket
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DEFAULT_FROM = "donotreply@" + socket.getfqdn()
DEFAULT_CSV = "sample.csv"

DESCRIPTION = \
"""
Secret Santa Picker
===================

Call a command with -h for more instructions.
"""

DESCRIPTION_RUN = \
"""
Run the script (Dry Run by default, will not send out emails). 
"""

class Formatter(argparse.ArgumentDefaultsHelpFormatter,
                argparse.RawDescriptionHelpFormatter):
    pass


def ssp_main():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=Formatter,
    )

    subparsers = parser.add_subparsers()

    run = subparsers.add_parser(
        'run',
        help="Create a new account and register",
        description=DESCRIPTION_RUN,
        formatter_class=Formatter,
    )
    run.add_argument('-f', '--from', dest="email", type=str, help="From email address", default=DEFAULT_FROM)
    run.add_argument('-c', '--csv', type=str, help="Location of CSV file", default=DEFAULT_CSV)
    run.add_argument('-s', '--send', help="Send out emails", action='store_true')
    run.set_defaults(func=_run)

    parser.add_argument('-v', '--verbose', help="Print Logging Information", action='store_true')
    parser.add_argument('-l', '--logfile', help="File to write logs into", default='STDOUT/STDERR' )

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit()
    
    # Set up logging
    logger = logging.getLogger('SecretSantaPicker')

    if args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    try:
        args.func(args, logger)
    except KeyboardInterrupt:
        logger.error("")
        logger.error("Manually Interrupted.")
        sys.exit()
    except Exception as e:
        logger.error("Oops! An unhandled error occurred. Please file a bug.")
        logger.exception(e)
        sys.exit()

def _run(args, logger):

    logger.info("Running Secret Santa Picker")
    logger.info(args)

    people = get_people(args.csv, logger)
    logger.info("Got People: " + str(people))

    logger.info("Shuffling List")
    random.shuffle(people)
    logger.info("Now People: " + str(people))

    logger.info("Getting Santas!")
    for i in range(len(people)):
        logger.info("\n\n****************************************************")

        person = people[i]
        santa_of = people[i-1]
        logger.info(person['name'] + " is Secret Santa of " +  santa_of['name'])

        logger.info("Setting up email")
        send_email(args.email, person, santa_of, args.send, logger)

        logger.info("****************************************************\n\n")
    

def get_people(csvfile, logger):
    logger.info("Reading CSV file: " + csvfile)
    with open(csvfile, 'r') as csvfile:
        people = list(csv.DictReader(csvfile))
    return people


def send_email(from_email, recipient, santa_of, send, logger):

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Your Secret Santa"
    msg['From'] = "Secret Santa Picker <" + from_email + ">"
    msg['To'] = recipient['name'] + " <" + recipient['email'] + ">"

    # Create the body of the message (a plain-text and an HTML version).
    text = "Hi " + recipient['name'] + ",\nYou are Secret Santa of: " + santa_of['name'] 
    text += "\n\nWishing you a Merry Christmas and a Happy New Year!!!"
    text += "\nYour Secret Santa Picker"
    #html = \
    #"""
    #"""

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    #part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    #msg.attach(part2)

    logger.info(msg)

    if send:
        try:
            # Send the message via local SMTP server.
            logger.info("Setting up SMTP") 
            s = smtplib.SMTP('localhost')
            # sendmail function takes 3 arguments: sender's address, recipient's address
            # and message to send - here it is sent as one string.
            logger.info("Sending out mail to " + recipient['email']) 
            s.sendmail(from_email, recipient['email'], msg.as_string())

            logger.info("Closing SMTP Connection") 
            s.quit()
        except ConnectionRefusedError:
            logger.error("Your system cannot send out emails")

    else:
        logger.info("Not sending email, Send flag not enabled")

if __name__ == "__main__":
    ssp_main()