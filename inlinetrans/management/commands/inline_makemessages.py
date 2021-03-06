# coding=utf-8

import re

from django.core.management.base import CommandError, BaseCommand, NoArgsCommand
from django.core.management.commands import makemessages

class Command(makemessages.Command):
    """
    Extends Django's makemessages command and modifies its behaviour
    by overriding two regular expressions in django.utils.translation
    """
    help = ("makemessages command modified for django-inlinetrans. "
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

        old_inline_re = trans_real.inline_re
        old_block_re = trans_real.block_re

        trans_real.inline_re = re.compile(r"""^\s*(?:trans|itrans)\s+((?:"[^"]*?")|(?:'[^']*?'))(\s+.*context\s+(?:"[^"]*?")|(?:'[^']*?'))?\s*""")

        # coming soon (hopefully)
        #block_re = re.compile(r"""^\s*(?:blocktrans|iblocktrans)(\s+.*context\s+(?:"[^"]*?")|(?:'[^']*?'))?(?:\s+|$)""")
        #endblock_re = re.compile(r"""^\s*(?:endblocktrans|iendblocktrans)$""")

        super(Command, self).handle(*args, **options)

        trans_real.inline_re = old_inline_re
        trans_real.block_re = old_block_re
