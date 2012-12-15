#include "EXTERN.h"
#include "perl.h"
#include "XSUB.h"

#include "ppport.h"

#include <megahal.h>

#include "const-c.inc"

MODULE = Megahal		PACKAGE = Megahal		

INCLUDE: const-xs.inc

void
megahal_learn_no_reply(x, h)
	char *x
	int h
        PROTOTYPE: $$

void 
megahal_initialize();
        PROTOTYPE: 

void
megahal_cleanup();
        PROTOTYPE: 

char *
megahal_do_reply(x, h)
	char *x
	int h
        PROTOTYPE: $$
