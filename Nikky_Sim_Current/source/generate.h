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

#ifndef __generate_h__
#define __generate_h__

#define SENTENCE_ALLOC_SIZE 2048

/* Max y saying has no real limit, but anything beyond a few 10k or so
 * starts to get very slow */
#define MAX_Y_SAYING 9999

enum RNGMODES {STDLIB, MTWISTER};

typedef struct {
    uint32_t x;
    uint16_t rngMode:1, y:15;
} SAYING;

void randInit(uint32_t);
void randGenerate(void);
uint32_t randNext(void);
uint32_t randNextRange(uint32_t);

void setSaying(SAYING);
uint16_t chooseRandom(const TABLE*);
void randomCaps(char *);
void goNikky(char*, const TABLE*);

#endif
