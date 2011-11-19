"""
Incremental Reading plugin for Anki
Copyright (C) 2011 Frank Raiser

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Version: 0.2.3
"""

from ankiqt import ui
from anki.hooks import addHook
from ankiqt.ui import utils
from ankiqt import mw
from anki.facts import Fact
from anki.utils import tidyHTML

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebPage

import os
import libxml2, urllib2, tempfile
from urlparse import urljoin

mw.registerPlugin("Incremental Reading", 22)

# prepare urllib2 opener
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

__originalContextMenuEvent = None
__originalFlush = None

def onInit():
    """
    Plugin initialization:
    - replace context menu
    - replace flush method
    - add tools menu entry
    """
    #utils.showInfo("Initializing AnkiIR plugin")

    # replace context menu
    global __originalContextMenuEvent, __originalFlush
    __originalContextMenuEvent = mw.bodyView.body.contextMenuEvent
    mw.bodyView.body.contextMenuEvent = _contextMenuEvent
    #__originalFlush = mw.bodyView.flush
    #mw.bodyView.flush = _flush
    mw.connect(mw.bodyView.body, SIGNAL("loadFinished(bool)"),
        _onLoadFinished)

    # add menu entry
    menu = QMenu("Incremental Reading", mw)
    act = QAction(menu)
    act.setText("Add URL for IR")
    mw.connect(act, SIGNAL("triggered()"),
               doAddURL)
    menu.addAction(act)
    mw.mainWin.menuTools.addMenu(menu)
    #utils.showInfo("IR Plugin initialized")

addHook("init", onInit)

def _replaceImageSrc(url, attr):
    """
    Helper method for the src=... attribute of an image.
    Downloads image, adds it to media library, and updates
    the src attribute to point to the file in the media library.
    """
    imgurl = urljoin(url, attr.content)
    # download image
    img = opener.open(imgurl).read()
    _, ext = os.path.splitext(imgurl) # keep img file extension
    handle, filename = tempfile.mkstemp(suffix=ext[:4])
    os.write(handle, img)
    os.close(handle)

    # add to media library
    newurl = mw.deck.addMedia(filename)

    # replace src attribute
    attr.content = newurl

    try:
        os.unlink(filename)
    except: pass

def doAddURL():
    # get URL from clipboard
    url = str(QApplication.clipboard().mimeData().text())
    try:
        # download HTML file with urllib
        html = opener.open(url).read()
    except ValueError:
       utils.showInfo("Please copy a URL to clipboard first.")
       return
    # parse HTML and find images
    xml = libxml2.htmlParseDoc(html, 'utf-8')
    context = xml.xpathNewContext()
    # find correct nodes via XPath
    count = 0
    for img in context.xpathEval('//img'):
        # get src attribute
        attr = img.get_properties()
        imgurl = None
        while attr:
            if attr.name == 'src':
                _replaceImageSrc(url, attr)
                count += 1
                break
            attr = attr.get_next()

    # add new fact
    fact = Fact(mw.deck.currentModel)
    val = tidyHTML(xml.serialize(encoding='utf-8').decode('utf-8', 'replace'))
    fact.fields[0].value = val
    mw.deck.addFact(fact, reset = True)
    utils.showInfo("URL successfully added as new fact (%d pictures downloaded)" % count)

def _markSelection():
    """
    Helper method to mark the selected content with green background.
    Returns the selected content (as HTML)
    """
    # copy selected text
    mw.bodyView.body.page().triggerAction(QWebPage.Copy)
    # convert to HTML, parse it as XML
    cb = QApplication.clipboard()
    html = str(cb.mimeData().html().toUtf8())
    xml = libxml2.htmlParseDoc(html, 'utf-8')
    context = xml.xpathNewContext()
    # find correct node via XPath
    res = context.xpathEval('/html/body/span/span')
    if len(res):
        # prepare replacement HTML and place it into clipboard
        data = QMimeData()
        # strange work-around for stupid QT behavior
        if res[0].lsCountNode() == 1:
            outer = (u"<span style='background-color: rgb(0,255,0);'>", u"</span>")
        else:
            outer = (u"<div style='background-color: rgb(0,255,0);'>", u"</div>")
        data.setHtml(u"<html><body>"+
            outer[0] +
            u"<a name='new_extract_anchor'><span style='color: rgb(80,80,80); font-size:small;'>(Last Extract)</span></a>" +
            str(res[0]).decode('utf-8', 'replace') +
            outer[1] +
            u"</body></html>"
            )
        cb.clear()
        cb.setMimeData(data)
        #utils.showText("Clipboard data: " + str(cb.mimeData().html().toUtf8()))
        # switch page to editable, paste replacement, make it uneditable again
        mw.bodyView.body.page().setContentEditable(True)
        mw.bodyView.body.page().triggerAction(QWebPage.Paste)
        mw.bodyView.body.page().setContentEditable(False)
        #utils.showText(str(res[0]) + "\n###\n" + mw.bodyView.body.page().mainFrame().toHtml())
    else:
        utils.showInfo("xpath failure (1)")
    # free resources
    xml.freeDoc()
    context.xpathFreeContext()

    _updateCardFromPage()

    return html

