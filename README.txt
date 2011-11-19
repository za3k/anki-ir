====================================
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

Version: 0.2.2

This software is bundled with libxml2 as it's not included with Anki
(libxml2 is licensed under the GPL-compatible PSF licence, 
see LICENSE_libxml2.txt for details).

Changelog:

0.2.3:
- minor fix for Linux

0.2.2:
- more solid highlighting of extracted content
- automatic jumping to last extraction

0.2.1:
- complete rewrite to update for Anki 1.2.x
- more solid parsing/processing (based on libxml2)
- extracted content no longer removed, but marked (green background)
- undo/redo support

0.1.3:
- added hotkeys (r for remove, e for extract, c for extract+copy
  and shift+e or shift+c automatically adds the extracted card and
  closes the add dialog again)

0.1.2:
- increased reschedule default to 5-7 days
- added workaround for media bug in Anki

0.1.1:
- added reschedule popup menu entry
- added undo/redo support

0.1:
- initial version


Known bugs:
- text marking causes problems, when extracting already extracted parts
- strange font-style changes of marked content when extracting

TODOs:

- add/update last-extract-anchor and jump to it when card is shown
- rescheduling (wait with implementation. Damien is planning a huge change
  for Anki 2 scheduling)
====================================

