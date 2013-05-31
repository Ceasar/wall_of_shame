"""
This script encourages documentation in a codebase.

This script will:

- Find undocumented public methods
- Find who wrote that method
- Email that person politely asking them to fix their code

This script is multithreaded to reduce the cost of blocking operations
over large codebases.


To test this code, a debug mail server can be run with:

    python -m smtpd -n -c DebuggingServer localhost:1025
"""
import os
import re
import subprocess
from Queue import Queue
from threading import Thread, RLock

# Delimiter used to detect whether or not a method is commented
COMMENT_END = "*/"

# Regex to extract email from git blames
EXTRACT_EMAIL_PATTERN = re.compile(r"^author-mail <(.+)>$")

OUT_FILE = "blames.csv"

_NUM_WORKER_THREADS = 4


def get_email_from_blame(blame):
    for line in blame.split("\n"):
        match = EXTRACT_EMAIL_PATTERN.match(line)
        if match:
            return match.group(1)
    raise ValueError("Could not get email")


def _raw_run(args, log_output=False):
    """Run a command and capture its output."""
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.read()


def get_blame(filename, line_number, local_path="."):
    """Get the email of the person responsible for the given line."""
    args = [
        "git",
        "blame",
        "-p",  # show porcelain
        "-l",  # show long revision
        os.path.join(local_path, filename),
        "-L",  # line number
        "%d,+1" % line_number,
    ]
    blame = _raw_run(args)
    if blame is None:
        raise ValueError("Could not execute `git blame`. Is this a git repo?")
    else:
        return blame


def gen_undocumented_public_methods(filename):
    """Find all undocumented public methods in class.

    A method is considered documented if the line preceding the definition
    is COMMENT_END.

    A method is considered public if the definition begins with 'public'.
    """
    has_comment = False
    with open(filename) as f:
        for linenum, line in enumerate(f):
            stripped = line.strip()
            if stripped == COMMENT_END:
                has_comment = True
            else:
                if not has_comment:
                    tokens = stripped.split()
                    if len(tokens) > 0 and tokens[0] == "public":
                        if "function" in tokens:
                            if not any(t.startswith("__") for t in tokens):
                                yield linenum, line
                has_comment = False


def _start_daemons(target, count):
    """Start a number of daemons on a process."""
    threads = []
    for _ in range(count):
        t = Thread(target=target)
        t.daemon = True
        t.start()
        threads.append(t)
    return threads


def main():
    """Dispatch emails asking people to document undocumented code."""

    blames = Queue()
    lines = Queue()
    filenames = Queue()

    lock = RLock()

    def fileworker():
        while True:
            filename = filenames.get()
            for line_number, _ in gen_undocumented_public_methods(filename):
                lines.put((filename, line_number))
            filenames.task_done()

    def blameworker():
        while True:
            filename, line_number = lines.get()
            blame = get_blame(filename, line_number)
            blames.put((blame, filename, line_number))
            lines.task_done()

    def mailworker():
        while True:
            blame, filename, line_number = blames.get()
            email = get_email_from_blame(blame)
            recipient, filename = email.split('@')[0], 'www' + filename[1:]
            with lock:
                with open(OUT_FILE, "a") as f:
                    f.write("%s,%s,%s\n" % (recipient, filename, line_number))
            blames.task_done()

    for path, dirs, files in os.walk('.'):
        for file in files:
            filename = os.path.join(path, file)
            if filename.endswith(".php"):
                filenames.put(filename)

    threads = _start_daemons(fileworker, _NUM_WORKER_THREADS)
    threads.extend(_start_daemons(blameworker, _NUM_WORKER_THREADS))
    threads.extend(_start_daemons(mailworker, _NUM_WORKER_THREADS))

    filenames.join()
    lines.join()
    blames.join()

if __name__ == "__main__":
    main()
