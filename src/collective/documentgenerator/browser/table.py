# -*- coding: utf-8 -*-
"""Define tables and columns."""

import os
from Products.CMFPlone import PloneMessageFactory as PMF
from Products.CMFPlone.utils import safe_unicode, normalizeString, base_hasattr
from collective.documentgenerator import _
from plone import api
from z3c.table.column import Column, LinkColumn
from z3c.table.table import Table
from zope.cachedescriptors.property import CachedProperty
from zope.i18n import translate


class TemplatesTable(Table):

    """Table that displays templates info."""

    cssClassEven = u'even'
    cssClassOdd = u'odd'
    cssClasses = {'table': 'listing templates-listing'}

    batchSize = 30
    startBatchingAt = 35
    sortOn = None
    results = []

    def __init__(self, context, request):
        super(TemplatesTable, self).__init__(context, request)
        self.portal = api.portal.getSite()
        self.context_path = self.context.absolute_url_path()
        self.context_path_len = len(self.context_path)
        self.paths = {'': '-'}

    @CachedProperty
    def translation_service(self):
        return api.portal.get_tool('translation_service')

    @CachedProperty
    def wtool(self):
        return api.portal.get_tool('portal_workflow')

    @CachedProperty
    def portal_url(self):
        return api.portal.get().absolute_url()

    @CachedProperty
    def values(self):
        return self.results


class TitleColumn(LinkColumn):

    """Column that displays title."""

    header = PMF("Title")
    weight = 10
    cssClasses = {'td': 'title-column'}

    def getLinkCSS(self, item):
        return ' class="state-%s icons-on contenttype-%s"' % (api.content.get_state(obj=item),
                                                              normalizeString(item.portal_type))

    def getLinkContent(self, item):
        return safe_unicode(item.title)


class PathColumn(LinkColumn):

    """Column that displays path."""

    header = _("Path")
    weight = 20
    cssClasses = {'td': 'path-column'}
    linkTarget = '_blank'

    def getLinkURL(self, item):
        """Setup link url."""
        return item.__parent__.absolute_url()

    def getLinkContent(self, item):
        path = item.absolute_url_path()[self.table.context_path_len:-(len(item.id)) - 1]
        if path not in self.table.paths:
            parent_path = '/'.join(path.split('/')[:-1])
            if parent_path:
                self.table.paths[path] = '%s / %s' % (self.table.paths[parent_path], item.__parent__.title)
            else:
                self.table.paths[path] = item.__parent__.title
        return self.table.paths[path]


class EnabledColumn(Column):

    """Column that displays enabled status."""

    header = _("Enabled")
    weight = 30
    cssClasses = {'td': 'enabled-column'}

    def renderCell(self, item):
        if not base_hasattr(item, 'enabled'):
            return u'-'
        if item.enabled:
            icon = ('++resource++collective.documentgenerator/ok.png',
                    self.table.translation_service.translate('Enabled'))
        else:
            icon = ('++resource++collective.documentgenerator/nok.png',
                    self.table.translation_service.translate('Disabled'))
        return u"<img title='{0}' src='{1}' />".format(
            safe_unicode(icon[1]).replace("'", "&#39;"),
            u"{0}/{1}".format(self.table.portal_url, icon[0]))


class OriginalColumn(Column):

    """Column that displays original status."""

    header = _("Original")
    weight = 40
    cssClasses = {'td': 'original-column'}

    def renderCell(self, item):
        if item.has_been_modified():
            icon = ('++resource++collective.documentgenerator/nok.png',
                    self.table.translation_service.translate('Modified'))
        else:
            icon = ('++resource++collective.documentgenerator/ok.png',
                    self.table.translation_service.translate('Original'))
        return u"<img title='{0}' src='{1}' />".format(
            safe_unicode(icon[1]).replace("'", "&#39;"),
            u"{0}/{1}".format(self.table.portal_url, icon[0]))


class ReviewStateColumn(Column):

    """Column that displays review state."""

    header = PMF("Review state")
    weight = 50

    def renderCell(self, item):
        state = api.content.get_state(item)
        if state:
            state_title = self.table.wtool.getTitleForStateOnType(state, item.portal_type)
            return translate(PMF(state_title), context=self.request)
        return ''


class ActionsColumn(Column):
    """
    A column displaying available actions of the listed item.
    Need imio.actionspanel to be used !
    """

    header = _("Actions")
    weight = 60
    params = {'useIcons': True, 'showHistory': False, 'showActions': True, 'showOwnDelete': False,
              'showArrows': True, 'showTransitions': False}

    def renderCell(self, item):
        # avoid double '//' that breaks (un)restrictedTraverse, moreover path can not be unicode
        path = os.path.join(item.absolute_url_path(), 'actions_panel').encode('utf-8')
        return self.table.portal.unrestrictedTraverse(path)(**self.params)
