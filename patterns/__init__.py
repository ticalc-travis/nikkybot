# -*- coding: utf-8 -*-

# “NikkyBot”
# Copyright ©2012-2014 Travis Evans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import importlib

import _table
reload(_table)

_PATTERN_FILES = ('general', 'remarks',
                  'commands', 'community', 'computers', 'meta', 'synonyms')

# Load all patterns
generic_remarks = []
patterns = []
for module_name in _PATTERN_FILES:
    m = importlib.import_module(__name__ + '.' + module_name)
    reload(m)       # Update in case of dynamic reload
    try:
        generic_remarks += list(m.generic_remarks)
    except AttributeError:
        pass
    try:
        patterns += m.patterns
    except AttributeError:
        pass
