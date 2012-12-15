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

#define MIN_AMS 200

#include <tigcclib.h>

#include "vocab.h"
#include "generate.h"
#include "nikky.h"
#include "ui.h"

#define MAX_SEARCH 100

#define HEADER_TOP 1
#define TXT_TOP 15
#define TXT_LEFT 1
#define TXT_RIGHT scrw
#define TXT_BOTTOM scrh - 17 - 8
#define TXT_FOOTER scrh - 15

#define KUP (calc ? 338 : 337)
#define KDOWN (calc ? 344 : 340)
#define KLEFT (calc ? 337 : 338)
#define KRIGHT (calc ? 340 : 344)
#define KCUT (calc ? 8280 : 20480)
#define KCOPY (calc ? 8259 : 24576 )

static unsigned short calc, scrw, scrh;

const char* helpText =
"\x15\x16\x17\x18 Browse sayings\n"
"[ENTER] Page long sayings\n"
"[STO\x12] Bookmark saying\n\n"
"[F2] Manage bookmarks\n"
"[F8] Search sayings\n"
"[F3] Repeat last search\n"
"[F4] Jump to random saying\n"
"[F5] Go to saying #\n"
"[F6] About\n"
"[F7] Switch random number generator methods (A=Native, B=Mersenne Twister)\n\n"
"[CUT] Copy saying to clipboard\n"
"[COPY] Append saying to current clipboard\n\n"
"[ESC]/[QUIT] Quit";

const char* aboutText =
"Copyright \xA9 2012 Travis Evans <travise@ticalc.org>\n\n"
"This program is free software; you can redistribute it and/or modify it under "
"the terms of the GNU General Public License as published by the Free "
"Software Foundation, version 3.\n\n"
"This software comes with ABSOLUTELY NO WARRANTY.  You should have received a "
"copy of the GNU General Public License along with this program.  If not, see "
"<http://www.gnu.org/licenses/>.";

// Set up calc-dependent constants
void initCompat(void) {
        calc = CALCULATOR;
        scrh = calc ? 128 : 100;
        scrw = calc ? 240 : 160;
}

void sprintsaying(char* out, char* prefix, SAYING saying) {
        char rng = saying.rngMode == STDLIB ? 'A' : 'B';
        sprintf(out, "%s#%c-%lu-%u", prefix, rng, saying.x, saying.y);
}

BOOL bookmarkDeleteConfirm(char* bookmarkName, SAYING saying) {
        HANDLE dlg = H_NULL;
        char sayingStr[27];
        short result;
        
        dlg = DialogNewSimple(calc?159:150, calc?75:60);
        if (dlg) {
                DialogAddTitle(dlg, "Delete bookmark", BT_OK, BT_CANCEL);
                DialogAddText(dlg, 3, calc?14:14, "Are you sure you want to");
                DialogAddText(dlg, 3, calc?23:21, "delete this bookmark?");
                DialogAddText(dlg, 3, calc?40:33, bookmarkName);
                sprintsaying(sayingStr, "Saying ", saying);
                DialogAddText(dlg, 3, calc?49:40, sayingStr);
                result = DialogDo(dlg, CENTER, CENTER, NULL, NULL);
                HeapFree(dlg);
                return result == KEY_ENTER ? TRUE : FALSE;
        } else {
                DlgMessage("Error", "Insufficient RAM for dialog box",
                        BT_OK, BT_NONE);
                return FALSE;
        }
}

BOOL bookmarkDialog(char* bookmarkName, SAYING saying, BOOL new) {
        HANDLE dlg = H_NULL;
        char sayingStr[27];
        short result;
        
        dlg = DialogNewSimple(calc?200:150, calc?50:45);
        if (dlg) {
                DialogAddTitle(dlg, new ? "Save bookmark" : "Edit bookmark",
                        BT_OK, BT_CANCEL);
                sprintsaying(sayingStr, "Saying", saying);
                DialogAddText(dlg, 3, 14, sayingStr);
                DialogAddRequest(dlg, 3, calc?25:24, "Name:", 0, 18, 19);
                result = DialogDo(dlg, CENTER, CENTER, bookmarkName, NULL);
                HeapFree(dlg);
                return result == KEY_ENTER ? TRUE : FALSE;
        } else {
                DlgMessage("Error", "Insufficient RAM for dialog box",
                        BT_OK, BT_NONE);
                return FALSE;
        }
}