def _updateCardFromPage():
    # Update card/fact
    # get html
    newHtml = str(mw.bodyView.body.page().mainFrame().toHtml().toUtf8())
    xml = libxml2.htmlParseDoc(newHtml, 'utf8')
    _updateAnchor(xml)
    context = xml.xpathNewContext()
    # find <div class="cardq" ...> tag to get only the main content
    res = context.xpathEval("//div[@class='cardq']")
    if len(res):
        # construct card content from serializations of children
        child = res[0].get_children()
        buf = u''
        while child:
            # (strange behavior of libxml2: it replaces html entities by unicode chars)
            # replace our work-around that used &nbsp;
            res = child.serialize(encoding='utf-8').replace('<span>\xc2\xa0</span>', '')
            buf += res.decode('utf-8', 'replace')
            child = child.get_next()
        fact = mw.currentCard.fact
        fact.fields[0].value = buf
        #utils.showText("New value: " + buf)
        fact.setModified(textChanged=True, deck=mw.deck)
        mw.deck.save()
        mw.deck.s.commit()
    else:
        utils.showInfo("xpath failure (2)")
    # free resources
    xml.freeDoc()
    context.xpathFreeContext()

    # update view
    mw.bodyView.redisplay()

def _updateAnchor(xml):
    """
    Helper method to update the last extract anchor from the current page's HTML.
    Only changes the given XML structure. Caller must make changes to fact.
    """
    context = xml.xpathNewContext()
    # is there a new anchor?
    nanchors = context.xpathEval("//a[@name='new_extract_anchor']")
    if len(nanchors):
        # remove existing anchors
        oanchors = context.xpathEval("//a[@name='last_extract_anchor']")
        for anchor in oanchors:
            anchor.unlinkNode()
            anchor.freeNode()
        # update new anchor (only property should be name=...
        name = nanchors[0].get_properties()
        name.setContent('last_extract_anchor')
        #utils.showText("Anchors updated: " + str(xml))
    else:
        utils.showInfo("No new anchor found")
    # update HTML view
    #mw.bodyView.body.page().mainFrame().setHtml(xml.serialize(encoding='utf-8').decode('utf-8', 'replace'))


def _onExtract():
    mw.deck.setUndoStart('Extract')
    # mark selection, get selected content
    html = _markSelection()
    mw.deck.setUndoEnd('Extract')
    # open add cards dialog
    addDialog = ui.dialogs.get("AddCards", mw)
    # add selected content to first field (Front) and
    # update editor display
    addDialog.editor.fact.fields[0].value = tidyHTML(html.decode('utf-8', 'replace'))
    addDialog.editor.drawFields(check=True)

def _onRemove():
    mw.deck.setUndoStart('Remove')
    # removes selection
    page = mw.bodyView.body.page()
    page.setContentEditable(True)
    page.triggerAction(QWebPage.Cut)
    page.setContentEditable(False)
    _updateCardFromPage()
    mw.deck.setUndoEnd('Remove')

def _contextMenuEvent(evt):
    body = mw.bodyView.body
    txt = body.selectedText()
    if not txt:
        return __originalContextMenuEvent(evt)
    menu = QMenu()
    menu.addAction("Extract", _onExtract)
    menu.addAction("Remove", _onRemove)
    menu.exec_(body.mapToGlobal(evt.pos()))

def _onLoadFinished(boolarg):
    """
    #Overwrites ankiqt.View.flush in order to jump the view to our anchors.
    """
    #__originalFlush()
    try:
        mw.bodyView.body.page().mainFrame().scrollToAnchor("last_extract_anchor")
    except AttributeError: pass
    #utils.showInfo("Intercepted")
