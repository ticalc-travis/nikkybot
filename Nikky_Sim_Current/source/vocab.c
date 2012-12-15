/*  The Nikky Simulator
 *  Copyright (C) 2012 Travis Evans
 * 
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, version 3.
 * 
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef CLI_PC_BUILD

#include <tigcclib.h>

#include "vocab.h"
#include "generate.h"
#include "nikky.h"
#include "ui.h"

#else

#include <stddef.h>
#include <stdint.h>

#include "vocab.h"
#include "generate.h"
#include "nikky-cli.h"

#endif

uint16_t tableLen(const TABLE* t) {
        uint16_t i;
        for (i = 0; t->entries[i].target != NULL; i++);
        return i;
}