CALLBACK short sortBookmarksCompare(void* b1, void* b2) {
        return cmpstri(((BOOKMARK*)b1)->name, ((BOOKMARK*)b2)->name);
}

void sortBookmarks(void) {
        BOOKMARK* bookmarks = HeapDeref(hBookmarks);
        qsort(bookmarks, NBookmarks, sizeof(BOOKMARK),
              (compare_t)sortBookmarksCompare);
}

void manageBookmarks(void) {
        HANDLE mnu = H_NULL;
        BOOKMARK* bookmarks = HeapDeref(hBookmarks);
        char name[19];
        signed short chosenItem = 0, i;
        
        if (!NBookmarks) {
                DlgMessage("Bookmarks",
                        "No bookmarks. Press [STO\x12] while viewing a saying to create one.",
                        BT_OK, BT_NONE);
                return;
        }
        
        HeapLock(hBookmarks);
        do {
                mnu = PopupNew("Bookmarks", 0);
                if (mnu) {
                        for (i = 0; i < NBookmarks; i++)
                                PopupAddText(mnu, -1, bookmarks[i].name, i + 1);
                        chosenItem = PopupDo(mnu, CENTER, CENTER, 1);
                        HeapFree(mnu);
                        
                        if (chosenItem) {
                                i = chosenItem - 1;
                                mnu = PopupNew("", 0);
                                if (mnu) {
                                        PopupAddText(mnu, -1, "Open", 1);
                                        PopupAddText(mnu, -1, "Edit name\xA0", 2);
                                        PopupAddText(mnu, -1, "Delete\xA0", 3);
                                        chosenItem = PopupDo(mnu, CENTER, CENTER, 1);
                                        HeapFree(mnu);
                                        
                                        switch(chosenItem) {
                                                case 1:
                                                        memcpy(&CurrentSaying, &bookmarks[i].seed,
                                                               sizeof(SAYING));
                                                        chosenItem = 0;
                                                        break;
                                                case 2:
                                                        memcpy(name, bookmarks[i].name, sizeof(char) * 19);
                                                        if (bookmarkDialog(name, bookmarks[i].seed, FALSE))
                                                                memcpy(bookmarks[i].name, name, sizeof(char) * 19);
                                                                sortBookmarks();
                                                        break;
                                                case 3:
                                                        if (bookmarkDeleteConfirm(bookmarks[i].name, bookmarks[i].seed)) {
                                                                memmove(&bookmarks[i], &bookmarks[i + 1], sizeof(BOOKMARK) * (NBookmarks - i));
                                                                NBookmarks--;
                                                        }
                                                        break;
                                                default:
                                                        chosenItem = -1;
                                        }
                                } else {
                                        DlgMessage("Error",
                                                "Insufficient RAM for menu",
                                                BT_OK, BT_NONE);
                                        return;
                                }
                        }
                } else {
                        DlgMessage("Error", "Insufficient RAM for menu",
                                        BT_OK, BT_NONE);
                        return;
                }
        } while (chosenItem);

        HeapUnlock(hBookmarks);
}

void addBookmark(char* defaultTitle) {
        BOOKMARK *bookmarks;
        char in[19];
        
        strncpy(in, defaultTitle, 18);
        in[18] = 0;
        if (bookmarkDialog(in, (SAYING)CurrentSaying, TRUE)) {
                BOOL success = FALSE;
                bookmarks = HeapDeref(hBookmarks);
                
                if (bookmarks && HeapRealloc(hBookmarks,
                        (NBookmarks + 1) * sizeof(BOOKMARK))) {
                        bookmarks = HeapDeref(hBookmarks);
                        if (bookmarks) {
                                memcpy(&bookmarks[NBookmarks].seed, &CurrentSaying,
                                        sizeof(SAYING));
                                memcpy(bookmarks[NBookmarks].name, in,
                                         sizeof(char) * 19);
                                NBookmarks++;
                                sortBookmarks();
                                success = TRUE;
                        }
                }
                if (!success) DlgMessage("Error",
                        "Insufficient RAM to save bookmark",
                        BT_OK, BT_NONE);
        }
}

