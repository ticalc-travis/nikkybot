#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <getopt.h>
#if !defined(AMIGA) && !defined(__mac_os)
#include <malloc.h>
#endif
#include <string.h>
#include <signal.h>
#include <math.h>
#include <time.h>
#include <ctype.h>
#if defined(__mac_os)
#include <types.h>
#include <Speech.h>
#else
#include <sys/types.h>
#endif
#include "megahal.h"
#if defined(DEBUG)
#include "debug.h"
#endif

#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>


/* extern errorfp;
extern statusfp;
  */
/* extern noprompt;
extern nowrap;
extern nobanner;
extern typing_delay;
extern speech;
extern quiet;
  */
static struct option long_options[] = {
    {"no-prompt", 0, NULL, 'p'},
    {"no-wrap", 0, NULL, 'w'},
    {"no-banner", 0, NULL, 'b'},
    {"help", 0, NULL, 'h'},
    {"no-greeting", 0, NULL, 'g'},
    {"directory", 1, NULL, 'd'},
    {0, 0, 0, 0}
};

void usage()
{
    puts("usage: megahal [-[pqrgwbh]]\n" \
	 "\t-h : show usage\n" \
	 "\t-p : inhibit prompts\n" \
	 "\t-q : quiet mode (no replies) enabled at start\n" \
	 "\t-r : inhibit progress display\n" \
	 "\t-g : inhibit initial greeting\n" \
	 "\t-b : inhibit banner display at startup\n" \
         "\t-d : sets the directory where your megahal files are\n");
}

/*===========================================================================*/

/*
 *		Function:	Main
 *
 *		Purpose:		Initialise everything, and then do an infinite loop.  In
 *						the loop, we read the user's input and reply to it, and
 *						do some housekeeping task such as responding to special
 *						commands.
 */
int main(int argc, char **argv)
{
    char *input=NULL;
    char *output=NULL;
    char *my_directory = NULL;
    int directory_set;
    int c, option_index = 0;
    
    directory_set = 0;

    while(1) {
	if((c = getopt_long(argc, argv, "hpwbgd:", long_options,
			    &option_index)) == -1)
	    break;
	switch(c) {
	case 'p':
	    megahal_setnoprompt();
	    break;
	case 'w':
	    megahal_setnowrap();
	    break;
        case 'd':
            megahal_setdirectory (optarg);
            directory_set = 1;
            break;
	case 'b':
	    megahal_setnobanner();
	    break;
    case 'g':
        megahal_setnogreeting();
        break;
	case 'h':
	    usage();
	    return 0;
	}
    }

    if (directory_set == 0)
    {
        if ((my_directory = getenv("MEGAHAL_DIR")))
        {
            megahal_setdirectory (my_directory);
            directory_set = 1;
        }
        else
        {
            struct stat dir_stat;

            my_directory = getenv ("HOME");
            if (my_directory == NULL)
            {
                fprintf (stderr, "Cannot find your home directory.\n");
                exit (1);
            }
            my_directory = malloc (12 + strlen (my_directory));
            strcpy (my_directory, getenv ("HOME"));
            strcat (my_directory, "/.megahal");
            if (stat (my_directory, &dir_stat))
            {
                if (errno == ENOENT)
                {
                    directory_set = mkdir (my_directory, S_IRWXU);
                    if (directory_set != 0)
                    {
                        fprintf (stderr, "Could not create %s.\n", 
                                 my_directory);
                        exit (1);
                    }
                    megahal_setdirectory (my_directory);
                    directory_set = 1;
                }
            }
            else
            {
                if (S_ISDIR(dir_stat.st_mode))
                {
                    megahal_setdirectory (my_directory);
                    directory_set = 1;
                }
                else
                {
                    fprintf (stderr, "Could not use megahal directory %s.\n", 
                             my_directory);
                    exit (1);
                }
            }
        }
    }
	
    /*
     *		Do some initialisation 
     */
    megahal_initialize();
    
	
    /*
     *		Create a dictionary which will be used to hold the segmented
     *		version of the user's input.
     */

    /*
     *		Load the default MegaHAL personality.
     */
    output = megahal_initial_greeting();
    megahal_output(output);
    /*
     *		Read input, formulate a reply and display it as output
     */
    while(1) {

	input = megahal_input("> ");
	
	/*
	 *		If the input was a command, then execute it
	 */

	if (megahal_command(input) != 0)
	    continue;

	output = megahal_do_reply(input, 1);

	megahal_output(output);
    }

    megahal_cleanup();
    exit(0);
}
