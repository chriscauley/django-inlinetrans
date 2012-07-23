# Extends Django's makemessages command and modifies its behaviour
# by overriding two regular expressions in django.utils.translation

import re

from django.core.management.base import CommandError, BaseCommand, NoArgsCommand
from django.core.management.commands import makemessages

class Command(makemessages.Command):
    help = ( "makemessages command modified for django-inlinetrans. "
"Runs over the entire source tree of the current directory and "
"pulls out all strings marked for translation. It creates (or updates) a message "
"file in the conf/locale (in the django tree) or locale (for projects and "
"applications) directory.\n\nYou must run this command with one of either the "
"--locale or --all options.")

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Command doesn't accept any arguments")

        from django.utils.translation import trans_real
        import re

        trans_real.inline_re = re.compile(r"""^\s*(?:trans|itrans|inline_trans)\s+((?:".*?")|(?:'.*?'))\s*""")
        trans_real.block_re = re.compile(r"""^\s*(?:blocktrans|iblocktrans)(?:\s+|$)""")

        super(Command, self).handle(*args, **options)