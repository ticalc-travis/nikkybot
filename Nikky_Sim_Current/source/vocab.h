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

#ifndef __vocab_h__
#define __vocab_h__

enum TABLE_TYPES { SEQUENCE, RANDOM, VOCABULARY };

typedef struct { const void* foo; unsigned char bar:1, baz:7; } blah;

typedef struct {
        const void* target;
        unsigned char capitalize:1, probability:7;
                /* capitalize only applies to SEQUENCE and RANDOM; ignored for
                 * VOCABULARY tables */
} TABLE_ENTRY;

typedef struct {
        unsigned char type;
        TABLE_ENTRY entries[];
} TABLE;

uint16_t tableLen(const TABLE *);

#define VOCAB_TABLE(name) static const TABLE name = { VOCABULARY, {
#define SEQ_TABLE(name) static const TABLE name = { SEQUENCE, {
#define RAND_TABLE(name) static const TABLE name = { RANDOM, {
#define ENTRY(string, cap, prob) { string, cap, prob },
#define TABLE_END { NULL, 0, 0 } } };

#define SPACE { &space, 0, 127 },
#define COMMA { &comma, 0, 127 },
#define HYPHEN { &hyphen, 0, 127 },
#define PUNCT { &punct, 0, 127 },
#define INTERPUNCT { &interPunct, 0, 127 },
#define APOSTROPHE { &apostrophe, 0, 127 },
#define APOSTROPHES { &apostropheS, 0, 127 },

/* Declarations for tables that need prototyping due to circular linking or
 * organizational reasons and such */
static const TABLE transVerbPlur;
static const TABLE adjectivePhrase;
static const TABLE nounPhrase;
static const TABLE anySingNoun;
static const TABLE plurVerbPhrase;
static const TABLE declaratorySentence;
static const TABLE address;
static const TABLE intBooleanPhrase;

#include "words.inc"

VOCAB_TABLE(comma)
        ENTRY(",", 0, 127)
TABLE_END

VOCAB_TABLE(space)
        ENTRY(" ", 0, 127)
TABLE_END

VOCAB_TABLE(hyphen)
        ENTRY("-", 0, 127)
TABLE_END

VOCAB_TABLE(interPunct)
        ENTRY("? ", 0, 127)
        ENTRY("?! ", 0, 8)
#ifdef CLI_PC_BUILD
        ENTRY("...", 0, 8)
#else
        ENTRY("\xA0 ", 0, 8)
#endif
TABLE_END

VOCAB_TABLE(punct)
        ENTRY(". ", 0, 127)
        ENTRY("! ", 0, 32)
        ENTRY("? ", 0, 8)
#ifdef CLI_PC_BUILD
        ENTRY("...", 0, 8)
#else
        ENTRY("\xA0 ", 0, 8)
#endif
TABLE_END

VOCAB_TABLE(a)
        ENTRY("a", 0, 127)
TABLE_END

VOCAB_TABLE(an)
        ENTRY("an", 0, 127)
TABLE_END

VOCAB_TABLE(apostropheS)
        ENTRY("'s", 0, 127)
TABLE_END

VOCAB_TABLE(apostrophe)
        ENTRY("'", 0, 127)
TABLE_END

VOCAB_TABLE(is)
        ENTRY("is ", 0, 127)
        ENTRY("isn't ", 0, 127)
        ENTRY("is not ", 0, 16)
TABLE_END

VOCAB_TABLE(are)
        ENTRY("are ", 0, 127)
        ENTRY("aren't ", 0, 127)
        ENTRY("are not ", 0, 16)
TABLE_END

VOCAB_TABLE(am)
        ENTRY(" am ", 0, 127)
        ENTRY(" am not ", 0, 16)
        ENTRY(" ain't ", 0, 32)
        ENTRY("'m ", 0, 127)
TABLE_END

VOCAB_TABLE(I)
        ENTRY("I", 0, 127)
TABLE_END

VOCAB_TABLE(me)
        ENTRY("me", 0, 127)
TABLE_END

VOCAB_TABLE(myself)
        ENTRY("myself", 0, 127)
