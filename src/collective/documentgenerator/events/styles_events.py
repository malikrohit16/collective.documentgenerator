# -*- coding: utf-8 -*-

from appy.shared.utils import executeCommand

from collective.documentgenerator.content.pod_template import IPODTemplate

from plone import api
from plone.namedfile.file import NamedBlobFile

import appy.pod
import logging
import os
import tempfile
import time

logger = logging.getLogger('collective.documentgenerator: styles update')

CONVSCRIPT = '%s/converter.py' % os.path.dirname(appy.pod.__file__)


def update_styles_of_all_PODtemplate(style_template, event):
    """
    Update all pod templates using 'style_template'.
    """
    style_odt = style_template.odt_file
    #template style is modify, update all template with style.
    style_template_filename = _create_temporary_style_template(style_odt)
    if style_template_filename:
        catalog = api.portal.get_tool('portal_catalog')
        pod_templates = catalog(object_provides=IPODTemplate.__identifier__)
        for brain in pod_templates:
            pod_template = brain.getObject()
            if pod_template.get_style_template() == style_template:
                _update_template_style(pod_template, style_template_filename)
                logger.info(" %s => updated" % pod_template.Title())

    #delete temporary styles files
    os.remove(style_template_filename)


def update_PODtemplate_styles(pod_template, event):
    """
    Update styles on a pod_template using external styles.
    """
    style_template = pod_template.get_style_template()
    if not style_template:
        return
    style_odt = style_template.odt_file
    style_template_filename = _create_temporary_style_template(style_odt)
    _update_template_style(pod_template, style_template_filename)


def _create_temporary_style_template(style_template):
    """
    Create Temporary file from template style.
    """
    if style_template and style_template.size:
        #save in temporary file, the style_template

        style_template_filename = '%s/%s_%f.%s' % (tempfile.gettempdir(), 'style_template', time.time(), 'odt')
        new_style_template = file(style_template_filename, "w")
        new_style_template.write(style_template.data)
        new_style_template.close()
        return style_template_filename
    return ''


def _update_template_style(pod_template, style_template_filename):
    """
    Update template pod_template by templateStyle.
    """
    #save in temporary file, the template
    tempFileName = '%s/%s_%f.%s' % (tempfile.gettempdir(), pod_template.UID(), time.time(), 'odt')
    newTemplate = file(tempFileName, "w")
    newTemplate.write(pod_template.odt_file.data)
    newTemplate.close()
    #merge style from templateStyle in template
    cmd = '%s %s %s %s -p%d -t%s' % \
        ('/usr/bin/python', CONVSCRIPT, tempFileName, 'odt',
            2002, style_template_filename)
    executeCommand(cmd)
    #read the merged file
    resTempFileName = tempFileName[:-3] + 'res.odt'
    if os.path.isfile(resTempFileName):
        resTemplate = open(resTempFileName, 'rb')
        #update template
        result = NamedBlobFile(data=resTemplate.read(),  contentType='applications/odt')
        pod_template.odt_file = result
        #delete temporary result files
        os.remove(resTempFileName)
    #delete temporary files
    os.remove(tempFileName)
