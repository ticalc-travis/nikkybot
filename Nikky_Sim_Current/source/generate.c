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

#else

#include <stdint.h>
#include <string.h>

#include "vocab.h"
#include "generate.h"

#define BOOL int
#define TRUE 1
#define FALSE 0

#endif

uint32_t randState[624];
uint16_t randStateIdx;

void randInit(uint32_t seed) {
#ifndef CLI_PC_BUILD
    if (CurrentSaying.rngMode == STDLIB) {
        srand(seed);
        return;
    }
#endif
    randStateIdx = 0;
    randState[0] = seed;
    int i;
    for (i = 1; i < 624; i++)
        randState[i] = 0x6c078965 * (randState[i-1] ^ (randState[i-1] >> 30)) + i;
}

/* Generate next set of random numbers--called automatically by randNext and
 * randNextRange as needed */
void randGenerate(void) {
    uint16_t i;
    uint32_t y;
    
    for (i = 0; i < 624; i++) {
        y = ((randState[i] & 0x80000000) |
            (randState[(i + 1) % 624] & 0x7fffffff));
        randState[i] = randState[(i + 397) % 624] ^ (y >> 1);
        if (y & 1) randState[i] = randState[i] ^ 0x9908b0df;
    }
}

uint32_t randNext(void) {
#ifndef CLI_PC_BUILD
        if (CurrentSaying.rngMode == STDLIB)
                return rand();
#endif
        if (!randStateIdx) randGenerate();
        uint32_t y = randState[randStateIdx];
        
        y = y ^ (y >> 11);
        y = y ^ ((y << 7) & 0x9d2c5680);
        y = y ^ ((y << 15) & 0xefc60000);
        y = y ^ (y >> 18);
        
        randStateIdx = (randStateIdx + 1) % 624;
        
        return y;
}

/* Return pseudorandom value from 0 to n - 1 */
uint32_t randNextRange(uint32_t n) {
#ifndef CLI_PC_BUILD
        if (CurrentSaying.rngMode == STDLIB)
                return random(n);
#endif
        return randNext() % n;
}

void setSaying(SAYING saying) {
        uint16_t i;
        
        randInit(saying.x);
        for (i = 0; i < saying.y; i++) randNext();
}

uint16_t chooseRandom(const TABLE* table) {
        uint16_t i;
        do i = randNextRange(tableLen(table)); while
#ifndef CLI_PC_BUILD
                /* Need to preserve sayings exactly from old version when using
                 * old PRNG.  Unfortunately, this means the incorrect subtraction
                 * from value eventually returned by random() has to be
                 * emulated, an addition to some funky typecasting to simulate
                 * the underflow exactly as before. */
                ((int16_t)randNextRange(128) -
                        (CurrentSaying.rngMode == STDLIB ? 1 : 0) >
                                table->entries[i].probability);
#else
                (randNextRange(128) > table->entries[i].probability);
#endif
        return i;
}

void randomCaps(char* string) {
        BOOL r = !randNextRange(2);
        unsigned int i;
        unsigned char c;
        
        for (i = 0; i < strlen(string); i++) {
                c = string[i];
                switch(c) {
                        case '.':
                        case ',':
                        case ';':
                        case '!':
                        case '?':
                                if (randNextRange(3) == 1) r = !r;
                }
                if (r) string[i] = toupper(string[i]);
        }
}

void goNikky(char *outText, const TABLE* table) {
        unsigned int i, newChar;
        char *t;
        static BOOL capitalize = FALSE;

        switch (table->type) {
                case SEQUENCE:
                        // Execute template entries in sequential order
                        for (i = 0; i < tableLen(table); i++) {
#ifndef CLI_PC_BUILD
                                 if ((int16_t)randNextRange(128) -
                                     (CurrentSaying.rngMode == STDLIB ? 1 : 0) <=
                                        /* See above in chooseRandom().  
                                         * Technically erraneous in the previous
                                         * version but now needed to ensure
                                         * sayings don't change */
#else
                                if (randNextRange(128) <=
#endif
                                        table->entries[i].probability) {
                                    capitalize =
                                            table->entries[i].capitalize ||
                                            capitalize;
                                    goNikky(outText, table->entries[i].target);
                                }
                        }
                        break;
                case RANDOM:
                        // Randomly select an entry from template pointed to
                        i = chooseRandom(table);
                        capitalize = table->entries[i].capitalize || capitalize;
                        goNikky(outText, table->entries[i].target);
                        break;
                case VOCABULARY:
                        // Randomly select word from list and add it
                        i = chooseRandom(table);
                        t = (char*)table->entries[i].target;
                        newChar = strlen(outText);
                        strncat(outText, t,
                                (SENTENCE_ALLOC_SIZE - (strlen(outText)) - 1));
                        if (capitalize)
                                outText[newChar] = toupper(outText[newChar]);
                        capitalize = 0;
                        if (randNextRange(256) == 1) {
                                // ALL CAPS DAY
                                randomCaps(outText);
                        }
        }
}