TABLE_END

VOCAB_TABLE(us)
        ENTRY("us", 0, 127)
TABLE_END

VOCAB_TABLE(you)
        ENTRY("you ", 0, 127)
TABLE_END

VOCAB_TABLE(yourself)
        ENTRY("yourself", 0, 127)
TABLE_END

VOCAB_TABLE(whoWhat)
        ENTRY("who ", 0, 127)
        ENTRY("what ", 0, 127)
TABLE_END

VOCAB_TABLE(howMany)
        ENTRY("how many ", 0, 127)
        ENTRY("how many more ", 0, 127)
        ENTRY("how many fewer ", 0, 127)
TABLE_END

VOCAB_TABLE(which)
        ENTRY("which ", 0, 127)
TABLE_END

VOCAB_TABLE(whenWhereWhyHow)
        ENTRY("when ", 0, 127)
        ENTRY("where ", 0, 127)
        ENTRY("why ", 0, 127)
        ENTRY("how ", 0, 127)
TABLE_END



/* Adjective phrase */

SEQ_TABLE(threeAdjectives)
        ENTRY(&vocAdjective, 0, 127)
        COMMA
        SPACE
        ENTRY(&vocAdjective, 0, 127)
        COMMA
        SPACE
        ENTRY(&vocListConjunction, 0, 127)
        SPACE
        ENTRY(&vocAdjective, 0, 127)
TABLE_END

SEQ_TABLE(twoAdjectives)
        ENTRY(&vocAdjective, 0, 127)
        SPACE
        ENTRY(&vocListConjunction, 0, 127)
        SPACE
        ENTRY(&vocAdjective, 0, 127)
TABLE_END

SEQ_TABLE(hyphenatedAdjective)
        ENTRY(&adjectivePhrase, 0, 64)
        ENTRY(&anySingNoun, 0, 127)
        HYPHEN
TABLE_END

RAND_TABLE(doAdjectivePhrase)
        ENTRY(&vocAdjective, 0, 127)
        ENTRY(&twoAdjectives, 0, 16)
        ENTRY(&threeAdjectives, 0, 8)
TABLE_END

SEQ_TABLE(adjectivePhraseSpace)
        ENTRY(&doAdjectivePhrase, 0, 127)
        SPACE
TABLE_END
        
RAND_TABLE(adjectivePhrase)
        ENTRY(&adjectivePhraseSpace, 0, 127)
        ENTRY(&hyphenatedAdjective, 0, 16)
TABLE_END



/* Plural noun phrase */

RAND_TABLE(anyPlurNoun)
        ENTRY(&vocPlurNounNodeterm, 0, 127)
        ENTRY(&vocPlurPropNoun, 0, 32)
TABLE_END

SEQ_TABLE(numDeterm012)
        ENTRY(&vocNumDeterm0, 0, 127)
        SPACE
        ENTRY(&vocNumDeterm1, 0, 127)
        SPACE
        ENTRY(&vocNumDeterm2, 0 ,127)
TABLE_END

SEQ_TABLE(numDeterm12)
        ENTRY(&vocNumDeterm1, 0, 127)
        SPACE
        ENTRY(&vocNumDeterm2, 0, 127)
TABLE_END

SEQ_TABLE(numDeterm01)
        ENTRY(&vocNumDeterm0, 0, 127)
        SPACE
        ENTRY(&vocNumDeterm1, 0, 127)
TABLE_END

RAND_TABLE(plurNumDeterm)
        ENTRY(&vocNumDeterm1, 0, 127)
        ENTRY(&numDeterm01, 0, 64)
        ENTRY(&numDeterm12, 0, 64)
        ENTRY(&numDeterm012, 0, 64)
TABLE_END

RAND_TABLE(plurDeterm)
        ENTRY(&vocPlurDeterm, 0, 127)
        ENTRY(&plurNumDeterm, 0, 64)
TABLE_END

SEQ_TABLE(plurNounDetermPhrase)
        ENTRY(&plurDeterm, 0, 127)
        SPACE
        ENTRY(&adjectivePhrase, 0, 16)
        ENTRY(&vocPlurNoun, 0, 127)
