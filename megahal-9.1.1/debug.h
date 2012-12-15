
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
 *		$Id: debug.h,v 1.1.1.1 2000/09/01 17:36:57 davidw Exp $
 *
 *		File:			debug.h
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

#define malloc(s)		my_malloc((s), __FILE__, __LINE__)
#define realloc(p,s)	my_realloc((p),(s), __FILE__, __LINE__)
#define free(p)		my_free((p), __FILE__, __LINE__)

extern void *my_malloc(size_t, char *, int);
extern void *my_realloc(void *ptr, size_t, char *, int);
extern void my_free(void *, char *, int);
extern bool isValidPointer(void *, char *, int);
extern unsigned long MemoryCount(void);

/*===========================================================================*/

/*
 *		$Log: debug.h,v $
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

