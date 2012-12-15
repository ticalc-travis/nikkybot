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

#ifndef __ui_h__
#define __ui_h__

void initCompat(void);
void sprintsaying(char*, char*, SAYING);
BOOL bookmarkDeleteConfirm(char*, SAYING);
BOOL bookmarkDialog(char*, SAYING, BOOL);
CALLBACK short sortBookmarksCompare(void*, void*);
void sortBookmarks(void);
void manageBookmarks(void);
void addBookmark(char*);
BOOL existsIn(char*, char*);
void search(BOOL, char*);
void gotoSaying(void);
void blankLine(short);
unsigned short printSaying(char*, unsigned short);
void sayingsUI(void);

#endif