TABLE_END

SEQ_TABLE(plurPropNoun)
        ENTRY(&adjectivePhrase, 0, 8)
        ENTRY(&vocPlurPropNoun, 0, 127)
TABLE_END

SEQ_TABLE(plurNounNodetermPhrase)
        ENTRY(&adjectivePhrase, 0, 16)
        ENTRY(&vocPlurNounNodeterm, 0, 127)
TABLE_END

RAND_TABLE(plurNounPhrase)
        ENTRY(&plurNounDetermPhrase, 0, 32)
        ENTRY(&plurNounNodetermPhrase, 0, 127)
        ENTRY(&plurPropNoun, 0, 16)
TABLE_END



/* Singular noun phrase */

RAND_TABLE(anySingNoun)
        ENTRY(&vocSingNounA, 0, 127)
        ENTRY(&vocSingNounAn, 0, 127)
        ENTRY(&vocSingNounNodeterm, 0, 127)
        ENTRY(&vocSingPropNoun, 0, 32)
TABLE_END

RAND_TABLE(singNounDeterm)
        ENTRY(&vocSingDeterm, 0, 127)
        ENTRY(&vocSingDetermNonum, 0, 127)
TABLE_END

RAND_TABLE(singNounDetermAn)
        ENTRY(&an, 0, 24)
        ENTRY(&singNounDeterm, 0, 127)
TABLE_END

RAND_TABLE(singNounDetermA)
        ENTRY(&a, 0, 24)
        ENTRY(&singNounDeterm, 0, 127)
TABLE_END

SEQ_TABLE(singNounAnPhrase)
        ENTRY(&singNounDetermAn, 0, 127)
        SPACE
        ENTRY(&vocSingNounAn, 0, 127)
TABLE_END

SEQ_TABLE(singNounAPhrase)
        ENTRY(&singNounDetermA, 0, 127)
        SPACE
        ENTRY(&vocSingNounA, 0, 127)
TABLE_END

SEQ_TABLE(singNounNodetermPhrase)
        ENTRY(&adjectivePhrase, 0, 32)
        ENTRY(&vocSingNounNodeterm, 0, 127)
TABLE_END

SEQ_TABLE(singPropNoun)
        ENTRY(&adjectivePhrase, 0, 8)
        ENTRY(&vocSingPropNoun, 0, 127)
TABLE_END

RAND_TABLE(singNounPhrase)
        ENTRY(&singNounAPhrase, 0, 127)
        ENTRY(&singNounAnPhrase, 0, 127)
        ENTRY(&singNounNodetermPhrase, 0, 127)
        ENTRY(&singPropNoun, 0, 48)
TABLE_END



/* Noun phrase */

SEQ_TABLE(singNounPhrasePossessive)
        ENTRY(&singNounPhrase, 0, 127)
        APOSTROPHES
        SPACE
        ENTRY(&adjectivePhrase, 0, 127)
        ENTRY(&anySingNoun, 0, 127)
TABLE_END

SEQ_TABLE(plurNounPhrasePossessive)
        ENTRY(&plurNounPhrase, 0, 127)
        APOSTROPHE
        SPACE
        ENTRY(&adjectivePhrase, 0, 32)
        ENTRY(&anyPlurNoun, 0, 127)
TABLE_END

RAND_TABLE(nounPhrase)
        ENTRY(&singNounPhrase, 0, 127)
        ENTRY(&plurNounPhrase, 0, 127)
        ENTRY(&singNounPhrasePossessive, 0, 32)
        ENTRY(&plurNounPhrasePossessive, 0, 32)
TABLE_END



/* Verb phrase */

SEQ_TABLE(adverbBefore)
        ENTRY(&vocAdverbBefore, 0, 127)
        SPACE
TABLE_END

SEQ_TABLE(adverbAfter)
        SPACE
        ENTRY(&vocAdverbAfter, 0, 127)
TABLE_END

