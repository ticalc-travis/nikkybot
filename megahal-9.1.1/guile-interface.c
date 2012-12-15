/*
 * MegaHal Guile interface
 *
 * copyleft 2k2 aNa|0Gue
 *              <analogue@glop.org>
 *              http://www.glop.org/
 *
 * In order to use it in your guile script, you need to add the 2 following lines:
 *
 * (define megahal-lib (dynamic-link "/path/to/libguilemegahal.so"))
 * (dynamic-call 'init_megahal megahal-lib)
 *
 * Availables primitives are:
 *
 *          (megahal-set-no-prompt)
 *          (megahal-set-no-wrap)
 *          (megahal-set-no-banner)
 *          (megahal-initialize)
 *   string (megahal-initial-greeting)
 *  boolean (megahal-command string)
 *   string (megahal-do-reply string)
 *          (megahal-cleanup)
 *
 */

#include "megahal.h"
#include <guile/gh.h>

SCM MH_setnoprompt()
{
    megahal_setnoprompt();
    return SCM_UNSPECIFIED;
}

SCM MH_setnowrap()
{
    megahal_setnowrap();
    return SCM_UNSPECIFIED;
}

SCM MH_setnobanner()
{
    megahal_setnobanner();
    return SCM_UNSPECIFIED;
}

SCM MH_initialize()
{
    megahal_initialize();
    return SCM_UNSPECIFIED;
}

SCM MH_initial_greeting()
{
    return gh_str02scm(megahal_initial_greeting());
}

SCM MH_command(SCM input)
{
    if ( megahal_command(gh_scm2newstr(input, NULL)) )
        return SCM_BOOL_T;
    else
        return SCM_BOOL_F;
}

SCM MH_do_reply(SCM input)
{
    return gh_str02scm(megahal_do_reply(gh_scm2newstr(input, NULL), 0));
}

SCM MH_cleanup()
{
    megahal_cleanup();
    return SCM_UNSPECIFIED;
}

void init_megahal ()
{
    gh_new_procedure("megahal-set-no-prompt",   MH_setnoprompt, 0, 0, 0);
    gh_new_procedure("megahal-set-no-wrap",     MH_setnowrap, 0, 0, 0);
    gh_new_procedure("megahal-set-no-banner",   MH_setnobanner, 0, 0, 0);
    gh_new_procedure("megahal-initialize",      MH_initialize, 0, 0, 0);
    gh_new_procedure("megahal-initial-greeting",MH_initial_greeting, 0, 0, 0);
    gh_new_procedure("megahal-command",         MH_command, 1, 1, 0);
    gh_new_procedure("megahal-do-reply",        MH_do_reply, 1, 1, 0);
    gh_new_procedure("megahal-cleanup",         MH_cleanup, 0, 0, 0);
}
