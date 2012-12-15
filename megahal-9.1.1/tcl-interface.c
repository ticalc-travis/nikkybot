/* $Id: tcl-interface.c,v 1.6 2004/01/13 10:59:20 lfousse Exp $ */
/* MegHAL Tcl interface, by David N. Welton <davidw@dedasys.com> */

#include <tcl.h>
#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
#include "megahal.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

Tcl_Interp *interp;

void saveandexit(int);

void saveandexit(int sig)
{
    megahal_cleanup();
    exit(1);
}

int Mh_Init(ClientData clientData, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[])
{
    megahal_initialize();

    return TCL_OK;
}

int Mh_DoReply(ClientData clientData, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[])
{

    char *input;
    char *output=NULL;

    if (objc != 2)
    {
	Tcl_WrongNumArgs(interp, 1, objv, "need reply");
	return TCL_ERROR;
    }
    input = Tcl_GetStringFromObj (objv[1], (int *)NULL);

    output = megahal_do_reply(input, 1);

    Tcl_SetObjResult(interp, Tcl_NewStringObj(output, -1));
    return TCL_OK;
}

int Mh_Cleanup(ClientData clientData, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[])
{
    megahal_cleanup();
    return TCL_OK;
}

int Mh_tcl_Init(Tcl_Interp *interp)
{
    Tcl_CreateObjCommand(interp, "mh_init", Mh_Init,
		      (ClientData) NULL, (Tcl_CmdDeleteProc *) NULL);
    Tcl_CreateObjCommand(interp, "mh_doreply", Mh_DoReply,
		      (ClientData) NULL, (Tcl_CmdDeleteProc *) NULL);
    Tcl_CreateObjCommand(interp, "mh_cleanup", Mh_Cleanup,
		      (ClientData) NULL, (Tcl_CmdDeleteProc *) NULL);
    Tcl_PkgProvide(interp, "Megahal", "1.0");
    return TCL_OK;
}
