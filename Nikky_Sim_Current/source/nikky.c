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

#define USE_TI89
#define USE_TI92P
#define USE_V200
#define MIN_AMS 200

#define SAVE_SCREEN
#define OPTIMIZE_ROM_CALLS
#define COMPRESSED_FORMAT_RELOCS

#include <tigcclib.h>

#include "vocab.h"
#include "generate.h"
#include "nikky.h"
#include "ui.h"

#define CFGVARNAME "nikkycfg"
const unsigned char CFGVARTAG[] = {0, 'C', 'F', 'G', 0, OTH_TAG};

SAYING CurrentSaying;

enum ERRSTATUS {OK, MEMORY, INVALID};

BOOL cfgTagOK(FILE* f) {
        char tag[sizeof(CFGVARTAG)];

        BOOL CfgOK = FALSE;
        if (f) {
                if (!fseek(f, -sizeof(CFGVARTAG), SEEK_END)) {
                        fread(&tag, sizeof(CFGVARTAG), 1, f);
                        if (!memcmp(&CFGVARTAG, &tag, sizeof(CFGVARTAG)))
                                CfgOK = TRUE;
                        rewind(f);
                }
        }
        return CfgOK;
}

unsigned short loadCfg(void) {
        FILE* f = fopen(CFGVARNAME, "rb");
        BOOKMARK* bookmarks;
        CurrentSaying.x = 0;
        CurrentSaying.y = 0;
        CurrentSaying.rngMode = MTWISTER;
        NBookmarks = 0;

        if (f) {
                if (cfgTagOK(f)) {
                        fread(&CurrentSaying, sizeof(CurrentSaying), 1, f);
                        fread(&NBookmarks, sizeof(NBookmarks), 1, f);
                        hBookmarks = HeapRealloc(hBookmarks,
                                max(NBookmarks, 1) * sizeof(BOOKMARK));
                        if (hBookmarks) {
                                bookmarks = HeapDeref(hBookmarks);
                                if (bookmarks) fread(bookmarks,
                                        sizeof(BOOKMARK), NBookmarks, f);
                        } else {
                                fclose(f);
                                return MEMORY;
                        }
                } else {
                        fclose(f);
                        return INVALID;
                }
                fclose(f);
        }
        return OK;
}

unsigned short saveCfg(void) {
        BOOL archived = FALSE, success = FALSE;
        BOOKMARK *bookmarks;
        HSym hs = SymFind(SYMSTR(CFGVARNAME));
        SYM_ENTRY *se;
        
        if (hs.folder) {
                se = DerefSym(hs);
                if (se && se->flags.bits.archived) {
                        archived = TRUE;
                        EM_moveSymFromExtMem(NULL, hs);
                }
        }
        
        HeapLock(hBookmarks);
        bookmarks = HeapDeref(hBookmarks);
        if (bookmarks) {
                FILE* f = fopen(CFGVARNAME, "wb");
                if (f) {
                        fwrite(&CurrentSaying, sizeof(CurrentSaying), 1, f);
                        fwrite(&NBookmarks, sizeof(NBookmarks), 1, f);
                        bookmarks = HeapDeref(hBookmarks);
                        fwrite(bookmarks, sizeof(BOOKMARK), NBookmarks, f);
                        fwrite(CFGVARTAG, sizeof(CFGVARTAG), 1, f);
                        fclose(f);
                        success = TRUE;
                }
        }
        HeapUnlock(hBookmarks);
        
        if (!success) {
                return (DlgMessage("Error",
                        "Unable to update '" CFGVARNAME "' variable (low RAM?)",
                        BT_OK, BT_CANCEL) == KEY_ENTER ? TRUE : FALSE);
        }
        
        if (archived) EM_moveSymToExtMem(NULL, hs);
        return TRUE;
}

void _main(void) {
        hBookmarks = HeapAlloc(sizeof(BOOKMARK));
        unsigned short result;
        
        if (!hBookmarks) {
                DlgMessage("Error",
                        "Insufficient RAM to load '" CFGVARNAME "' variable",
                        BT_OK, BT_NONE);
                return;
        }
        
        result = loadCfg();
        if (result == MEMORY) {
                DlgMessage("Error",
                        "Insufficient RAM to load '" CFGVARNAME "' variable",
                        BT_OK, BT_NONE);
        } else if (result == INVALID) {
                DlgMessage("Error", "Invalid '" CFGVARNAME "' variable", BT_OK,
                           BT_NONE);
        } else {
                do {
                        sayingsUI();
                } while (!saveCfg());
        }
        if (hBookmarks) HeapFree(hBookmarks);
}