// Case-insensitive check if sub exists in s
BOOL existsIn(char* s, char* sub) {
        unsigned short i, j, subl = strlen(sub);
        if (strlen(s) >= subl)  // Need to check, or we begin searching beyond 
        {                       // the string terminator
                for (i = 0; s[i + subl]; i++) {
                        for (j = 0; toupper(s[i + j]) == toupper(sub[j]) && sub[j]; j++);
                        if (!sub[j]) return TRUE;
                }
        }
        return FALSE;
}

// Search sayings for string
void search(BOOL getNew, char* sent) {
        HANDLE dlg = H_NULL, mnu = H_NULL;
        static char searchString[MAX_SEARCH + 1] = "";
        static unsigned short direction = 1;
        unsigned long oldx = CurrentSaying.x, oldy = CurrentSaying.y;
        BOOL proceed = FALSE;
        
        if (getNew || !searchString[0]) {
                mnu = PopupNew("", 0);
                dlg = DialogNewSimple(calc?200:150, calc?52:45);
                if (dlg && mnu) {
                        PopupAddText(mnu, -1, "#\x13-#", 1);
                        PopupAddText(mnu, -1, "#-#\x13", 2);
                        PopupAddText(mnu, -1, "#\x14-#", 3);
                        PopupAddText(mnu, -1, "#-#\x14", 4);
                        
                        DialogAddTitle(dlg, "Find", BT_OK, BT_CANCEL);
                        DialogAddRequest(dlg, 3, 15,
                                        "Search for", 0, MAX_SEARCH, 16);
                        DialogAddPulldown(dlg, 3, calc?26:24,
                                        "Direction:", mnu, 0);
                        if (DialogDo(dlg, CENTER, CENTER,
                                searchString, &direction) == KEY_ENTER)
                                proceed = TRUE;
                        HeapFree(dlg);
                        HeapFree(mnu);
                } else {
                        DlgMessage("Error", "Insufficient RAM for dialog box",
                                BT_OK, BT_NONE);
                        if (dlg) HeapFree(dlg);
                        if (mnu) HeapFree(mnu);
                        return;
                }
        } else {
                proceed = TRUE;
        }
        
        if (proceed) {
                char disp[50];
                unsigned long tick = 0;
                blankLine(TXT_FOOTER);
                DrawStr(0, TXT_FOOTER, "Press [ON] to stop\xA0", A_NORMAL);

                do {
                        /* Silk-smooth racing numbers are fun to watch, but
                         * AMS's routines just slow it down too much--better to
                         * limit update rate to significantly speed the search */
                        if ((FiftyMsecTick - tick) > 20) {
                                sprintsaying(disp, "Search: ", CurrentSaying);
                                blankLine(HEADER_TOP);
                                DrawStr((scrw / 2 - strlen(disp) * 6 / 2),
                                        HEADER_TOP, disp, A_REPLACE);
                                if (kbhit()) {
                                        if (ngetchx() == KEY_ON) {
                                                OSClearBreak();
                                                CurrentSaying.x = oldx;
                                                CurrentSaying.y = oldy;
                                                break;
                                        }
                                }
                                tick = FiftyMsecTick;
                        }
                        
                        switch(direction) {
                                case 1:
                                        CurrentSaying.x++;
                                        if (CurrentSaying.x == 0)
                                                CurrentSaying.y++;
                                                if (CurrentSaying.y > MAX_Y_SAYING)
                                                        CurrentSaying.y = 0;
                                        break;
                                case 2:
                                        CurrentSaying.y++;
                                        if (CurrentSaying.y > MAX_Y_SAYING) {
                                                CurrentSaying.y = 0;
                                                CurrentSaying.x++;
                                        }
                                        break;
                                case 3:
                                        CurrentSaying.x--;
                                        if ((signed long)CurrentSaying.x == -1)
                                                CurrentSaying.y--;
                                                if (CurrentSaying.y == 32767)
                                                        CurrentSaying.y = MAX_Y_SAYING;
                                        break;
                                case 4:
                                        CurrentSaying.y--;
                                        if (CurrentSaying.y == 32767) {
                                                CurrentSaying.y = MAX_Y_SAYING;
                                                CurrentSaying.x--;
                                        }
                        }
                        sent[0] = 0;
                        setSaying(CurrentSaying);
                        goNikky(sent, &rootTable);
            } while (!existsIn(sent, searchString));
        }
}

