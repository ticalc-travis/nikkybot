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

#ifndef __nikky_h__
#define __nikky_h__

#define COMMENT_PROGRAM_NAME   "The Nikky Simulator"
#define COMMENT_VERSION_STRING "v0.10.01"
#define COMMENT_VERSION_NUMBER 0,1,0,1
#define COMMENT_AUTHORS        "Travis Evans"

typedef struct {
        unsigned char name[19];
        SAYING seed;
} BOOKMARK;

signed short CfgOK;
SAYING CurrentSaying;
HANDLE hBookmarks;
unsigned short NBookmarks;

BOOL cfgTagOK(FILE*);
unsigned short loadCfg(void);
unsigned short saveCfg(void);
void _main(void);

#endif
