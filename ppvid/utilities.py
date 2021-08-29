import os
import re


def get_erase_char():
    if os.name == 'posix':
        pttrn = re.compile(r'; erase = (\^.);')
        settings = os.popen('stty -a').read()
        return pttrn.findall(settings)[0]


def repair_console(erase_char = '^H'):
    if os.name == 'posix':
        os.system('stty sane')
        os.system(f'stty erase {erase_char}')


def log_info(text, console):
    "Matchering's information output will be marked with a bold prefix."
    console.log(f"[bold]INFO:[/bold] {text}")


def log_warning(text, console):
    "The warning output will be marked with a bold, red prefix and warning sign."
    console.log(f":warning: [bold red]WARNING:[/bold red] {text}")

