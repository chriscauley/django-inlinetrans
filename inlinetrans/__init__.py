# coding=utf-8
VERSION = (0, 4, 0)


def get_version(svn=False):
    """
    Returns the version as a human-format string."
    """
    version = '.'.join([str(i) for i in VERSION])

    if svn:
        from django.utils.version import get_svn_revision
        import os

        svn_rev = get_svn_revision(os.path.dirname(__file__))

        if svn_rev:
            version = '%s-%s' % (version, svn_rev)

    return version
