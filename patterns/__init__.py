# “NikkyBot”
# Copyright ©2012-2016 Travis Evans
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

from . import _table
reload(_table)

_GLOBAL_PATTERN_FILES = ('global', 'synonyms')
_NIKKY_PATTERN_FILES = ('general', 'remarks',
                        'commands', 'community', 'computers', 'meta',
                        'nikkyisms')

global_patterns = []
nikky_generic_remarks = []
nikky_patterns = []

# Load global patterns (nikky and all other personalities)

for module_name in _GLOBAL_PATTERN_FILES:
    m = importlib.import_module(__name__ + '.' + module_name)
    reload(m)       # Update in case of dynamic reload
    try:
        global_patterns += m.patterns
        nikky_patterns += m.patterns
    except AttributeError:
        pass

# Load nikky-only patterns and remarks

for module_name in _NIKKY_PATTERN_FILES:
    m = importlib.import_module(__name__ + '.' + module_name)
    reload(m)       # Update in case of dynamic reload
    try:
        nikky_generic_remarks += list(m.generic_remarks)
    except AttributeError:
        pass
    try:
        nikky_patterns += m.patterns
    except AttributeError:
        pass
