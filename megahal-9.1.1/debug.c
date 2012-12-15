
/*===========================================================================*/

/*
 *  Copyright (C) 1998 Jason Hutchens
 *
 *  This program is free software; you can redistribute it and/or modify it
 *  under the terms of the GNU General Public License as published by the Free
 *  Software Foundation; either version 2 of the license or (at your option)
 *  any later version.
 *
 *  This program is distributed in the hope that it will be useful, but
 *  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 *  or FITNESS FOR A PARTICULAR PURPOSE.  See the Gnu Public License for more
 *  details.
 *
 *  You should have received a copy of the GNU General Public License along
 *  with this program; if not, write to the Free Software Foundation, Inc.,
 *  675 Mass Ave, Cambridge, MA 02139, USA.
 */

/*===========================================================================*/

/*
 *		$Id: debug.c,v 1.1.1.1 2000/09/01 17:36:57 davidw Exp $
 *
 *		File:			debug.c
 *
 *		Program:		MegaHAL v8r5
 *
 *		Purpose:		Memory debugging functions for the MegaHAL project.
 *
 *		Author:		Mr. Paul Baxter.
 *
 *		WWW:			http://ciips.ee.uwa.edu.au/~hutch/hal/
 *
 *		E-Mail:		pbaxter@assistivetech.com
 *
 *		Notes:		This file is best viewed with tabstops set to three spaces.
 */

/*===========================================================================*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if !defined(AMIGA) && !defined(__mac_os)
#include <malloc.h>
#endif
#include "megahal.h"

/*===========================================================================*/

#ifdef malloc
#undef malloc
#endif

#ifdef realloc
#undef realloc
#endif

#ifdef free
#undef free
#endif

#define kStartSigniture		0xABCD
#define kEndSigniture		0xDEADBEEF
#define kExtraBytes			(sizeof(BYTE2) + sizeof(BYTE4) + sizeof(size_t))

/*===========================================================================*/

void *my_malloc(size_t, char *, int);
void *my_realloc(void *ptr, size_t, char *, int);
void my_free(void *, char *, int);
bool isValidPointer(void *, char *, int);
unsigned long MemoryCount(void);

/*===========================================================================*/

static long mallocscalled = 0;
static long freescalled = 0;
static long reallocscalled = 0;

/*===========================================================================*/

/*
 *              Function:       my_malloc
 *
 *              Purpose:          emulate malloc plus check memory allocation for debug.
 */
void*  my_malloc(size_t size, char* file, int line)
{
#pragma unused(file, line)

	char *newptr;

	mallocscalled++;
	newptr = malloc(size + kExtraBytes);
	if (newptr) {
									// start signiture
		*((BYTE2*)newptr) = kStartSigniture; 
		newptr += sizeof(BYTE2);
									// store length of ptr
		memcpy(newptr, &size, sizeof(size_t));
		newptr += sizeof(size_t);
		memset(newptr, 0xFF, size);	// make sure not 0
									// end signiture
		*((BYTE4*)&newptr[size]) = kEndSigniture; 
	}
	return newptr;
}

/*---------------------------------------------------------------------------*/

/*
 *              Function:       my_realloc
 *
 *              Purpose:          emulate realloc plus check memory 
allocation for debug.
 */
void*  my_realloc(void* ptr, size_t size, char* file, int line)
{
	char* newptr;

	reallocscalled++;

	if (!isValidPointer(ptr, file, line)) {
		printf("\nrealloc MEM overwrite: FILE %s LINE %d\n[mallocs %ld] [frees %ld] [reallocs %ld]\n",
				file, line, mallocscalled, freescalled, reallocscalled);
		exit(1);
	}

	newptr = ((char*)ptr) - sizeof(BYTE2) - sizeof(size_t);
	newptr = realloc(newptr, size + kExtraBytes);
	if (newptr) {
									// start signiture
		*((BYTE2*)newptr) = kStartSigniture; 
		newptr += sizeof(BYTE2);
									// store length of ptr
		memcpy(newptr, &size, sizeof(size_t));
		newptr += sizeof(size_t);
									// end signiture
		*((BYTE4*)&newptr[size]) = kEndSigniture; 
	}
	return newptr;
}

/*---------------------------------------------------------------------------*/

/*
 *              Function:       my_free
 *              Purpose:          emulate free plus check memory 
allocation for debug.
 */
void my_free(void* ptr, char*file, int line)
{
	char* newptr;
	size_t ptrsize;

	freescalled++;
	if (!isValidPointer(ptr, file, line)) {
		printf("\nfree MEM overwrite: FILE %s LINE %d\n[mallocs %ld] [frees %ld] [reallocs %ld]\n",
				file, line, mallocscalled, freescalled, reallocscalled);
		exit(1);
	}
	newptr = ((char*)ptr) - sizeof(BYTE2) - sizeof(size_t);	// real start
	ptrsize = *((size_t*)&newptr[sizeof(BYTE2)]);			// size of pointer
	memset(ptr, 0xFF, ptrsize);		// make sure mem is changed
	free(newptr);
	return;
}

/*---------------------------------------------------------------------------*/

/*
 *              Function:       isValidPointer
 *              Purpose:          check to see is a pointer is valid.
 */
bool isValidPointer(void* ptr, char* file, int line)
{
	char* newptr;
	size_t ptrsize;
	
	newptr = ((char*)ptr) - sizeof(BYTE2) - sizeof(size_t);	// real start
	ptrsize = *((size_t*)&newptr[sizeof(BYTE2)]);			// size of pointer

	if (*((BYTE2*)newptr) != kStartSigniture) {
		printf("\nisValidPointer MEM overwrite: FILE %s LINE %d\n[mallocs %ld] [frees %ld] [reallocs %ld]\n",
				file, line, mallocscalled, freescalled, reallocscalled);
		return FALSE;
	}
	newptr += sizeof(BYTE2) + sizeof(size_t) + ptrsize;
	if ((*(BYTE4*)newptr) != kEndSigniture) {
		printf("\nisValidPointer MEM overwrite: FILE %s LINE %d\n[mallocs %ld] [frees %ld] [reallocs %ld]\n",
				file, line, mallocscalled, freescalled, reallocscalled);
		return FALSE;
	}
	return TRUE;
}

/*---------------------------------------------------------------------------*/

/*
 *              Function:       MemoryCount
 *              Purpose:          check count of malloc vs frees.
 */
unsigned long MemoryCount(void)
{
	return mallocscalled - freescalled;
}

/*===========================================================================*/

/*
 *		$Log: debug.c,v $
 *		Revision 1.1.1.1  2000/09/01 17:36:57  davidw
 *		Imported sources
 *		
 *		Revision 1.2  1998/04/21 10:10:56  hutch
 *		Fixed a few little errors.
 *
 *		Revision 1.1  1998/04/06 08:02:01  hutch
 *		Initial revision
 */

/*===========================================================================*/

