import os
import datetime

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.core.management import call_command
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.utils.encoding import smart_str
from django.utils.translation import get_language, ugettext as _
from django.views.decorators.http import require_POST
import inlinetrans

from inlinetrans.polib import pofile
from inlinetrans.utils import validate_format, find_pos
from inlinetrans import settings as app_settings

def find_po(lang, msgid, include_djangos=False):
    pos = find_pos(lang, include_djangos=include_djangos)
    entries = [(None, None, None)]
    if pos:
        for file_po in pos:
            candidate = pofile(file_po)
            poentry = candidate.find(msgid)
            if poentry:
                entries.append((file_po, candidate, poentry))
                if candidate:
                    break

    return entries[-1]

def set_new_translation(request):
    """
    Post to include a new translation for a msgid
    """

    internal_ip = request.META['REMOTE_ADDR'] in settings.INTERNAL_IPS
    anon = request.user.is_anonymous()
    is_staff = request.user.is_staff

    if not (is_staff or (internal_ip and anon)):
        return HttpResponseForbidden(_('You have no permission to update translation catalogs'))

    if not request.POST:
        return HttpResponseBadRequest(render_to_response('inlinetrans/response.html',
                                      {'message': _('Invalid request method')},
                                      context_instance=RequestContext(request)))
    else:
        result = {'errors': True,
                  'question': False,
                  'message': _('Unknow error'),
                 }
        selected_pofile = None
        msgid = smart_str(request.POST['msgid'])
        msgstr = smart_str(request.POST['msgstr'])
        retry = smart_str(request.POST['retry'])
        lang = get_language()

        # We try to update the catalog
        if retry != 'false':
            root_path = os.path.dirname(os.path.normpath(os.sys.modules[settings.SETTINGS_MODULE].__file__))
            locale_path = os.path.dirname(os.path.normpath(os.sys.modules[settings.SETTINGS_MODULE].__file__))
            call_command('inline_makemessages', locale=lang, extensions=['.html'], root_path=root_path, locale_path=locale_path)
#            make_messages(lang, extensions=['.html'], root_path=root_path, locale_path=locale_path)

        file_po, selected_pofile, poentry = find_po(lang, msgid,
            include_djangos=True)

        if poentry:
            poentry.msgstr = msgstr
            if 'fuzzy' in poentry.flags:
                poentry.flags.remove('fuzzy')
            po_filename = file_po

        # We can not find the msgid in any of the catalogs
        elif not selected_pofile:
            result['message'] = _('"%(msgid)s" not found in any catalog' % {'msgid': msgid})
            if retry == 'false':
                result['question'] = _('Do you want to update the catalog (this could take longer) and try again?')
            return HttpResponse(simplejson.dumps(result), mimetype='text/plain')

        format_errors = validate_format(selected_pofile)
        if format_errors:
            result['message'] = format_errors
            return HttpResponse(simplejson.dumps(result), mimetype='text/plain')

        if poentry and not format_errors:
            try:
                selected_pofile.metadata['Last-Translator'] = smart_str("%s %s <%s>" % (request.user.first_name, request.user.last_name, request.user.email))
                selected_pofile.metadata['X-Translated-Using'] = smart_str("inlinetrans %s" % inlinetrans.get_version(False))
                selected_pofile.metadata['PO-Revision-Date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M%z')
            except UnicodeDecodeError:
                pass
            selected_pofile.save()
            selected_pofile.save_as_mofile(po_filename.replace('.po', '.mo'))
            result['errors'] = False
            result['message'] = _('Catalog updated successfully')
        elif not poentry:
            result['message'] = _('PO entry not found')
    return HttpResponse(simplejson.dumps(result), mimetype='text/plain')


@require_POST
@staff_member_required
def do_restart(request):
    """
    Does a reload using one of following methods
    * "runserver"
    * "mod_wsgi"
    * "gunicorn"
    * "command"
    """
    reload_method = app_settings.RELOAD_METHOD
    reload_log = app_settings.RELOAD_LOG
    reload_time = app_settings.RELOAD_TIME
    
    if reload_method == 'runserver':
        settings_module = request.environ.get('DJANGO_SETTINGS_MODULE')
        filename = __import__(settings_module, {}, {}, [], 0).__file__
        if filename.endswith('.pyc'):
            filename = filename.replace('.pyc', '.py')
        os.utime(filename, None)

    # TODO: Test mod_wsgi
    elif reload_method == 'mod_wsgi':
        if int(request.environ.get('mod_wsgi.script_reloading', '0')) and \
                request.environ.has_key('mod_wsgi.process_group') and \
                request.environ.get('mod_wsgi.process_group',None) and \
                request.environ.has_key('SCRIPT_FILENAME'):
            try:
                os.utime(request.environ.get('SCRIPT_FILENAME'), None)
            except:
                return HttpResponse("The call to os.utime failed", status=500)
        else:
            return HttpResponse("mod_wsgi reload mode is used, but mod_wsgi \
                is not configured correctly", status=500)

    # TODO: test gunicorn
    elif reload_method == 'gunicorn':
        try:
            os.kill(os.getppid(), 1)
        except Exception as e:
            return HttpResponse("Gunicorn reload failed with: %s" % e, status=500)

    elif reload_method == 'command' and app_settings.RELOAD_COMMAND:
        if not (os.path.exists(os.path.dirname(reload_log))):
            return HttpResponse("The INLINETRANS_RELOAD_LOG directory does not exist", status=500)
        os.system("sleep 2 && %s &> %s & " % (app_settings.RELOAD_COMMAND, reload_log))

    else:
        return HttpResponse("Invalid INLINETRANS_RELOAD_METHOD (%s) or \
            INLINETRANS_RELOAD_COMMAND is not specified" % app_settings.RELOAD_METHOD)

    return HttpResponse(str(reload_time))