RAND_TABLE(verbObject)
        ENTRY(&nounPhrase, 0, 127)
        ENTRY(&me, 0, 32)
        ENTRY(&us, 0, 32)
TABLE_END

SEQ_TABLE(auxVerbMainPProgTrans)
        ENTRY(&vocTransVerbPProg, 0, 127)
        SPACE
        ENTRY(&verbObject, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

SEQ_TABLE(intransVerbPProg)
        ENTRY(&vocIntransVerbPProg, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

RAND_TABLE(auxVerbMainPProg)
        ENTRY(&auxVerbMainPProgTrans, 0, 127)
        ENTRY(&vocIntransVerbPProg, 0, 127)
TABLE_END

SEQ_TABLE(intransVerbPlur)
        ENTRY(&adverbBefore, 0, 127)
        ENTRY(&vocIntransVerbPlur, 0, 127)
        ENTRY(&adverbAfter, 0, 127)
TABLE_END

SEQ_TABLE(transVerbPlur)
        ENTRY(&adverbBefore, 0, 32)
        ENTRY(&vocTransVerbPlur, 0, 127)
        SPACE
        ENTRY(&verbObject, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

SEQ_TABLE(intransVerbSing)
        ENTRY(&adverbBefore, 0, 32)
        ENTRY(&vocIntransVerbSing, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

SEQ_TABLE(transVerbSing)
        ENTRY(&adverbBefore, 0, 32) 
        ENTRY(&vocTransVerbSing, 0, 127)
        SPACE
        ENTRY(&verbObject, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

SEQ_TABLE(transVerbInf)
        ENTRY(&adverbBefore, 0, 32)
        ENTRY(&vocTransVerbInf, 0, 127)
        SPACE
        ENTRY(&verbObject, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

SEQ_TABLE(intransVerbInf)
        ENTRY(&adverbBefore, 0, 32)
        ENTRY(&vocTransVerbInf, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

RAND_TABLE(infVerbPhrase)
        ENTRY(&vocIntransVerbInf, 0, 127)
        ENTRY(&transVerbInf, 0, 127)
TABLE_END

SEQ_TABLE(singAuxVerbPhraseInf)
        ENTRY(&vocAuxVerbInf, 0, 127)
        SPACE
        ENTRY(&infVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(singAuxVerbPhrasePProg)
        ENTRY(&vocSingAuxVerbPProg, 0, 127)
        SPACE
        ENTRY(&auxVerbMainPProg, 0, 127)
TABLE_END

RAND_TABLE(singAuxVerbPhrase)
        ENTRY(&singAuxVerbPhraseInf, 0, 127)
        ENTRY(&singAuxVerbPhrasePProg, 0, 127)
TABLE_END

SEQ_TABLE(isNoun)
        ENTRY(&is, 0, 127)
        ENTRY(&nounPhrase, 0, 127)
TABLE_END

SEQ_TABLE(isAdjective)
        ENTRY(&is, 0, 127)
        ENTRY(&doAdjectivePhrase, 0, 127)
TABLE_END

RAND_TABLE(singVerbPhrase)
        ENTRY(&intransVerbSing, 0, 127)
        ENTRY(&transVerbSing, 0, 64)
        ENTRY(&singAuxVerbPhrase, 0, 32)
        ENTRY(&isNoun, 0, 127)
        ENTRY(&isAdjective, 0, 127)
TABLE_END

SEQ_TABLE(singNounVerbPhrase)
        ENTRY(&singNounPhrase, 0, 127)
        SPACE
        ENTRY(&singVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(plurNounVerbPhrase)
        ENTRY(&plurNounPhrase, 0, 127)
        SPACE
        ENTRY(&plurVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(twoNounAnd)
        ENTRY(&nounPhrase, 0, 127)
        SPACE
        ENTRY(&vocNounListAndConjunction, 0, 127)
        SPACE
        ENTRY(&nounPhrase, 0, 127)
        SPACE
        ENTRY(&plurVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(twoNounOrSing)
        ENTRY(&nounPhrase, 0, 127)
        SPACE
        ENTRY(&vocNounListOrConjunction, 0, 127)
        SPACE
        ENTRY(&singNounPhrase, 0, 127)
        SPACE
        ENTRY(&singVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(plurAuxVerbPhraseInf)
        ENTRY(&vocAuxVerbInf, 0, 127)
        SPACE
        ENTRY(&infVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(plurAuxVerbPhrasePProg)
        ENTRY(&vocPlurAuxVerbPProg, 0, 127)
        SPACE
        ENTRY(&auxVerbMainPProg, 0, 127)
TABLE_END

RAND_TABLE(plurAuxVerbPhrase)
        ENTRY(&plurAuxVerbPhraseInf, 0, 127)
        ENTRY(&plurAuxVerbPhrasePProg, 0, 127)
TABLE_END

SEQ_TABLE(areNoun)
        ENTRY(&are, 0, 127)
        ENTRY(&nounPhrase, 0, 127)
TABLE_END

SEQ_TABLE(areAdjective)
        ENTRY(&are, 0, 127)
        ENTRY(&doAdjectivePhrase, 0, 127)
TABLE_END

RAND_TABLE(plurVerbPhrase)
        ENTRY(&vocIntransVerbPlur, 0, 127)
        ENTRY(&transVerbPlur, 0, 127)
        ENTRY(&plurAuxVerbPhrase, 0, 127)
        ENTRY(&areAdjective, 0, 127)
        ENTRY(&areNoun, 0, 127)
TABLE_END

SEQ_TABLE(twoNounOrPlur)
        ENTRY(&nounPhrase, 0, 127)
        SPACE
        ENTRY(&vocNounListOrConjunction, 0, 127)
        SPACE
        ENTRY(&plurNounPhrase, 0, 127)
        SPACE
        ENTRY(&plurVerbPhrase, 0, 127)
TABLE_END

RAND_TABLE(twoNounVerbPhrase)
        ENTRY(&twoNounAnd, 0, 127)
        ENTRY(&twoNounOrSing, 0, 127)
        ENTRY(&twoNounOrPlur, 0, 127)
TABLE_END

SEQ_TABLE(threeNounVerbPhrase)
        ENTRY(&nounPhrase, 0, 127)
        COMMA
        SPACE
        ENTRY(&twoNounVerbPhrase, 0, 127)
TABLE_END

RAND_TABLE(iAmNounAdjectiveOrVerb)
        ENTRY(&nounPhrase, 0, 127)
        ENTRY(&doAdjectivePhrase, 0, 127)
        ENTRY(&auxVerbMainPProg, 0, 127)
TABLE_END

SEQ_TABLE(iAm)
        ENTRY(&am, 0, 127)
        ENTRY(&iAmNounAdjectiveOrVerb, 0, 127)
TABLE_END

SEQ_TABLE(myselfVerb)
        ENTRY(&adverbBefore, 0, 32)
        ENTRY(&vocTransVerbPlur, 0, 127)
        SPACE
        ENTRY(&myself, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

RAND_TABLE(iNormalVerbPhrase)
        ENTRY(&vocIntransVerbPlur, 0, 127)
        ENTRY(&transVerbPlur, 0, 127)
        ENTRY(&myselfVerb, 0, 127)
        ENTRY(&plurAuxVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(spaceINormalVerbPhrase)
        SPACE
        ENTRY(&iNormalVerbPhrase, 0, 127)
TABLE_END

RAND_TABLE(iVerb)
        ENTRY(&spaceINormalVerbPhrase, 0, 127)
        ENTRY(&iAm, 0, 64)
TABLE_END

SEQ_TABLE(iVerbPhrase)
        ENTRY(&I, 0, 127)
        ENTRY(&iVerb, 0, 127)
TABLE_END

SEQ_TABLE(youVerbPhrase)
        ENTRY(&you, 0, 127)
        ENTRY(&plurVerbPhrase, 0, 127)
TABLE_END

RAND_TABLE(nounVerbPhrase)
        ENTRY(&singNounVerbPhrase, 0, 127)
        ENTRY(&plurNounVerbPhrase, 0, 127)
        ENTRY(&twoNounVerbPhrase, 0, 16)
        ENTRY(&threeNounVerbPhrase, 0, 16)
        ENTRY(&iVerbPhrase, 0, 32)
        ENTRY(&youVerbPhrase, 0, 32)
TABLE_END



/* Imperatives */

SEQ_TABLE(impYourselfVerbPhrase)
        ENTRY(&adverbBefore, 0, 32)
        ENTRY(&vocTransVerbInf, 0, 127)
        SPACE
        ENTRY(&yourself, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

RAND_TABLE(impAuxVerbPhrase)
        ENTRY(&infVerbPhrase, 0, 127)
        ENTRY(&plurAuxVerbPhrasePProg, 0, 127)
TABLE_END

RAND_TABLE(impVerbPhrase)
        ENTRY(&impAuxVerbPhrase, 0, 127)
        ENTRY(&impYourselfVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(impAuxVerb)
        ENTRY(&vocImpAuxVerb, 0, 127)
        SPACE
TABLE_END

SEQ_TABLE(imperativeSentence)
        ENTRY(&address, 0, 16)
        ENTRY(&impAuxVerb, 0, 64)
        ENTRY(&impVerbPhrase, 0, 127)
        PUNCT
TABLE_END



/* Interrogatives */

RAND_TABLE(interNounOrAdjective)
        ENTRY(&nounPhrase, 0, 127)
        ENTRY(&doAdjectivePhrase, 0, 127)
TABLE_END

SEQ_TABLE(interSingVerbPhraseNormal)
        ENTRY(&vocInterSingAuxVerb, 0, 127)
        SPACE
        ENTRY(&singNounPhrase, 0, 127)
        SPACE
        ENTRY(&infVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(interSingIsNounOrAdjective)
        ENTRY(&is, 0, 127)
        ENTRY(&singNounPhrase, 0, 127)
        SPACE
        ENTRY(&interNounOrAdjective, 0, 127)
TABLE_END

RAND_TABLE(interSingVerbPhrase)
        ENTRY(&interSingVerbPhraseNormal, 0, 127)
        ENTRY(&interSingIsNounOrAdjective ,0 ,63)
TABLE_END

SEQ_TABLE(interPlurVerbPhraseNormal)
        ENTRY(&vocInterPlurAuxVerb, 0, 127)
        SPACE
        ENTRY(&plurNounPhrase, 0, 127)
        SPACE
        ENTRY(&infVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(interPlurAreNounOrAdjective)
        ENTRY(&are, 0, 127)
        ENTRY(&plurNounPhrase, 0, 127)
        SPACE
        ENTRY(&interNounOrAdjective, 0, 127)
TABLE_END

RAND_TABLE(interPlurVerbPhrase)
        ENTRY(&interPlurVerbPhraseNormal, 0, 127)
        ENTRY(&interPlurAreNounOrAdjective ,0 ,63)
TABLE_END

RAND_TABLE(interVerbPhrase)
        ENTRY(&interSingVerbPhrase, 0, 127)
        ENTRY(&interPlurVerbPhrase, 0, 127)
TABLE_END

SEQ_TABLE(intPronounSingSubject)
        ENTRY(&vocInterSingAuxVerb, 0, 127)
        SPACE
        ENTRY(&singNounPhrase, 0, 127)
TABLE_END

SEQ_TABLE(intPronounPlurSubject)
        ENTRY(&vocInterPlurAuxVerb, 0, 127)
        SPACE
        ENTRY(&plurNounPhrase, 0, 127)
TABLE_END

RAND_TABLE(intPronounSubject)
        ENTRY(&intPronounSingSubject, 0, 127)
        ENTRY(&intPronounPlurSubject, 0, 127)
TABLE_END

SEQ_TABLE(intPronounVerbPhrase)
        ENTRY(&intPronounSubject, 0, 127)
        SPACE
        ENTRY(&adverbBefore, 0, 32)
        ENTRY(&vocTransVerbInf, 0, 127)
        ENTRY(&adverbAfter, 0, 32)
TABLE_END

SEQ_TABLE(whoWhatPhrase)
        ENTRY(&whoWhat, 0, 127)
        ENTRY(&intPronounVerbPhrase, 0, 127)
        INTERPUNCT
TABLE_END

SEQ_TABLE(howManyPhrase)
        ENTRY(&howMany, 0, 127)
        ENTRY(&anyPlurNoun, 0, 127)
        SPACE
        ENTRY(&intPronounVerbPhrase, 0, 127)
        INTERPUNCT
TABLE_END

SEQ_TABLE(whichPhrase)
        ENTRY(&which, 0, 127)
        ENTRY(&anySingNoun, 0, 127)
        SPACE
        ENTRY(&intPronounVerbPhrase, 0, 127)
        INTERPUNCT
TABLE_END

SEQ_TABLE(whenWhereWhyHowPhrase)
        ENTRY(&whenWhereWhyHow, 0, 127)
        ENTRY(&intBooleanPhrase, 0, 127)
TABLE_END

RAND_TABLE(intPronounPhrase)
        ENTRY(&whoWhatPhrase, 0, 127)
        ENTRY(&howManyPhrase, 0, 127)
        ENTRY(&whichPhrase, 0, 127)
        ENTRY(&whenWhereWhyHowPhrase, 0, 127)
TABLE_END

SEQ_TABLE(intBooleanPhrase)
        ENTRY(&interVerbPhrase, 0, 127)
        INTERPUNCT
TABLE_END

RAND_TABLE(interrogativeSentence)
        ENTRY(&intPronounPhrase, 0, 127)
        ENTRY(&intBooleanPhrase, 0, 127)
TABLE_END



/* Root and high-level definitions */

SEQ_TABLE(intro)
        ENTRY(&vocIntroPhrase, 0, 127)
        SPACE
TABLE_END

SEQ_TABLE(conjoinedSentence)
        COMMA
        SPACE
        ENTRY(&vocSentenceConjunction, 0, 127)
        SPACE
        ENTRY(&nounVerbPhrase, 0, 127)
        ENTRY(&conjoinedSentence, 0, 8)
TABLE_END

RAND_TABLE(addressNoun)
        ENTRY(&vocSingPropNoun, 0, 127)
        ENTRY(&vocSingNounA, 0, 2)
        ENTRY(&vocSingNounAn, 0, 2)
        ENTRY(&vocSingNounNodeterm, 0, 2)
        ENTRY(&vocPlurNoun, 0, 2)
        ENTRY(&vocPlurNounNodeterm, 0, 2)
TABLE_END

SEQ_TABLE(address)
        ENTRY(&addressNoun, 0, 127)
        COMMA
        SPACE
TABLE_END

SEQ_TABLE(declaratorySentence)
        ENTRY(&intro, 0, 16)
        ENTRY(&address, 0, 16)
        ENTRY(&nounVerbPhrase, 0, 127)
        ENTRY(&conjoinedSentence, 0, 32)
        PUNCT
TABLE_END

RAND_TABLE(mainSentence)
        ENTRY(&declaratorySentence, 0, 127)
        ENTRY(&imperativeSentence, 0, 64)
        ENTRY(&interrogativeSentence, 0, 16)
TABLE_END

SEQ_TABLE(interjection)
        ENTRY(&vocInterjection, 0, 127)
        PUNCT
TABLE_END

SEQ_TABLE(interjectionOnly)
        ENTRY(&interjection, 1, 127)
        ENTRY(&interjection, 1, 16)
        ENTRY(&interjection, 1, 4)
        ENTRY(&interjection, 1, 8)
TABLE_END

SEQ_TABLE(normal)
        ENTRY(&interjection, 1, 16)
        ENTRY(&interjection, 1, 16)
        ENTRY(&interjection, 1, 4)
        ENTRY(&mainSentence, 1, 127)
        ENTRY(&interjection, 1, 32)
TABLE_END

RAND_TABLE(rootTable)
        ENTRY(&interjectionOnly, 0, 4)
        ENTRY(&normal, 0, 127)
TABLE_END

#endif