void gotoSaying(void) {
        HANDLE dlg = H_NULL;
        char in[18];
        sprintf(in, "%lu-%u", CurrentSaying.x, CurrentSaying.y);
        
        dlg = DialogNewSimple(calc?160:124, calc?60:57);
        if (dlg) {
                DialogAddTitle(dlg, "Goto saying", BT_OK, BT_CANCEL);
                DialogAddText(dlg, 3, calc?14:15, "Enter saying number");
                DialogAddText(dlg, 3, calc?23:24, "(example: 1234-567)");
                DialogAddRequest(dlg, 3, calc?34:35, "#", 0, 15, 16);
                DialogAddXFlags(dlg, 0, XF_NO_ALPHA_LOCK, 0, 0, 0);
                if (DialogDo(dlg, CENTER, CENTER, in, NULL) == KEY_ENTER) {
                        // In case no y value entered, assume 0
                        strcat(in, "-0");
                        
                        CurrentSaying.x = atol(in);
                        CurrentSaying.y = min(
                                atol(&in[strspn(in, "0123456789") + 1]),
                                MAX_Y_SAYING);
                }
                HeapFree(dlg);
        } else {
                DlgMessage("Error", "Insufficient RAM for dialog box",
                        BT_OK, BT_NONE);
        }
}

void blankLine(short y) {
        short i;
        for (i = max(y - 1, 0); i < y + 8; i++)
                DrawLine(0, i, scrw, i, A_REVERSE);
}

unsigned short printSaying(char* sentence, unsigned short pos) {
        unsigned char x = TXT_LEFT, y = TXT_TOP, bottom = TXT_BOTTOM;
        unsigned short wordLen;
        unsigned short lineWid = (TXT_RIGHT - TXT_LEFT) / 6;
        char wordBuff[lineWid + 1];
        BOOL spaceSep;
        
        for (y = TXT_TOP; y <= bottom; y += 8) blankLine(y);
        y = TXT_TOP; x = TXT_LEFT;

        while (sentence[pos] && (y <= TXT_BOTTOM && x <= TXT_RIGHT)) {
                if (sentence[pos] == '\n') {
                        x = TXT_LEFT;
                        y += 8;
                        pos++;
                } else {
                        wordLen = min(strcspn(&sentence[pos], " -\n"), lineWid - 1);
                        spaceSep = FALSE;
                        switch (sentence[pos + wordLen]) {
                                case ' ':
                                        spaceSep = TRUE;
                                        break;
                                case '\n':
                                case '\0':
                                        wordLen--;
                        }
                        if (x + ((wordLen + (spaceSep?0:1)) * 6) > TXT_RIGHT) {
                                if (x == TXT_LEFT) {
                                        wordLen = lineWid;
                                } else {
                                        x = TXT_LEFT;
                                        y += 8;
                                }
                        }
                        if (y <= TXT_BOTTOM) {
                                strncpy(wordBuff, &sentence[pos], wordLen + 1);
                                wordBuff[wordLen + 1] = 0;
                                DrawStr(x, y, wordBuff, A_NORMAL);
                                x += (wordLen + 1) * 6;
                                if (x > TXT_RIGHT) {
                                        x = TXT_LEFT;
                                        y += 8;
                                }
                                pos += wordLen + 1;
                        }
                }
        }

        /* Next sentence position is where we leave off, or, if end of complete
         * saying was printed, loops back to the beginning */
        return sentence[pos] ? pos : 0;
}

