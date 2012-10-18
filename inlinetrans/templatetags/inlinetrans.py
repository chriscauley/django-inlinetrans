# coding=utf-8
import copy

from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.template import TemplateSyntaxError, TokenParser, Node, Variable

try:
    from django.template.base import _render_value_in_context
except ImportError: # Django 1.1 fallback
    from django.template import _render_value_in_context

from django.utils.translation import get_language
from django.utils.translation.trans_real import catalog

# Using relative import to get inlinetrans.settings module
from .. import settings as app_settings

register = template.Library()



def get_language_name(lang):
    for lang_code, lang_name in settings.LANGUAGES:
        if lang == lang_code:
            return lang_name



class NotTranslated(object):
    @staticmethod
    def ugettext(cadena):
        raise ValueError("not translated")

    @staticmethod
    def add_fallback(func):
        return



class InlineTranslateNode(Node):
    def __init__(self, filter_expression, noop):
        self.noop = noop
        self.filter_expression = filter_expression

        if isinstance(self.filter_expression.var, basestring):
            self.filter_expression.var = Variable(u"'%s'" % self.filter_expression.var)

    def render(self, context):
        if 'user' in context:
            user = context['user']
        elif 'request' in context:
            user = getattr(context.get('request'), 'user', None)
        else:
            user = None
        if not (user and user.is_staff):
            self.filter_expression.var.translate = not self.noop
            output = self.filter_expression.resolve(context)

            return _render_value_in_context(output, context)

        if getattr(self.filter_expression.var, 'literal'):
            msgid = self.filter_expression.var.literal
        else:
            msgid = self.filter_expression.resolve(context)

        cat = copy.copy(catalog())
        cat.add_fallback(NotTranslated)
        styles = ['translatable']

        try:
            msgstr = cat.ugettext(msgid)

        except ValueError:
            styles.append("untranslated")
            msgstr = msgid

        return render_to_string('inlinetrans/inline_trans.html',{
            'msgid': msgid,
            'styles': ' '.join(styles),
            'value': msgstr})



def inline_trans(parser, token):
    """
    Template tag 'itrans' that replaces Django's 'trans' template tag.
    """
    class TranslateParser(TokenParser):
        def top(self):
            value = self.value()
            if self.more():
                if self.tag() == 'noop':
                    noop = True
                else:
                    raise TemplateSyntaxError("only option for 'trans' is 'noop'")
            else:
                noop = False
            return (value, noop)

    value, noop = TranslateParser(token.contents).top()

    return InlineTranslateNode(parser.compile_filter(value), noop)

register.tag('inline_trans', inline_trans)
register.tag('itrans', inline_trans)



@register.inclusion_tag('inlinetrans/inline_header.html', takes_context=True)
def inlinetrans_media(context):
    """
    Template tag that renders the html tags to include the necessary stylesheets
    and javascript files
    """
    tag_context = {
        'is_translator': False,
        'INLINETRANS_STATIC_URL': app_settings.STATIC_URL,
        'request': context['request'],
    }

    # if the user is a translator
    if 'user' in context and \
       context['user'].groups.filter(name=app_settings.TRANSLATORS_GROUP).count() > 0:
        tag_context.update({
            'is_translator': True,
            'language': get_language_name(get_language()),
        })

    return tag_context



@register.inclusion_tag('inlinetrans/inline_toolbar.html', takes_context=True)
def inlinetrans_toolbar(context, node_id):
    """
    Template tag that renders the inlinetrans toolbar.
    """
    tag_context = {
        'is_translator': False,
        'INLINETRANS_STATIC_URL': app_settings.STATIC_URL,
        'request': context['request'],
    }

    # if the user is a translator
    if 'user' in context and\
       context['user'].groups.filter(name=app_settings.TRANSLATORS_GROUP).count() > 0:
        tag_context.update({
            'is_translator': True,
            'language': get_language_name(get_language()),
            'node_id': node_id,
        })

    else:
        tag_context.update({
            'request': context['request'],
        })
    return tag_context

