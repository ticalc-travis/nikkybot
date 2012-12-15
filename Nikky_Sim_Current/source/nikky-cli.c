
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#include "nikky-cli.h"
#include "vocab.h"
#include "generate.h"

SAYING parseSayingNumber(char *sayingStr) {
    char* c;
    uint64_t x, y;
    SAYING s;
    
    x = strtoul(sayingStr, NULL, 10);
    c = strchr(sayingStr, '-');
    y = c ? strtoul(c + 1, NULL, 10) : 0;
    
    if (x > UINT32_MAX) x = UINT32_MAX;
    if (y > MAX_Y_SAYING) y = MAX_Y_SAYING;
    
    s.x = x;
    s.y = y;
    return s;
}

int main(int argc, char *argv[]) {
    char sentence[SENTENCE_ALLOC_SIZE];
    SAYING sayStart, sayEnd, sayCurrent;
    uint64_t x, y;
    
    if (argc == 1 || argc > 3) {
        printf("Usage: %s saying1 [saying2]\n"
               "Generate and print saying number 'saying1'\n"
               "If 'saying2' is specified, print sayings 'saying1' to 'saying2',\n"
               "one per line\n"
               "\nSaying numbers are of the form ###-###.  Examples:\n"
               "1234-567     777-0     0-777     555666 (interpreted as \"555666-0\")\n\n"
               "Saying numbers range from 0-0 to %u-%u.\n"
               "This utility only supports the Mersenne Twister PRNG "
               "(\"B\" sayings).\n\n",
               argv[0], UINT32_MAX, MAX_Y_SAYING);
        return 1;
    }
    
    sayStart = parseSayingNumber(argv[1]);
    if (argc == 3)
        sayEnd = parseSayingNumber(argv[2]);
    else
        sayEnd = sayStart;
    
    for (y = sayStart.y; y <= sayEnd.y; y++) {
        for (x = sayStart.x; x <= sayEnd.x; x++) {
            sentence[0] = 0;
            sayCurrent.x = x;
            sayCurrent.y = y;
            setSaying(sayCurrent);
            goNikky(sentence, &rootTable);
            printf("#B-%u-%u: %s\n", sayCurrent.x, sayCurrent.y, sentence);
        }
    }
    
    return 0;
}