void sayingsUI(void) {
        enum STATUS {IDLE, REDISPLAY, GENERATE_SAYING, QUIT};
        BOOL justStarted = TRUE;
        unsigned short status = GENERATE_SAYING;
        unsigned short currDispPos = 0;
        char headerText[40];
        char* sent = NULL;
        
        initCompat();
        
        sent = malloc(SENTENCE_ALLOC_SIZE * sizeof(char));
        if (!sent) {
                DlgMessage("Error", "Insufficient RAM for sentence generation", BT_OK, BT_NONE);
                return;
        }
        
        while (status != QUIT) {
                // Generate saying
                if (status == GENERATE_SAYING) {
                        sprintsaying(headerText, "Saying ", CurrentSaying);
                        setSaying(CurrentSaying);
                        sent[0] = 0;
                        goNikky(sent, &rootTable);
                        currDispPos = 0;
                        status = REDISPLAY;
                }

                // Print saying
                if (status == REDISPLAY) {
                        // Header
                        ClrScr();
                        FontSetSys(F_6x8);
                        DrawLine(0, scrh - 7, scrw - 1, scrh - 7, A_NORMAL);
                        DrawLine(0, 10, scrw - 1, 10, A_NORMAL);
                        DrawLine(0, scrh - 17, scrw - 1, scrh - 17, A_NORMAL);
                        blankLine(HEADER_TOP);
                        DrawStr((scrw / 2 - strlen(headerText) * 6 / 2),
                                HEADER_TOP, headerText, A_NORMAL);
                        
                        // Saying
                        currDispPos = printSaying(sent, currDispPos);
                        
                        // Footer
                        if (!currDispPos) {
                                DrawStr(4, TXT_FOOTER, "Help", A_NORMAL);
                                DrawStr(35, TXT_FOOTER, "Bkmk", A_NORMAL);
                                DrawStr(67, TXT_FOOTER, calc?"FNxt":"Find", A_NORMAL);
                                DrawStr(99, TXT_FOOTER, "Rand", A_NORMAL);
                                DrawStr(131, TXT_FOOTER, "Goto", A_NORMAL);
                                DrawLine(0, TXT_FOOTER - 1, 0, TXT_FOOTER + 8, A_NORMAL);
                                DrawLine(31, TXT_FOOTER - 1, 31, TXT_FOOTER + 8, A_NORMAL);
                                DrawLine(63, TXT_FOOTER - 1, 63, TXT_FOOTER + 8, A_NORMAL);
                                DrawLine(95, TXT_FOOTER - 1, 95, TXT_FOOTER + 8, A_NORMAL);
                                DrawLine(127, TXT_FOOTER - 1, 127, TXT_FOOTER + 8, A_NORMAL);
                                DrawLine(159, TXT_FOOTER - 1, 159, TXT_FOOTER + 8, A_NORMAL);
                                if (calc) {
                                        DrawStr(163, TXT_FOOTER, "Abt", A_NORMAL);
                                        DrawStr(188, TXT_FOOTER, "RNG", A_NORMAL);
                                        DrawStr(213, TXT_FOOTER, "Find", A_NORMAL);
                                        DrawLine(184, TXT_FOOTER - 1, 184, TXT_FOOTER + 8, A_NORMAL);
                                        DrawLine(210, TXT_FOOTER - 1, 210, TXT_FOOTER + 8, A_NORMAL);
                                        DrawLine(239, TXT_FOOTER - 1, 239, TXT_FOOTER + 8, A_NORMAL);

                                }
                        } else {
                                DrawStr(TXT_LEFT, TXT_FOOTER, "\x18 ENTER to page \x18", A_NORMAL);
                        }
                        
                        // Intro message
                        if (justStarted)
                                ST_helpMsg(COMMENT_PROGRAM_NAME " "
                                        COMMENT_VERSION_STRING " | F1 = Help");
                                
                        justStarted = FALSE;
                        status = IDLE;
                }

                ST_busy(ST_IDLE);
                short k = ngetchx();
                if (k == KEY_ESC || k == KEY_QUIT) status = QUIT;
                else if (k == KUP) {
                        CurrentSaying.x += 1;
                        status = GENERATE_SAYING;
                } else if (k == KDOWN) {
                        CurrentSaying.x -= 1;
                        status = GENERATE_SAYING;
                } else if (k == KLEFT) {
                        CurrentSaying.y -= 1;
                        if (CurrentSaying.y > MAX_Y_SAYING)
                                CurrentSaying.y = MAX_Y_SAYING;
                        status = GENERATE_SAYING;
                } else if (k == KRIGHT) {
                        CurrentSaying.y += 1;
                        if (CurrentSaying.y > MAX_Y_SAYING)
                                CurrentSaying.y = 0;
                        status = GENERATE_SAYING;
                } else if (k == KEY_F1) {
                        strcpy(sent, helpText);
                        strcpy(headerText, "Key help");
                        currDispPos = 0;
                        status = REDISPLAY;
                } else if (k == KEY_F2) {
                        manageBookmarks();
                        status = GENERATE_SAYING;
                } else if (k == KEY_F3) {
                        search(FALSE, sent);
                        status = GENERATE_SAYING;
                } else if (k == KEY_F8) {
                        search(TRUE, sent);
                        status = GENERATE_SAYING;
                } else if (k == KEY_F4) {
                        CurrentSaying.rngMode = MTWISTER;
                        /* MTWISTER generates full 32-bit random number for
                         * CurrentSaying.x */
                        
                        randInit(FiftyMsecTick);
                        
                        CurrentSaying.x = randNext();
                        CurrentSaying.y = randNextRange(MAX_Y_SAYING + 1);
                        CurrentSaying.rngMode = randNextRange(2);
                        
                        status = GENERATE_SAYING;
                } else if (k == KEY_F5) {
                        gotoSaying();
                        status = GENERATE_SAYING;
                } else if (k == KEY_F6) {
                        strcpy(sent, aboutText);
                        strcpy(headerText, "About");
                        currDispPos = 0;
                        status = REDISPLAY;
                } else if (k == KEY_F7) {
                        CurrentSaying.rngMode = !CurrentSaying.rngMode;
                        status = GENERATE_SAYING;
                } else if (k == KEY_STO) {
                        addBookmark(sent);
                } else if (k == KCUT) {
                        // Copy current saying to clipboard
                        BOOL success = FALSE;
                        char *newClip;
                        unsigned long newClipLen;
                        HANDLE hNewClip;
                        
                        newClipLen = strlen(sent) + 26;
                        hNewClip = HeapAlloc(sizeof(char) * newClipLen);
                        if (hNewClip) {
                                newClip = HeapDeref(hNewClip);
                                if (newClip) {
                                        sprintsaying(newClip, "", CurrentSaying);
                                        strcat(newClip, ": ");
                                        strcat(newClip, sent);
                                        if (CB_replaceTEXT(newClip, strlen(newClip), FALSE))
                                                success = TRUE;
                                        HeapFree(hNewClip);
                                }
                        }
                        if (!success)
                                DlgMessage("Error", "Clipboard operation failed (low RAM?)", BT_OK, BT_NONE);
                } else if (k == KCOPY) {
                        // Append current saying to clipboard
                        BOOL success = FALSE;
                        const char *clip;
                        char *newClip;
                        unsigned long clipLen = 0, newClipLen;
                        HANDLE hNewClip, hClip;
                        
                        CB_fetchTEXT(&hClip, &clipLen);
                        if (hClip) {
                                newClipLen = clipLen + strlen(sent) + 27;
                                                // Leave some extra space for saying #
                                hNewClip = HeapAlloc(sizeof(char) * newClipLen);
                                if (hNewClip) {
                                        newClip = HeapDeref(hNewClip);
                                        clip = HeapDeref(hClip);
                                        if (newClip && clip) {
                                                memcpy(newClip, clip, sizeof(char) * clipLen);
                                                sprintsaying(&newClip[clipLen], "\r", CurrentSaying);
                                                strcat(newClip, ": ");
                                                strcat(newClip, sent);
                                                if (CB_replaceTEXT(newClip, strlen(newClip), FALSE))
                                                        success = TRUE;
                                                HeapFree(hNewClip);
                                        }
                                }
                        }
                        if (!success)
                                DlgMessage("Error", "Clipboard operation failed (low RAM?)", BT_OK, BT_NONE);
                } else if (k == KEY_ENTER) {
                        status = REDISPLAY;
                }
        }
        if (sent) free(sent);
        ST_busy(ST_BUSY);
        OSClearBreak();
}
