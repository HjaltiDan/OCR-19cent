# OCR-19cent
OCR correction code for 19th century Icelandic manuscripts.

## Primary functionality ##
This program reviews text files generated through unsupervised OCR transcription of the manuscripts, and attempts to identify and correct OCR-generated errors.

As part of this process, we employ a slightly modified Levenshtein distance algorithm, wherein the program attempts to match an apparently-misspelled word with either a  known 19th-Century correction, or a known present-day one.

The program also generates count-based weights for known words. Therefore, if two 19th-Century words are equal candidates for an OCR correction, the program uses these weights as a tiebreaker to choose the most correct one.

## Secondary functionalty ##
Alongside OCR corrections, the program automatically generates lists of potential new (as in hereto-undiscovered) OCR errors. 
After these lists have been reviewed by a human, they can be added to a formal list of known errors and will be corrected automatically from then on.
